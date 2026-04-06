from pathlib import Path

from risk_dashboard.storage.sqlite_store import IngestRegistry


def test_register_and_latest(tmp_path):
    db = tmp_path / "t.db"
    reg = IngestRegistry(db)
    rid = reg.register(
        parquet_path=tmp_path / "a.parquet",
        manifest_path=None,
        market_label="m",
        macro_label="x",
        start_date="2024-01-01",
        end_date="2024-12-31",
        n_rows=100,
    )
    assert rid
    latest = reg.latest()
    assert latest is not None
    assert latest.parquet_path.endswith("a.parquet")
    reg.close()
