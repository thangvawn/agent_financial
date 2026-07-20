from __future__ import annotations

import argparse
from pathlib import Path

from risk_dashboard.engines.quant.research_report import build_model_research_report, save_model_research_report


def main() -> None:
    p = argparse.ArgumentParser(description="Sinh báo cáo nghiên cứu model từ artifact và benchmark hiện có.")
    p.add_argument("--models", type=Path, default=Path("data/models"), help="Thư mục chứa model reports và benchmark")
    p.add_argument("--out", type=Path, default=Path("data/models"), help="Thư mục lưu markdown/json report")
    args = p.parse_args()

    report = build_model_research_report(args.models)
    paths = save_model_research_report(report, args.out)

    print(f"Markdown: {paths.markdown_path}")
    print(f"JSON: {paths.json_path}")
    print(report.summary)


if __name__ == "__main__":
    main()
