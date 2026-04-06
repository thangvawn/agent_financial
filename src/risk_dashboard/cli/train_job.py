from __future__ import annotations

import argparse
import pickle
from datetime import date
from pathlib import Path

import pandas as pd

from risk_dashboard.quant.model_benchmark import resolve_benchmark_training_config
from risk_dashboard.quant.xgb_engine import train_risk_model


def main() -> None:
    p = argparse.ArgumentParser(description="Chạy Offline Training và lưu model ra dạng pkl.")
    p.add_argument("--panel", type=Path, required=True, help="Đường dẫn parquet training panel (vd: data/cache/panel_*.parquet)")
    p.add_argument("--out", type=Path, default=Path("data/models/latest_model.pkl"), help="Đường dẫn lưu file model .pkl")
    p.add_argument("--version", default="skhgb-v4-hybrid")
    p.add_argument("--benchmark-dir", type=Path, default=Path("data/models"))
    
    args = p.parse_args()
    
    print(f"Đọc dữ liệu từ {args.panel} ...")
    panel = pd.read_parquet(args.panel)
    panel["date"] = pd.to_datetime(panel["date"])
    
    benchmark_cfg = None
    if args.benchmark_dir and args.benchmark_dir.exists():
        try:
            benchmark_cfg = resolve_benchmark_training_config(args.benchmark_dir)
        except Exception:
            pass

    print(f"Tiến hành train model '{args.version}' trên {len(panel)} rows. Quá trình này có thể tốn vài chục giây...")
    trained, metrics = train_risk_model(
        panel,
        version=args.version,
        vn30_panel=None,
        feature_cols_by_horizon=benchmark_cfg.feature_cols_by_horizon if benchmark_cfg else None,
        estimator_params_by_horizon=benchmark_cfg.estimator_params_by_horizon if benchmark_cfg else None,
    )
    
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "wb") as f:
        pickle.dump({"model": trained, "metrics": metrics}, f)
        
    print(f"Thành công! Đã Serialize/Lưu model tại {args.out}")
    print("Metrics Evaluation:")
    for k, v in metrics.items():
        if v is not None:
             print(f"  - {k}: {v:.4f}")
        else:
             print(f"  - {k}: {v}")

if __name__ == "__main__":
    main()
