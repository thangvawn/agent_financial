import json

from risk_dashboard.engines.quant.research_report import (
    build_model_research_report,
    render_model_research_markdown,
    save_model_research_report,
)


def test_build_model_research_report_reads_latest_artifacts(tmp_path):
    model_payload = {
        "model_version": "skhgb-v9",
        "train_as_of": "2026-03-27",
        "created_at": "2026-03-30T00:00:00+00:00",
        "panel_path": "panel.parquet",
        "vn30_panel_path": "vn30.parquet",
        "artifact_path": "model.pkl",
        "n_rows_raw": 1000,
        "usable_rows": {"1w": 900},
        "metrics": {"auc_1w": 0.6, "auc_2w": 0.7, "auc_1m": 0.8, "brier_1w": 0.2, "brier_2w": 0.18, "brier_1m": 0.11},
    }
    model_benchmark_payload = {
        "best_models": [{"horizon": "2w", "model_name": "hist_gradient_boosting_tuned", "auc": 0.7, "brier": 0.18}],
    }
    feature_benchmark_payload = {
        "best_variants": [{"horizon": "2w", "variant_name": "legacy_plus_breadth", "n_features": 27, "auc": 0.69}],
    }
    (tmp_path / "risk_model_vnindex_hgb_hybrid_20260330T063442Z.json").write_text(json.dumps(model_payload), encoding="utf-8")
    (tmp_path / "model_benchmark_20260330T034245Z.json").write_text(json.dumps(model_benchmark_payload), encoding="utf-8")
    (tmp_path / "feature_benchmark_20260330T040521Z.json").write_text(json.dumps(feature_benchmark_payload), encoding="utf-8")

    report = build_model_research_report(tmp_path)

    assert report.summary["model_version"] == "skhgb-v9"
    assert report.summary["metrics"]["auc_2w"] == 0.7
    assert report.summary["best_benchmark_models"][0]["model_name"] == "hist_gradient_boosting_tuned"
    assert report.summary["best_feature_variants"][0]["variant_name"] == "legacy_plus_breadth"


def test_save_model_research_report_writes_markdown_and_json(tmp_path):
    model_payload = {
        "model_version": "skhgb-v9",
        "train_as_of": "2026-03-27",
        "created_at": "2026-03-30T00:00:00+00:00",
        "panel_path": "panel.parquet",
        "vn30_panel_path": "vn30.parquet",
        "artifact_path": "model.pkl",
        "n_rows_raw": 1000,
        "usable_rows": {"1w": 900},
        "metrics": {"auc_1w": 0.6, "auc_2w": 0.7, "auc_1m": 0.8, "brier_1w": 0.2, "brier_2w": 0.18, "brier_1m": 0.11},
    }
    (tmp_path / "risk_model_vnindex_hgb_hybrid_20260330T063442Z.json").write_text(json.dumps(model_payload), encoding="utf-8")

    report = build_model_research_report(tmp_path)
    paths = save_model_research_report(report, tmp_path)
    markdown = render_model_research_markdown(report)

    assert paths.markdown_path.exists()
    assert paths.json_path.exists()
    assert "# Model Research Report" in markdown
