from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from risk_dashboard.engines.quant.model_benchmark import run_model_benchmark, save_benchmark_results, summarize_best_models


def main() -> None:
    p = argparse.ArgumentParser(description="Benchmark nhiều model sklearn trên training panel hiện tại.")
    p.add_argument("--panel", type=Path, required=True, help="Đường dẫn parquet training panel")
    p.add_argument("--out", type=Path, default=Path("data/models"), help="Thư mục lưu benchmark csv/json")
    args = p.parse_args()

    panel = pd.read_parquet(args.panel)
    panel["date"] = pd.to_datetime(panel["date"])
    results = run_model_benchmark(panel)
    paths = save_benchmark_results(results, args.out)
    best = summarize_best_models(results)

    print(f"CSV: {paths.csv_path}")
    print(f"JSON: {paths.json_path}")
    print(best.to_string(index=False))


if __name__ == "__main__":
    main()
