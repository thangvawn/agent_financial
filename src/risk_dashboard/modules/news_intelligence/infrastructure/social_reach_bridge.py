"""Run pinned Agent-Reach in its own Python environment, without browser/session access.

Invoked as a script by agent_reach_adapter. The isolated library directory is explicit;
HOME is untouched. Import order is intentional: bind paths before importing runtime.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    request = json.loads(sys.stdin.read(8192))
    runtime = Path(request["runtime"]).resolve()
    runtime.mkdir(mode=0o700, parents=True, exist_ok=True)
    import agent_reach.utils.paths as paths

    paths.home_dir = lambda: runtime

    from agent_reach.channels import youtube
    from agent_reach.channels.reddit import RedditChannel
    from agent_reach.channels.youtube import YouTubeChannel
    from agent_reach.runtime.dispatch import run_action

    original_argv = youtube._ytdlp_argv
    youtube._ytdlp_argv = lambda *args: original_argv(
        "--ignore-config", "--no-playlist", "--cache-dir", str(runtime / "cache"), *args
    )
    platform, action = request["platform"], request["action"]
    allowed = {"youtube": {"search", "read", "subtitle"}, "reddit": {"search", "read"}}
    if platform not in allowed or action not in allowed[platform]:
        raise ValueError("Unsupported public action")
    channel = YouTubeChannel() if platform == "youtube" else RedditChannel()
    result = run_action(
        channel,
        action,
        request["params"],
        timeout=30,
        only_backend="yt-dlp" if platform == "youtube" else "public-web",
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
