"""Exercise the runner as a CLI, with disposable test files and a decoy user DB."""

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "scripts/qa/run_isolated_tests.py"


class IsolatedRunnerTests(unittest.TestCase):
    def run_sample(self, source, *options):
        with tempfile.TemporaryDirectory(prefix="northstar-runner-contract-") as folder:
            folder = Path(folder)
            sentinel = folder / "user.db"
            sentinel.write_bytes(b"user data must stay unchanged")
            sample = folder / "test_sample.py"
            sample.write_text(textwrap.dedent(source), encoding="utf-8")
            env = {
                **os.environ,
                "RISK_DASHBOARD_DB_PATH": str(sentinel),
                "RISK_DASHBOARD_APP_STATE_DB": str(sentinel),
                "RISK_DASHBOARD_SQLITE": str(sentinel),
            }
            result = subprocess.run(
                [sys.executable, str(RUNNER), *options, "--", str(sample), "-q"],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(sentinel.read_bytes(), b"user data must stay unchanged")
            reports = [
                line.removeprefix("Report: ")
                for line in result.stdout.splitlines()
                if line.startswith("Report: ")
            ]
            self.assertEqual(len(reports), 1, result.stdout + result.stderr)
            report = json.loads(Path(reports[0]).read_text())
            self.assertEqual(report["exit_code"], result.returncode)
            self.assertFalse(Path(report["temporary_directory"]).exists())
            self.assertTrue(Path(report["log"]).is_file())
            return result, report

    def test_import_time_db_and_pytest_files_are_isolated(self):
        result, report = self.run_sample("""
            import os
            import sqlite3
            from pathlib import Path
            from risk_dashboard.platform.database.config import get_db_path
            database = get_db_path()
            with sqlite3.connect(database) as connection:
                connection.execute("CREATE TABLE contract (value TEXT)")
                connection.execute("INSERT INTO contract VALUES ('temporary data')")
            def test_runtime(tmp_path):
                assert database.name == 'state.db'
                for key in ['RISK_DASHBOARD_DB_PATH', 'RISK_DASHBOARD_APP_STATE_DB',
                            'RISK_DASHBOARD_SQLITE']:
                    assert Path(os.environ[key]) == database
                assert os.environ['PYTHON_DOTENV_DISABLED'] == '1'
                assert Path(os.environ['VN_SCREENER_CACHE_DIR']).parent == database.parent
                assert os.environ['ENABLE_VN_SCREENER'] == '0'
                assert tmp_path.is_relative_to(database.parent)
                with sqlite3.connect(database) as connection:
                    row = connection.execute('SELECT value FROM contract').fetchone()
                    assert row == ('temporary data',)
        """)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(report["status"], "passed")

    def test_failed_assertion_remains_a_failure(self):
        result, report = self.run_sample(
            "def test_failure():\n    assert False, 'expected failure'"
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(report["status"], "failed")

    def test_empty_collection_is_not_success(self):
        result, report = self.run_sample("# No tests here\n")
        self.assertEqual(result.returncode, 5, result.stdout + result.stderr)
        self.assertEqual(report["status"], "failed")

    def test_timeout_cleans_up_and_reports_failure(self):
        result, report = self.run_sample(
            "import time\ndef test_wait():\n    time.sleep(20)",
            "--timeout",
            "2",
        )
        self.assertEqual(result.returncode, 124, result.stdout + result.stderr)
        self.assertEqual(report["status"], "timed_out")

    def test_rejects_custom_basetemp_without_deleting_data(self):
        with tempfile.TemporaryDirectory(prefix="northstar-keep-") as folder:
            sentinel = Path(folder) / "user-data.txt"
            sentinel.write_text("keep this")
            result = subprocess.run(
                [sys.executable, str(RUNNER), "--", "--basetemp", folder],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=10,
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertEqual(sentinel.read_text(), "keep this")


if __name__ == "__main__":
    unittest.main()
