from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from risk_dashboard.quant.model_benchmark import (
    run_feature_variant_benchmark,
    save_feature_benchmark_results,
    summarize_best_feature_variants,
)


def main() -> None:
    p = argparse.ArgumentParser(description="Benchmark nhiều hướng feature engineering trên training panel.")
    p.add_argument("--panel", type=Path, required=True, help="Đường dẫn parquet training panel")
    p.add_argument("--vn30", type=Path, help="Đường dẫn parquet VN30 daily để sinh breadth features")
    p.add_argument("--out", type=Path, default=Path("data/models"), help="Thư mục lưu benchmark csv/json")
    args = p.parse_args()

    panel = pd.read_parquet(args.panel)
    panel["date"] = pd.to_datetime(panel["date"])
    vn30 = None
    if args.vn30:
        vn30 = pd.read_parquet(args.vn30)

    results = run_feature_variant_benchmark(panel, vn30_panel=vn30)
    paths = save_feature_benchmark_results(results, args.out)
    best = summarize_best_feature_variants(results)

    print(f"CSV: {paths.csv_path}")
    print(f"JSON: {paths.json_path}")
    print(best.to_string(index=False))


if __name__ == "__main__":
    main()
