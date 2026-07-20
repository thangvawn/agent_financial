from __future__ import annotations

import json
from pathlib import Path
import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from risk_dashboard.modules.data_hub.application.services import DataHubService
from risk_dashboard.modules.data_hub.api.public import get_vn_snapshot
from risk_dashboard.modules.market_portfolio.application.services import MarketPortfolioService
from risk_dashboard.modules.market_portfolio.schemas import (
    CancelOrderRequest,
    PlaceOrderRequest,
    ResetPortfolioRequest,
    WatchlistAddRequest,
)

router = APIRouter(prefix="/market-portfolio", tags=["Market & Portfolio"])
_service = MarketPortfolioService()


# ── Market data proxies (keep data-hub paths as source of truth) ─────────────

_PROJECT_ROOT = Path(__file__).resolve().parents[4]
VN_MARKET_CACHE_DIR = _PROJECT_ROOT / "data" / "vn_market"


def _json_safe_provider_value(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(value, "item"):
        try:
            value = value.item()
        except (TypeError, ValueError):
            pass
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _get_ticker_profile(symbol: str) -> dict:
    symbol = symbol.upper().strip()
    cache_path = VN_MARKET_CACHE_DIR / "profiles" / f"{symbol}.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            pass
            
    try:
        from vnstock import Vnstock
        stock = Vnstock().stock(symbol)
        df = stock.company.overview()
        if isinstance(df, pd.DataFrame) and not df.empty:
            row = df.iloc[0]
            profile_data = {}
            for col in df.columns:
                profile_data[col] = _json_safe_provider_value(row[col])
            
            cache_path.write_text(json.dumps(profile_data, ensure_ascii=False, default=str), encoding="utf-8")
            return profile_data
    except Exception:
        pass
        
    return {
        "symbol": symbol,
        "name": f"CTCP {symbol}",
        "business_model": "Thông tin chi tiết doanh nghiệp chưa được tải xuống hoặc không khả dụng.",
        "ceo_name": "N/A",
        "listing_date": "N/A",
        "exchange": "HOSE",
        "outstanding_shares": None,
        "charter_capital": None,
        "website": "",
        "phone": "",
        "address": "N/A"
    }


def _get_ticker_shareholders(symbol: str) -> dict:
    symbol = symbol.upper().strip()
    cache_path = VN_MARKET_CACHE_DIR / "shareholders" / f"{symbol}.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            pass
            
    try:
        from vnstock import Vnstock
        stock = Vnstock().stock(symbol)
        df = stock.company.shareholders()
        if isinstance(df, pd.DataFrame) and not df.empty:
            list_items = []
            for _, row in df.iterrows():
                item = {}
                for col in df.columns:
                    item[col] = _json_safe_provider_value(row[col])
                list_items.append(item)
            
            payload = {"symbol": symbol, "shareholders": list_items}
            cache_path.write_text(json.dumps(payload, ensure_ascii=False, default=str), encoding="utf-8")
            return payload
    except Exception:
        pass
        
    return {
        "symbol": symbol,
        "shareholders": [],
        "data_status": "unavailable",
    }


def _get_ticker_officers(symbol: str) -> dict:
    symbol = symbol.upper().strip()
    cache_path = VN_MARKET_CACHE_DIR / "officers" / f"{symbol}.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            pass
            
    try:
        from vnstock import Vnstock
        stock = Vnstock().stock(symbol)
        df = stock.company.officers()
        if isinstance(df, pd.DataFrame) and not df.empty:
            list_items = []
            for _, row in df.iterrows():
                item = {}
                for col in df.columns:
                    item[col] = _json_safe_provider_value(row[col])
                list_items.append(item)
            
            payload = {"symbol": symbol, "officers": list_items}
            cache_path.write_text(json.dumps(payload, ensure_ascii=False, default=str), encoding="utf-8")
            return payload
    except Exception:
        pass
        
    return {
        "symbol": symbol,
        "officers": [],
        "data_status": "unavailable",
    }


@router.get("/market-data/terminal")
def market_data_terminal(view: str = "dashboard") -> dict:
    return DataHubService().get_global_terminal(view=view)


@router.get("/market-data/leaders")
def get_market_leaders() -> dict:
    from datetime import date
    items = [
        {
            "id": "leader_pham_nhat_vuong",
            "name": "Phạm Nhật Vượng",
            "company": "VIC",
            "company_name": "Tập đoàn Vingroup",
            "position": "Chủ tịch HĐQT Vingroup, TGĐ VinFast",
            "birth_year": 1968,
            "hometown": "Hà Tĩnh",
            "avatar_char": "V",
            "shares_value_vnd_b": 196400,
            "bio": "Nhà sáng lập Vingroup, tỷ phú đô la đầu tiên của Việt Nam được Forbes vinh danh.",
            "insider_transactions_count": 42
        },
        {
            "id": "leader_truong_gia_binh",
            "name": "Trương Gia Bình",
            "company": "FPT",
            "company_name": "Công ty Cổ phần FPT",
            "position": "Chủ tịch HĐQT FPT, Trưởng ban Nghiên cứu Phát triển Kinh tế tư nhân",
            "birth_year": 1956,
            "hometown": "Quảng Nam",
            "avatar_char": "B",
            "shares_value_vnd_b": 15450,
            "bio": "Linh hồn của tập đoàn FPT, người đặt nền móng cho ngành công nghệ thông tin và xuất khẩu phần mềm Việt Nam.",
            "insider_transactions_count": 18
        },
        {
            "id": "leader_tran_dinh_long",
            "name": "Trần Đình Long",
            "company": "HPG",
            "company_name": "Tập đoàn Hòa Phát",
            "position": "Chủ tịch HĐQT Hòa Phát",
            "birth_year": 1961,
            "hometown": "Hải Dương",
            "avatar_char": "L",
            "shares_value_vnd_b": 46200,
            "bio": "Biệt danh 'Vua Thép' Việt Nam, dẫn dắt Hòa Phát trở thành tập đoàn sản xuất thép lớn nhất Đông Nam Á.",
            "insider_transactions_count": 29
        },
        {
            "id": "leader_nguyen_thi_phuong_thao",
            "name": "Nguyễn Thị Phương Thảo",
            "company": "VJC",
            "company_name": "Vietjet Aviation",
            "position": "Chủ tịch HĐQT Vietjet Air, Phó CTHĐQT thường trực HDBank",
            "birth_year": 1970,
            "hometown": "Hà Nội",
            "avatar_char": "T",
            "shares_value_vnd_b": 26800,
            "bio": "Nữ tỷ phú tự thân đầu tiên của Việt Nam và Đông Nam Á, người phổ cập hóa dịch vụ hàng không giá rẻ.",
            "insider_transactions_count": 15
        },
        {
            "id": "leader_ho_hung_anh",
            "name": "Hồ Hùng Anh",
            "company": "TCB",
            "company_name": "Ngân hàng Techcombank",
            "position": "Chủ tịch HĐQT Techcombank",
            "birth_year": 1970,
            "hometown": "Thừa Thiên Huế",
            "avatar_char": "A",
            "shares_value_vnd_b": 21900,
            "bio": "Doanh nhân ngân hàng hàng đầu, đưa Techcombank trở thành ngân hàng tư nhân có lợi nhuận cao nhất Việt Nam.",
            "insider_transactions_count": 22
        },
        {
            "id": "leader_nguyen_dang_quang",
            "name": "Nguyễn Đăng Quang",
            "company": "MSN",
            "company_name": "Tập đoàn Masan",
            "position": "Chủ tịch HĐQT Masan Group",
            "birth_year": 1963,
            "hometown": "Quảng Trị",
            "avatar_char": "Q",
            "shares_value_vnd_b": 18200,
            "bio": "Người kiến tạo Masan trở thành tập đoàn tiêu dùng - bán lẻ hàng đầu phục vụ nhu cầu thiết yếu hàng ngày của người Việt.",
            "insider_transactions_count": 11
        }
    ]
    return {
        "as_of": date.today().isoformat(),
        "total": len(items),
        "items": items
    }


@router.get("/market-data/instruments/{symbol}/history")
def market_data_history(symbol: str, period: str = "6mo", interval: str = "1d") -> dict:
    return DataHubService().get_instrument_history(symbol=symbol, period=period, interval=interval)


@router.get("/market-data/instruments/{symbol}/profile")
def get_instrument_profile(symbol: str) -> dict:
    return _get_ticker_profile(symbol)


@router.get("/market-data/instruments/{symbol}/shareholders")
def get_instrument_shareholders(symbol: str) -> dict:
    return _get_ticker_shareholders(symbol)


@router.get("/market-data/instruments/{symbol}/officers")
def get_instrument_officers(symbol: str) -> dict:
    return _get_ticker_officers(symbol)


@router.get("/market-data/vn/snapshot")
def market_data_vn_snapshot(
    sort: str = Query("change_desc", pattern="^(change_desc|change_asc|volume_desc|value_desc|symbol_asc)$"),
    exchange: str | None = Query(None, pattern="^(HOSE|HSX|HNX|UPCOM)$"),
    search: str | None = Query(None, max_length=12),
    limit: int = Query(50, ge=1, le=500),
) -> dict:
    return get_vn_snapshot(sort=sort, exchange=exchange, search=search, limit=limit)


@router.get("/market-data/derivatives/snapshot")
def get_derivatives_snapshot() -> dict:
    from risk_dashboard.modules.data_hub.application.global_market_feed import GlobalMarketFeedProducer

    from risk_dashboard.modules.market_portfolio.application.derivatives_feed import fetch_derivatives_snapshot

    vn30_price = None
    
    try:
        feed = GlobalMarketFeedProducer().snapshot()
        indices = feed.get("groups", {}).get("indices", [])
        vn30_item = next((i for i in indices if i.get("symbol") == "VN30"), None)
        if vn30_item:
            vn30_price = vn30_item.get("price")
    except Exception:
        pass
    return fetch_derivatives_snapshot(vn30_price=vn30_price)


@router.get("/market-data/crypto/snapshot")
def get_crypto_snapshot() -> dict:
    from risk_dashboard.modules.data_hub.application.global_market_feed import GlobalMarketFeedProducer
    try:
        feed = GlobalMarketFeedProducer().snapshot()
        crypto = feed.get("groups", {}).get("crypto", [])
        priority = {"BTC-USD": 0, "ETH-USD": 1, "BNB-USD": 2, "SOL-USD": 3, "XRP-USD": 4, "ADA-USD": 5}
        crypto.sort(key=lambda x: priority.get(x.get("symbol", ""), 99))
        return {
            "as_of": feed.get("as_of"),
            "source": feed.get("source"),
            "freshness": feed.get("freshness"),
            "stale_reason": feed.get("stale_reason"),
            "total": len(crypto),
            "items": crypto
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market-data/commodities/snapshot")
def get_commodities_snapshot() -> dict:
    from risk_dashboard.modules.market_portfolio.application.commodity_feed import sync_commodity_snapshot
    try:
        return sync_commodity_snapshot()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Watchlist ────────────────────────────────────────────────────────────────


@router.get("/watchlist")
def get_watchlist(session_id: str = Query(..., min_length=8)) -> dict:
    return {"items": _service.list_watchlist(session_id)}


@router.post("/watchlist/items")
def add_watchlist_item(req: WatchlistAddRequest) -> dict:
    return _service.add_watchlist(req.session_id, req.symbol, req.label)


@router.delete("/watchlist/items/{symbol}")
def remove_watchlist_item(symbol: str, session_id: str = Query(..., min_length=8)) -> dict:
    return _service.remove_watchlist(session_id, symbol)


# ── Mock orders ──────────────────────────────────────────────────────────────


@router.get("/orders")
def list_orders(session_id: str = Query(..., min_length=8)) -> dict:
    return {"orders": _service.list_orders(session_id)}


@router.post("/orders")
def place_order(req: PlaceOrderRequest) -> dict:
    try:
        return _service.place_order(
            session_id=req.session_id,
            symbol=req.symbol,
            side=req.side,
            order_type=req.order_type,
            quantity=req.quantity,
            limit_price=req.limit_price,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/orders/{order_id}/cancel")
def cancel_order(order_id: str, req: CancelOrderRequest) -> dict:
    try:
        return _service.cancel_order(req.session_id, order_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ── Portfolio / PnL ──────────────────────────────────────────────────────────


@router.get("/portfolio")
def get_portfolio(session_id: str = Query(..., min_length=8)) -> dict:
    return _service.portfolio_summary(session_id)


@router.post("/portfolio/reset")
def reset_portfolio(req: ResetPortfolioRequest) -> dict:
    return _service.reset_portfolio(req.session_id)
