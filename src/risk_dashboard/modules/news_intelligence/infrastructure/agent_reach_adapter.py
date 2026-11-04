"""Bounded public-only Agent-Reach adapter. No install, login or browser commands."""

from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from risk_dashboard.modules.news_intelligence.domain.social_content import (
    ERRORS,
    canonical_url,
    clean,
    normalize_item,
)
from risk_dashboard.platform.database.config import project_root

PINNED_COMMIT = "7a38047acf26a729cbb27851e3cb81639da86b29"


class ReachFailure(RuntimeError):
    def __init__(self, code: str):
        self.code = code if code in ERRORS else "UPSTREAM_BROKEN"
        super().__init__(ERRORS[self.code])


def tool_python() -> Path:
    return Path(
        os.environ.get("SOCIAL_REACH_PYTHON") or project_root() / ".venv-social-tools/bin/python"
    )


class AgentReachAdapter:
    def available(self) -> bool:
        return tool_python().is_file()

    def call(self, platform: str, action: str, params: dict) -> dict:
        if not self.available():
            raise ReachFailure("NEED_SETUP")
        runtime = Path(
            os.environ.get("SOCIAL_REACH_RUNTIME") or project_root() / ".local-dev/social-reach"
        )
        request = {
            "platform": platform,
            "action": action,
            "params": params,
            "runtime": str(runtime),
        }
        bridge = Path(__file__).with_name("social_reach_bridge.py")
        env = {
            k: os.environ[k]
            for k in ("PATH", "LANG", "SSL_CERT_FILE", "SSL_CERT_DIR", "TMPDIR")
            if k in os.environ
        }
        env["PYTHONUTF8"] = "1"
        with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
            try:
                process = subprocess.Popen(
                    [str(tool_python()), str(bridge)],
                    stdin=subprocess.PIPE,
                    stdout=output,
                    stderr=errors,
                    env=env,
                    start_new_session=True,
                )
            except OSError as exc:
                raise ReachFailure("NEED_SETUP") from exc
            process.stdin.write(json.dumps(request).encode())
            process.stdin.close()
            deadline = time.monotonic() + 45
            failure = None
            while process.poll() is None:
                if output.tell() > 2_000_000 or errors.tell() > 500_000:
                    failure = "INVALID_PAYLOAD"
                    break
                if time.monotonic() >= deadline:
                    failure = "TIMEOUT"
                    break
                time.sleep(0.1)
            if failure:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
                raise ReachFailure(failure)
            output.seek(0)
            try:
                result = json.loads(output.read(2_000_001))
                if (
                    not isinstance(result, dict)
                    or result.get("schema_version") != 1
                    or not isinstance(result.get("ok"), bool)
                ):
                    raise ValueError
                if not result["ok"]:
                    raise ReachFailure((result.get("error") or {}).get("code", "UPSTREAM_BROKEN"))
                if process.returncode != 0 or not isinstance(result.get("items"), list):
                    raise ValueError
                return result
            except (ValueError, TypeError, KeyError) as exc:
                raise ReachFailure("INVALID_PAYLOAD") from exc

    def collect(self, job: dict) -> tuple[list[dict], int]:
        platform, action, target = job["platform"], job["action"], job["target"]
        query = target
        if action == "search":
            if platform == "reddit":
                since = (datetime.now(timezone.utc) - timedelta(days=7)).date()
                query = f"{target} after:{since.isoformat()}"
            else:
                query = f"{target} -psychic -astrology -tarot"
        params = {"query": query, "limit": 6} if action == "search" else {"target": target}
        response = self.call(platform, action, params)
        if action == "read" and not response["items"]:
            raise ReachFailure("NOT_FOUND")
        posts, partial = [], 0
        for index, item in enumerate(response["items"][:6]):
            if not isinstance(item, dict):
                partial += 1
                continue
            # Public-web readers may return an HTTP-200 access gate as a post.
            if platform == "reddit" and re.search(
                r"you(?:'|’)ve been blocked by network security|"
                r"log in to your reddit account or use your developer token|"
                r"whoa there, pardner|verify you are human",
                str(item.get("text") or "")[:2000],
                re.I,
            ):
                if action == "read":
                    raise ReachFailure("PLATFORM_BLOCKED")
                partial += 1
                continue
            try:
                canonical_url(str(item.get("url") or ""))
                detail = item
                backend = response.get("backend") or "public"
                if platform == "youtube" and action == "search":
                    try:
                        read = self.call(platform, "read", {"target": item["url"]})
                        if read["items"]:
                            detail = read["items"][0]
                    except ReachFailure as exc:
                        partial += 1
                        if exc.code in {"RATE_LIMITED", "PLATFORM_BLOCKED", "NEED_LOGIN"}:
                            if not posts:
                                raise
                            partial += len(response["items"][:6]) - index - 1
                            break
                post = normalize_item(
                    detail,
                    platform=platform,
                    market=job["market"],
                    backend=backend,
                    content_kind="description"
                    if platform == "youtube"
                    else "public_page"
                    if action == "read"
                    else "search_excerpt",
                )
                if platform == "youtube" and action == "read":
                    try:
                        captions = self.call(
                            platform, "subtitle", {"target": post["url"], "lang": "vi,en,en-orig"}
                        )
                        post["transcript"] = (
                            clean(captions["items"][0].get("text"), 24000)
                            if captions["items"]
                            else ""
                        )
                        post["transcript_status"] = (
                            "available" if post["transcript"] else "unavailable"
                        )
                    except ReachFailure as exc:
                        post["transcript_status"] = (
                            "unavailable" if exc.code == "NOT_FOUND" else "error"
                        )
                        partial += 1
                posts.append(post)
            except (ValueError, TypeError, KeyError):
                partial += 1
        if response["items"] and not posts:
            raise ReachFailure("INVALID_PAYLOAD")
        return posts, partial
