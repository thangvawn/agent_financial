from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from risk_dashboard.data.financials import (
    FinancialDataError,
    get_financial_dataset,
    import_financial_dataset,
)
from risk_dashboard.schemas.financials import FinancialDataset


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch hoặc import cache dữ liệu financial analysis cho một ticker."
    )
    parser.add_argument("--ticker", required=True, help="Mã cổ phiếu, ví dụ FPT")
    parser.add_argument("--refresh", action="store_true", help="Bỏ qua cache và gọi provider")
    parser.add_argument(
        "--from-file",
        type=Path,
        default=None,
        help="Import dataset JSON đã chuẩn hóa thay vì gọi provider",
    )
    args = parser.parse_args()

    try:
        if args.from_file is not None:
            payload = json.loads(args.from_file.read_text(encoding="utf-8"))
            dataset = FinancialDataset.model_validate(payload)
            path = import_financial_dataset(dataset)
            print(f"Imported financial dataset -> {path}")
            return

        dataset = get_financial_dataset(args.ticker, refresh=args.refresh)
        print(dataset.model_dump_json(indent=2))
    except FinancialDataError as exc:
        print(exc.message, file=sys.stderr)
        for note in exc.notes:
            if note:
                print(f"- {note}", file=sys.stderr)
        if exc.hint:
            print(f"Hint: {exc.hint}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
