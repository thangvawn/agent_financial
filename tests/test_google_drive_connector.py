from pathlib import Path

from risk_dashboard.data.google_drive import (
    normalize_extensions,
    safe_filename,
    safe_relative_drive_path,
    unique_path,
)


def test_google_drive_path_helpers(tmp_path):
    assert normalize_extensions(["csv,.xlsx", "PDF"]) == {".csv", ".xlsx", ".pdf"}
    assert safe_filename('bad/name:*?.csv') == "bad_name_.csv"
    assert safe_relative_drive_path("Quant Science/raw/file.csv", folder_name="Quant Science") == Path("raw")

    target = tmp_path / "data.csv"
    target.write_text("x", encoding="utf-8")
    assert unique_path(target) == tmp_path / "data_1.csv"
