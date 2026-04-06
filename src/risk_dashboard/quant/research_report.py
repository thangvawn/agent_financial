from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ResearchReportPaths:
    markdown_path: Path
    json_path: Path


@dataclass(frozen=True)
class ModelResearchReport:
    created_at: str
    model_dir: str
    latest_model_report: dict[str, Any]
    latest_model_benchmark: dict[str, Any] | None
    latest_feature_benchmark: dict[str, Any] | None
    summary: dict[str, Any]


def _latest_json(path: Path, pattern: str) -> tuple[Path, dict[str, Any]] | None:
    candidates = sorted(path.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    for candidate in candidates:
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            return candidate, payload
    return None


def _round_metric(value: Any) -> float | None:
    if not isinstance(value, (float, int)):
        return None
    return round(float(value), 4)


def build_model_research_report(model_dir: str | Path = "data/models") -> ModelResearchReport:
    root = Path(model_dir)
    latest_model_loaded = _latest_json(root, "risk_model_vnindex*.json")
    if latest_model_loaded is None:
        raise FileNotFoundError(f"No model report found in {root}")
    latest_model_path, latest_model = latest_model_loaded

    latest_model_benchmark_loaded = _latest_json(root, "model_benchmark_*.json")
    latest_feature_benchmark_loaded = _latest_json(root, "feature_benchmark_*.json")
    latest_model_benchmark = latest_model_benchmark_loaded[1] if latest_model_benchmark_loaded else None
    latest_feature_benchmark = latest_feature_benchmark_loaded[1] if latest_feature_benchmark_loaded else None

    metrics = latest_model.get("metrics", {})
    summary = {
        "model_file": latest_model_path.name,
        "model_version": latest_model.get("model_version"),
        "train_as_of": latest_model.get("train_as_of"),
        "created_at": latest_model.get("created_at"),
        "panel_path": latest_model.get("panel_path"),
        "vn30_panel_path": latest_model.get("vn30_panel_path"),
        "artifact_path": latest_model.get("artifact_path"),
        "n_rows_raw": latest_model.get("n_rows_raw"),
        "usable_rows": latest_model.get("usable_rows"),
        "metrics": {
            "auc_1w": _round_metric(metrics.get("auc_1w")),
            "auc_2w": _round_metric(metrics.get("auc_2w")),
            "auc_1m": _round_metric(metrics.get("auc_1m")),
            "brier_1w": _round_metric(metrics.get("brier_1w")),
            "brier_2w": _round_metric(metrics.get("brier_2w")),
            "brier_1m": _round_metric(metrics.get("brier_1m")),
            "precision_high_risk_1w": _round_metric(metrics.get("precision_high_risk_1w")),
            "precision_high_risk_2w": _round_metric(metrics.get("precision_high_risk_2w")),
            "precision_high_risk_1m": _round_metric(metrics.get("precision_high_risk_1m")),
        },
        "best_benchmark_models": latest_model_benchmark.get("best_models", []) if latest_model_benchmark else [],
        "best_feature_variants": latest_feature_benchmark.get("best_variants", []) if latest_feature_benchmark else [],
    }
    return ModelResearchReport(
        created_at=datetime.now(timezone.utc).isoformat(),
        model_dir=str(root),
        latest_model_report=latest_model,
        latest_model_benchmark=latest_model_benchmark,
        latest_feature_benchmark=latest_feature_benchmark,
        summary=summary,
    )


def render_model_research_markdown(report: ModelResearchReport) -> str:
    summary = report.summary
    metrics = summary["metrics"]
    lines = [
        "# Model Research Report",
        "",
        f"- Created at: `{report.created_at}`",
        f"- Model version: `{summary['model_version']}`",
        f"- Model file: `{summary['model_file']}`",
        f"- Train as of: `{summary['train_as_of']}`",
        f"- Raw rows: `{summary['n_rows_raw']}`",
        "",
        "## Latest Metrics",
        "",
        f"- AUC 1w: `{metrics['auc_1w']}`",
        f"- AUC 2w: `{metrics['auc_2w']}`",
        f"- AUC 1m: `{metrics['auc_1m']}`",
        f"- Brier 1w: `{metrics['brier_1w']}`",
        f"- Brier 2w: `{metrics['brier_2w']}`",
        f"- Brier 1m: `{metrics['brier_1m']}`",
        "",
        "## Best Benchmark Models",
        "",
    ]
    best_models = summary["best_benchmark_models"] or []
    if best_models:
        for row in best_models:
            lines.append(
                f"- {row.get('horizon')}: `{row.get('model_name')}` | auc `{row.get('auc')}` | brier `{row.get('brier')}`"
            )
    else:
        lines.append("- None")

    lines.extend(["", "## Best Feature Variants", ""])
    best_variants = summary["best_feature_variants"] or []
    if best_variants:
        for row in best_variants:
            lines.append(
                f"- {row.get('horizon')}: `{row.get('variant_name')}` | n_features `{row.get('n_features')}` | auc `{row.get('auc')}`"
            )
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"


def save_model_research_report(report: ModelResearchReport, output_dir: str | Path = "data/models") -> ResearchReportPaths:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    markdown_path = out_dir / f"model_research_report_{ts}.md"
    json_path = out_dir / f"model_research_report_{ts}.json"
    markdown_path.write_text(render_model_research_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8")
    return ResearchReportPaths(markdown_path=markdown_path, json_path=json_path)
