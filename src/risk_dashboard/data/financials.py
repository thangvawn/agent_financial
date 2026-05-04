from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from risk_dashboard.schemas.financials import FinancialDataset, FinancialPeriodData


class FinancialDataError(RuntimeError):
    def __init__(self, message: str, *, hint: str | None = None, notes: list[str] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint
        self.notes = notes or []


@dataclass
class ProviderAttempt:
    provider: str
    success: bool
    detail: str


_STATEMENT_TYPE_MAP = {
    "IncomeStatement": "income",
    "BalanceSheet": "balance",
    "CashFlow": "cashflow",
}

_METRIC_PATTERNS: list[tuple[str, tuple[str, ...]]] = [
    ("revenue", ("doanh thu thuần", "doanh thu", "net sales", "revenue")),
    ("gross_profit", ("lợi nhuận gộp", "lãi gộp", "gross profit")),
    ("operating_profit", ("lợi nhuận thuần từ hoạt động kinh doanh", "lãi/lỗ từ hoạt động kinh doanh", "lãi/(lỗ) từ hoạt động kinh doanh", "operating profit")),
    ("ebit", ("ebit", "earnings before interest and taxes")),
    ("ebitda", ("ebitda",)),
    ("net_income", ("lợi nhuận sau thuế của cổ đông công ty mẹ", "lợi nhuận của cổ đông của công ty mẹ", "lãi/(lỗ) thuần sau thuế", "lợi nhuận sau thuế", "lợi nhuận thuần", "net profit", "profit after tax", "attributable to parent company")),
    ("total_assets", ("tổng cộng tài sản", "total assets")),
    ("total_liabilities", ("nợ phải trả", "total liabilities")),
    ("equity", ("vốn chủ sở hữu", "equity")),
    ("cash", ("tiền và tương đương tiền", "cash and cash equivalents", "cash")),
    ("short_term_investments", ("đầu tư ngắn hạn", "short-term investments")),
    ("short_term_debt", ("vay và nợ thuê tài chính ngắn hạn", "short-term borrowings", "short-term debt")),
    ("long_term_debt", ("vay và nợ thuê tài chính dài hạn", "long-term borrowings", "long-term debt")),
    ("debt", ("vay và nợ thuê tài chính", "total debt", "borrowings")),
    ("current_assets", ("tài sản ngắn hạn", "current assets")),
    ("current_liabilities", ("nợ ngắn hạn", "current liabilities")),
    ("non_current_liabilities", ("nợ dài hạn", "non-current liabilities", "long-term liabilities")),
    ("accounts_payable", ("phải trả người bán", "trade accounts payable", "accounts payable")),
    ("inventory", ("hàng tồn kho", "inventory")),
    ("receivables", ("các khoản phải thu ngắn hạn", "các khoản phải thu", "accounts receivable", "receivables")),
    ("fixed_assets", ("tài sản cố định", "fixed assets")),
    ("investment_properties", ("bất động sản đầu tư", "investment properties")),
    ("long_term_investments", ("đầu tư dài hạn", "long-term investments")),
    ("retained_earnings", ("lợi nhuận sau thuế chưa phân phối", "retained earnings")),
    ("minority_interest", ("lợi ích cổ đông không kiểm soát", "minority interest")),
    ("operating_cash_flow", ("lưu chuyển tiền tệ ròng từ các hoạt động sxkd", "lưu chuyển tiền tệ ròng từ các hoạt động sản xuất kinh doanh", "lưu chuyển tiền thuần từ hoạt động kinh doanh", "net cash inflows/(outflows) from operating activities", "operating cash flow")),
    ("investing_cash_flow", ("lưu chuyển từ hoạt động đầu tư", "lưu chuyển tiền thuần từ hoạt động đầu tư", "investing cash flow")),
    ("financing_cash_flow", ("lưu chuyển tiền từ hoạt động tài chính", "lưu chuyển tiền thuần từ hoạt động tài chính", "financing cash flow")),
    ("capex", ("mua sắm tscđ", "tiền chi để mua sắm, xây dựng tscđ", "tiền chi để mua sắm, xây dựng tscd", "purchases of fixed assets", "capital expenditure", "purchase of fixed assets")),
]

_IGNORED_LABEL_PATTERNS = (
    "tăng trưởng",
    "%",
    "biên",
    "margin",
    "roe",
    "roa",
    "eps",
)


def _financial_root_dir() -> Path:
    custom = os.getenv("RISK_DASHBOARD_FINANCIALS_DIR")
    if custom:
        return Path(custom)
    return Path("data/financials")


def _financial_cache_dir() -> Path:
    cache_dir = _financial_root_dir() / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _cache_path_for_ticker(ticker: str) -> Path:
    return _financial_cache_dir() / f"{ticker.upper().strip()}.json"


def load_cached_financial_dataset(ticker: str) -> FinancialDataset | None:
    path = _cache_path_for_ticker(ticker)
    if not path.exists():
        return None
    return FinancialDataset.model_validate_json(path.read_text(encoding="utf-8"))


def save_financial_dataset(dataset: FinancialDataset) -> Path:
    path = _cache_path_for_ticker(dataset.ticker)
    path.write_text(dataset.model_dump_json(indent=2), encoding="utf-8")
    return path


def import_financial_dataset(dataset: FinancialDataset) -> Path:
    return save_financial_dataset(dataset)


def _normalize_label(value: Any) -> str:
    raw = str(value or "").strip().lower()
    raw = re.sub(r"\s+", " ", raw)
    return raw


def _normalize_period_info(value: Any) -> tuple[str, int | None, int | None]:
    raw = str(value or "").strip()

    match = re.search(r"Q([1-4])[-/\s]?(\d{4})", raw, re.IGNORECASE)
    if match:
        quarter = int(match.group(1))
        year = int(match.group(2))
        return f"{year}-Q{quarter}", year, quarter

    match = re.search(r"(\d{4})[-/\s]?Q([1-4])", raw, re.IGNORECASE)
    if match:
        year = int(match.group(1))
        quarter = int(match.group(2))
        return f"{year}-Q{quarter}", year, quarter

    year_match = re.search(r"(20\d{2})", raw)
    if year_match:
        year = int(year_match.group(1))
        quarter_match = re.search(r"quý\s*([1-4])", raw, re.IGNORECASE)
        quarter = int(quarter_match.group(1)) if quarter_match else None
        period = f"{year}-Q{quarter}" if quarter else str(year)
        return period, year, quarter

    return raw or "unknown", None, None


def _to_float(value: Any) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text:
        return None

    text = text.replace(",", "")
    text = text.replace("\u2212", "-")
    try:
        return float(text)
    except ValueError:
        return None


def _canonical_metric(metric_name: str) -> str | None:
    label = _normalize_label(metric_name)
    if any(pattern in label for pattern in _IGNORED_LABEL_PATTERNS):
        return None
    for canonical_name, patterns in _METRIC_PATTERNS:
        if any(pattern in label for pattern in patterns):
            return canonical_name
    return None


def _assign_metric(bucket: dict[str, Any], metric_name: str, value: float) -> None:
    if metric_name == "debt":
        bucket[metric_name] = float(bucket.get(metric_name, 0.0) + value)
        return
    if metric_name in {"short_term_debt", "long_term_debt"}:
        if bucket.get(metric_name) is None:
            bucket[metric_name] = value
        bucket["debt"] = float(bucket.get("debt", 0.0) + value)
        return
    if bucket.get(metric_name) is None:
        bucket[metric_name] = value


def _is_row_oriented_statement(statement_df: pd.DataFrame) -> bool:
    normalized_columns = {_normalize_label(column) for column in statement_df.columns}
    return bool(
        {"năm", "kỳ"} <= normalized_columns
        or {"year", "quarter"} <= normalized_columns
    )


def _merge_row_statement_into_periods(
    period_map: dict[str, dict[str, Any]],
    statement_df: pd.DataFrame,
) -> None:
    if statement_df.empty:
        return

    for _, row in statement_df.iterrows():
        row_map = {str(column): row.get(column) for column in statement_df.columns}

        year = _to_float(row_map.get("Năm") or row_map.get("year"))
        quarter = _to_float(row_map.get("Kỳ") or row_map.get("quarter"))
        year_int = int(year) if year is not None else None
        quarter_int = int(quarter) if quarter is not None else None

        if year_int is None:
            continue

        period = f"{year_int}-Q{quarter_int}" if quarter_int else str(year_int)
        bucket = period_map.setdefault(
            period,
            {"period": period, "year": year_int, "quarter": quarter_int},
        )

        for column_name, raw_value in row_map.items():
            metric_name = _canonical_metric(column_name)
            if metric_name is None:
                continue
            value = _to_float(raw_value)
            if value is None:
                continue
            _assign_metric(bucket, metric_name, value)


def _merge_statement_into_periods(period_map: dict[str, dict[str, Any]], statement_df: pd.DataFrame) -> None:
    if statement_df.empty or len(statement_df.columns) < 2:
        return

    if _is_row_oriented_statement(statement_df):
        _merge_row_statement_into_periods(period_map, statement_df)
        return

    label_column = statement_df.columns[0]
    period_columns = [
        column for column in statement_df.columns[1:]
        if not str(column).startswith("Unnamed")
        and _normalize_label(column) not in {"item_en", "item_id"}
    ]

    for _, row in statement_df.iterrows():
        metric_name = _canonical_metric(row.get(label_column))
        if metric_name is None:
            continue

        for period_column in period_columns:
            period, year, quarter = _normalize_period_info(period_column)
            bucket = period_map.setdefault(period, {"period": period, "year": year, "quarter": quarter})
            value = _to_float(row.get(period_column))
            if value is not None:
                _assign_metric(bucket, metric_name, value)


def _build_dataset_from_statement_frames(
    ticker: str,
    *,
    income_df: pd.DataFrame,
    balance_df: pd.DataFrame,
    cashflow_df: pd.DataFrame,
    source: str,
    provider_notes: list[str] | None = None,
) -> FinancialDataset:
    period_map: dict[str, dict[str, Any]] = {}
    _merge_statement_into_periods(period_map, income_df)
    _merge_statement_into_periods(period_map, balance_df)
    _merge_statement_into_periods(period_map, cashflow_df)

    periods = [FinancialPeriodData.model_validate(period_data) for period_data in period_map.values()]

    return FinancialDataset(
        ticker=ticker,
        source=source,
        fetched_at=datetime.now(timezone.utc),
        provider_notes=provider_notes or [],
        periods=periods,
    )


def _prepare_vnstock_runtime() -> None:
    # In sandboxed runs, HOME may not be writable. Point vnstock caches to the workspace.
    runtime_home = _financial_root_dir() / ".runtime-home"
    runtime_home.mkdir(parents=True, exist_ok=True)
    current_home = Path(os.path.expanduser("~"))
    if not os.access(current_home, os.W_OK):
        os.environ["HOME"] = str(runtime_home)
    os.environ["VNSTOCK_DATA_DIR"] = str(runtime_home / ".vnstock")
    os.environ.setdefault("MPLCONFIGDIR", str(runtime_home / ".matplotlib"))


def _attempt_vnstock_fetch(ticker: str) -> FinancialDataset:
    attempts: list[str] = []

    _prepare_vnstock_runtime()

    try:
        from vnstock.api.financial import Finance
    except Exception as exc:  # pragma: no cover - import dependent
        raise FinancialDataError(
            "Không import được vnstock.",
            hint="Kiểm tra dependency `.[vnstock]` trong virtualenv Python 3.10+.",
            notes=[str(exc)],
        ) from exc

    for source in ("VCI", "KBS"):
        frames: dict[str, pd.DataFrame] = {}
        try:
            finance = Finance(source=source, symbol=ticker, period="quarter", get_all=True, show_log=False)
            frames["income"] = finance.income_statement(period="quarter", lang="vi", dropna=True)
            frames["balance"] = finance.balance_sheet(period="quarter", lang="vi", dropna=True)
            frames["cashflow"] = finance.cash_flow(period="quarter", lang="vi", dropna=True)
            if any(frame.empty for frame in frames.values()):
                raise ValueError("Provider returned empty statement.")
            return _build_dataset_from_statement_frames(
                ticker,
                income_df=frames["income"],
                balance_df=frames["balance"],
                cashflow_df=frames["cashflow"],
                source=f"vnstock-{source.lower()}",
                provider_notes=attempts,
            )
        except Exception as exc:
            attempts.append(f"{source}: {exc}")

    raise FinancialDataError(
        f"Không lấy được đầy đủ BCTC từ vnstock cho mã {ticker}.",
        hint="Kiểm tra mạng hoặc proxy cho provider live. Nếu vẫn lỗi, import JSON chuẩn hóa vào cache để dùng offline.",
        notes=attempts,
    )


def get_financial_dataset(ticker: str, *, refresh: bool = False) -> FinancialDataset:
    ticker = ticker.upper().strip()
    if not refresh:
        cached = load_cached_financial_dataset(ticker)
        if cached is not None:
            return cached

    provider_errors: list[str] = []

    try:
        dataset = _attempt_vnstock_fetch(ticker)
        save_financial_dataset(dataset)
        return dataset
    except FinancialDataError as exc:
        provider_errors.extend([exc.message, *(exc.notes or []), exc.hint or ""])

    cached = load_cached_financial_dataset(ticker)
    if cached is not None:
        notes = list(cached.provider_notes)
        notes.extend([note for note in provider_errors if note])
        return cached.model_copy(update={"provider_notes": notes})

    raise FinancialDataError(
        f"Chưa lấy được dữ liệu BCTC cho {ticker}.",
        hint="Thử import dữ liệu thủ công vào cache hoặc kiểm tra kết nối tới provider live.",
        notes=[note for note in provider_errors if note],
    )
