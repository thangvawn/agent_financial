#!/usr/bin/env python3
"""Run pytest with temporary runtime paths set before application imports.

Usage: .venv/bin/python scripts/qa/run_isolated_tests.py -- tests/test_personal_library.py
This isolates configured paths; it is not an OS filesystem or network sandbox.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]


def positive_seconds(value: str) -> int:
    seconds = int(value)
    if seconds <= 0:
        raise argparse.ArgumentTypeError("timeout must be positive")
    return seconds


def stop_process(process: subprocess.Popen) -> None:
    # pytest can spawn child processes; stop the group before deleting its DB.
    def send(sig):
        try:
            if os.name == "posix":
                os.killpg(process.pid, sig)
            elif sig == signal.SIGTERM:
                process.terminate()
            else:
                process.kill()
        except ProcessLookupError:
            pass

    send(signal.SIGTERM)
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        pass
    # A descendant may outlive pytest even if the parent has already exited.
    if os.name == "posix":
        send(signal.SIGKILL)
    else:
        process.kill()
    process.wait()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=positive_seconds, default=600)
    parser.add_argument("pytest_args", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    pytest_args = args.pytest_args
    if pytest_args[:1] == ["--"]:
        pytest_args = pytest_args[1:]
    if any(value == "--basetemp" or value.startswith("--basetemp=") for value in pytest_args):
        parser.error("--basetemp is managed by this runner; choose tests after --")

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    output = ROOT / "output/qa/isolated-tests" / run_id
    output.mkdir(parents=True)
    log_path = output / "pytest.log"
    started = time.monotonic()
    status, exit_code = "failed", 1
    with tempfile.TemporaryDirectory(prefix="northstar-tests-") as temporary:
        scratch = Path(temporary).resolve()
        env = {
            **os.environ,
            "PYTHON_DOTENV_DISABLED": "1",
            "RISK_DASHBOARD_DB_PATH": str(scratch / "state.db"),
            "RISK_DASHBOARD_APP_STATE_DB": str(scratch / "state.db"),
            "RISK_DASHBOARD_SQLITE": str(scratch / "state.db"),
            "RISK_DASHBOARD_FINANCIAL_UPLOADS_DIR": str(scratch / "financial-uploads"),
            "VN_SCREENER_CACHE_DIR": str(scratch / "vn-screener"),
            "ENABLE_VN_SCREENER": "0",
            "MPLCONFIGDIR": str(scratch / "matplotlib"),
            "PYTEST_ADDOPTS": "",
            "ENABLE_TELEGRAM_NEWS_SCHEDULER": "0",
            "ENABLE_VN_MARKET_SCHEDULER": "0",
            "ENABLE_SOCIAL_WORKER": "0",
            "AI_ASSISTANT_AGENT_ENABLED": "0",
            "API_SECRET_KEY": "",
        }
        env["PYTHONPATH"] = os.pathsep.join(
            filter(None, [str(ROOT / "src"), env.get("PYTHONPATH")])
        )
        command = [
            sys.executable,
            "-m",
            "pytest",
            *pytest_args,
            "--basetemp",
            str(scratch / "pytest"),
            "-o",
            f"cache_dir={scratch / 'pytest-cache'}",
        ]
        print(f"Test log: {log_path}", flush=True)
        with log_path.open("w", encoding="utf-8") as log:
            try:
                process = subprocess.Popen(
                    command,
                    cwd=ROOT,
                    env=env,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
                try:
                    exit_code = process.wait(timeout=args.timeout)
                    if exit_code < 0:
                        exit_code = 128 - exit_code
                    status = "passed" if exit_code == 0 else "failed"
                except subprocess.TimeoutExpired:
                    stop_process(process)
                    status, exit_code = "timed_out", 124
                except KeyboardInterrupt:
                    stop_process(process)
                    status, exit_code = "interrupted", 130
            except OSError as error:
                log.write(f"Cannot start pytest: {error}\n")

    report = {
        "status": status,
        "exit_code": exit_code,
        "command": command,
        "duration_seconds": round(time.monotonic() - started, 3),
        "temporary_directory": str(scratch),
        "temporary_directory_removed": not scratch.exists(),
        "log": str(log_path),
    }
    report_path = output / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(log_path.read_text(encoding="utf-8", errors="replace")[-12000:], end="")
    print(f"\nResult: {status} (exit {exit_code})")
    print(f"Report: {report_path}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
