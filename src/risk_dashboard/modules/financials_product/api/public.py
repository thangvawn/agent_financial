from __future__ import annotations

import sys

from fastapi import APIRouter, HTTPException

from risk_dashboard.data.financials import FinancialDataError, get_financial_dataset, import_financial_dataset
from risk_dashboard.quant.balance_sheet_strength import BalanceSheetDataError, build_balance_sheet_strength
from risk_dashboard.quant.financial_analysis import analyze_financial_dataset
from risk_dashboard.quant.financial_quality_charts import build_financial_quality_charts
from risk_dashboard.schemas.financials import FinancialImportRequest

router = APIRouter(tags=["Financials"])


@router.get("/financials/status", tags=["Financials"])
def financials_status() -> dict[str, object]:
    return {
        "provider": "vnstock-live",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        "notes": [
            "Provider BCTC mặc định hiện dùng vnstock 3.x với luồng live fetch.",
            "Môi trường đã nâng lên Python 3.10+ để tương thích provider mới.",
            "Có thể import cache JSON chuẩn hóa nếu provider live thất bại.",
        ],
    }


@router.get("/financials/{ticker}/analysis", tags=["Financials"])
def financial_analysis(ticker: str, refresh: bool = False):
    try:
        dataset = get_financial_dataset(ticker, refresh=refresh)
    except FinancialDataError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "message": exc.message,
                "error": exc.notes[0] if exc.notes else None,
                "hint": exc.hint,
                "notes": exc.notes,
            },
        ) from exc
    return analyze_financial_dataset(dataset).model_dump(mode="json")


@router.get("/financials/{ticker}/quality-charts", tags=["Financials"])
def financial_quality_charts(ticker: str, refresh: bool = False):
    try:
        dataset = get_financial_dataset(ticker, refresh=refresh)
    except FinancialDataError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "message": exc.message,
                "error": exc.notes[0] if exc.notes else None,
                "hint": exc.hint,
                "notes": exc.notes,
            },
        ) from exc
    return build_financial_quality_charts(dataset).model_dump(mode="json")


@router.get("/financials/{ticker}/balance-sheet-strength", tags=["Financials"])
def financial_balance_sheet_strength(ticker: str, period: str | None = None, refresh: bool = False):
    try:
        dataset = get_financial_dataset(ticker, refresh=refresh)
        return build_balance_sheet_strength(dataset, period=period).model_dump(mode="json")
    except FinancialDataError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "message": exc.message,
                "error": exc.notes[0] if exc.notes else None,
                "hint": exc.hint,
                "notes": exc.notes,
            },
        ) from exc
    except BalanceSheetDataError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/financials/{ticker}/peers", tags=["Financials"])
def financial_peer_compare(ticker: str, peers: str | None = None):
    from risk_dashboard.quant.peer_compare import compare_peers

    peer_list = [p.strip().upper() for p in peers.split(",") if p.strip()] if peers else None
    result = compare_peers(ticker, peer_tickers=peer_list)
    return result.to_dict()


@router.get("/financials/cached-tickers", tags=["Financials"])
def list_cached_financial_tickers():
    from risk_dashboard.quant.peer_compare import list_cached_tickers

    tickers = list_cached_tickers()
    return {"tickers": tickers, "count": len(tickers)}


@router.post("/financials/import", tags=["Financials"])
def financial_import(req: FinancialImportRequest):
    path = import_financial_dataset(req.dataset)
    analysis = analyze_financial_dataset(req.dataset)
    return {
        "ok": True,
        "path": str(path),
        "ticker": req.dataset.ticker,
        "periods": len(req.dataset.periods),
        "analysis": analysis.model_dump(mode="json"),
    }
