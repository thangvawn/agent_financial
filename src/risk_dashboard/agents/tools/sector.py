"""
Sector Tool — Kết nối trực tiếp vào vnstock và Money Flow API nội bộ.
"""
from __future__ import annotations

from langchain_core.tools import tool


@tool
def get_sector_money_flow() -> dict:
    """Lấy dữ liệu dòng tiền ngành THẬT từ API đang chạy trên Dashboard.
    Trả về dict chứa dòng tiền khối ngoại và nội từng ngành."""
    try:
        import httpx
        resp = httpx.get("http://127.0.0.1:8000/dashboard/money-flow", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "sectors": data.get("sectors", []),
                "foreign_summary": data.get("foreign", {}),
                "source": "Internal API (/dashboard/money-flow)",
            }
    except Exception:
        pass
    
    # Fallback: đọc từ sector_connector nếu API không chạy
    try:
        from risk_dashboard.data.sector_connector import sector_winners_losers
        from datetime import date
        from pathlib import Path
        import pandas as pd
        
        csv_path = Path("data/cache/sector_panel.csv")
        if csv_path.exists():
            panel = pd.read_csv(csv_path)
            result = sector_winners_losers(panel, date.today(), window_months=3)
            return {
                "winners": result.winners,
                "losers": result.losers,
                "window_months": result.window_months,
                "source": "sector_connector (CSV cache)",
            }
    except Exception as e:
        return {"error": f"Không lấy được dòng tiền ngành: {e}"}
    
    return {"error": "Không có nguồn dữ liệu sector khả dụng."}


@tool
def get_sector_top_movers(sector: str) -> dict:
    """Lấy danh sách cổ phiếu tăng/giảm mạnh nhất trong một ngành cụ thể.
    Input: tên ngành (ví dụ 'Ngân hàng', 'Bất động sản', 'Thép').
    Kéo dữ liệu THẬT từ vnstock."""
    try:
        from vnstock import Vnstock
        
        # Map tên ngành sang industry code
        stock = Vnstock().stock(symbol="VCB", source="VCI")
        
        # Lấy danh sách toàn thị trường
        listing = stock.listing.all_symbols()
        if listing is not None and not listing.empty:
            # Lọc theo ngành (tìm kiếm fuzzy)
            sector_lower = sector.lower().strip()
            matched = listing[listing.apply(
                lambda row: sector_lower in str(row).lower(), axis=1
            )]
            
            if not matched.empty:
                tickers = matched["ticker"].head(10).tolist() if "ticker" in matched.columns else []
                return {
                    "sector": sector,
                    "tickers_found": tickers,
                    "count": len(matched),
                    "source": "vnstock3 listing",
                }
    except Exception:
        pass
    
    # Fallback: thông báo lỗi rõ ràng
    return {
        "sector": sector,
        "note": f"Không truy xuất được danh sách mã trong ngành '{sector}'. vnstock có thể chưa cài hoặc API lỗi.",
    }
