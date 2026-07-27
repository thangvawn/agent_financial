"""Telegram HTML renderer and safe section chunk packer (< 3,800 chars per chunk)."""

from __future__ import annotations

import html
from risk_dashboard.modules.market_summary.domain.models import MarketSummaryReport

MAX_CHUNK_CHARS = 3800  # Safe margin below 4096 Telegram entity parsing limit


def escape_html(text: str) -> str:
    """Escapes special HTML characters (&, <, >)."""
    return html.escape(str(text), quote=False)


def format_percentage_diff(diff_pct: float | None, base_label: str) -> str | None:
    if diff_pct is None:
        return None
    abs_pct = abs(diff_pct)
    if abs_pct < 0.1:
        return f"↳ Tương đương {base_label}"
    comp = "Cao" if diff_pct > 0 else "Thấp"
    return f"↳ {comp} hơn {abs_pct:.1f}% so với {base_label}"


def render_report_sections(report: MarketSummaryReport, mode: str = "fast") -> list[str]:
    """Generates structured HTML sections for the Telegram report."""
    date_str = report.report_date.strftime("%d/%m/%Y")
    sections: list[str] = []

    # Section 0: Test Fixture Banner if applicable
    if report.provenance.data_mode == "fixture":
        sections.append("🧪 <b>DỮ LIỆU GIẢ LẬP — KHÔNG PHẢI DỮ LIỆU THỊ TRƯỜNG THỰC</b>")

    # Section 1: Header & Overview
    sec1_lines = [f"📊 <b>TỔNG KẾT THỊ TRƯỜNG — {date_str}</b>\n"]
    for idx in report.indices:
        sign = "+" if idx.change_points >= 0 else ""
        sec1_lines.append(f"🔹 <b>{escape_html(idx.symbol)}:</b> {idx.close:,.2f} điểm | {sign}{idx.change_pct:.2f}%")

    # Volume & Value stats with explicit scope
    if report.indices:
        vnindex = report.indices[0]
        val_bil = vnindex.value_vnd / 1e9 if vnindex.value_vnd > 0 else 0.0
        sec1_lines.append(f"🔹 <b>Giá trị giao dịch HOSE:</b> {val_bil:,.0f} tỷ đồng")
        
        vol_prev_text = format_percentage_diff(vnindex.vol_vs_prev_pct, "phiên trước")
        if vol_prev_text:
            sec1_lines.append(vol_prev_text)
            
        vol_sma_text = format_percentage_diff(vnindex.vol_vs_sma20_pct, "trung bình 20 phiên")
        if vol_sma_text:
            sec1_lines.append(vol_sma_text)

    sections.append("\n".join(sec1_lines))

    # Section 2: Market Breadth
    if report.breadth:
        b = report.breadth
        sec2 = (
            f"📈 <b>ĐỘ RỘNG THỊ TRƯỜNG ({escape_html(b.universe)})</b>\n"
            f"• Tăng: <b>{b.advancers}</b> | Giảm: <b>{b.decliners}</b> | Tham chiếu: <b>{b.unchanged}</b>\n"
            f"• Trần: <b>{b.ceiling}</b> | Sàn: <b>{b.floor}</b>\n"
            f"• <i>Đánh giá:</i> {escape_html(b.summary_assessment)}"
        )
        sections.append(sec2)

    # Section 3: Index Contributions
    if report.positive_movers or report.negative_movers:
        pos_str = ", ".join([f"<b>{escape_html(m.ticker)}</b> (+{m.points_impact:.2f})" for m in report.positive_movers[:4]])
        neg_str = ", ".join([f"<b>{escape_html(m.ticker)}</b> ({m.points_impact:.2f})" for m in report.negative_movers[:4]])
        sec3 = (
            "🎯 <b>TÁC ĐỘNG VN-INDEX</b>\n"
            f"• Kéo tăng: {pos_str or 'Không đáng kể'}\n"
            f"• Kéo giảm: {neg_str or 'Không đáng kể'}"
        )
        sections.append(sec3)

    # Section 4: Capital Flow with sign-dependent natural phrasing
    if report.capital_flow and report.capital_flow.is_available:
        cf = report.capital_flow
        net_val = cf.net_foreign_val_billion
        if net_val > 0.1:
            net_text = f"<b>mua ròng {net_val:,.1f}</b> tỷ đồng"
        elif net_val < -0.1:
            net_text = f"<b>bán ròng {abs(net_val):,.1f}</b> tỷ đồng"
        else:
            net_text = "<b>giao dịch cân bằng</b>"

        buy_str = ", ".join([f"<b>{escape_html(t)}</b> ({v:,.1f} tỷ)" for t, v in cf.top_foreign_buy[:3]])
        sell_str = ", ".join([f"<b>{escape_html(t)}</b> ({v:,.1f} tỷ)" for t, v in cf.top_foreign_sell[:3]])

        sec4_lines = [
            f"🏦 <b>KHỐI NGOẠI ({escape_html(cf.universe)})</b>",
            f"• Khối ngoại {net_text}",
        ]
        if buy_str:
            sec4_lines.append(f"• Mua ròng nổi bật: {buy_str}")
        if sell_str:
            sec4_lines.append(f"• Bán ròng nổi bật: {sell_str}")

        sections.append("\n".join(sec4_lines))

    # Section 5: Technical Overview (Analytical Mode)
    if mode == "analytical" and report.technical:
        tech = report.technical
        trend_str = "Tích cực (Tăng)" if tech.short_term_trend == "BULLISH" else ("Tiêu cực (Giảm)" if tech.short_term_trend == "BEARISH" else "Đi ngang (Tích lũy)")
        sec5 = (
            "🧭 <b>GÓC NHÌN KỸ THUẬT</b>\n"
            f"• Xu hướng ngắn hạn: <b>{trend_str}</b>\n"
            f"• Vùng hỗ trợ gần: <b>{tech.support_zone[0]:,.0f}–{tech.support_zone[1]:,.0f}</b> điểm\n"
            f"• Vùng kháng cự gần: <b>{tech.resistance_zone[0]:,.0f}–{tech.resistance_zone[1]:,.0f}</b> điểm"
        )
        sections.append(sec5)

    # Section 6: Next Session Watch Points
    if mode == "analytical" and report.technical and report.technical.watch_points:
        wp_lines = [f"• {escape_html(p)}" for p in report.technical.watch_points]
        sec6 = "👀 <b>PHIÊN TIẾP THEO</b>\n" + "\n".join(wp_lines)
        sections.append(sec6)

    # Section 7: Footer & Timestamp
    gen_time = report.generated_at.strftime("%H:%M")
    sec_footer = (
        f"⏱ <i>Dữ liệu cập nhật lúc {gen_time} ({report.timezone})</i>\n"
        "⚠️ <i>Nội dung mang tính tham khảo, không phải khuyến nghị đầu tư.</i>"
    )
    sections.append(sec_footer)

    return sections


def pack_sections(sections: list[str], max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Packs text sections into message chunks safely below max_chars."""
    chunks: list[str] = []
    current_chunk: list[str] = []
    current_len = 0

    for sec in sections:
        sec_len = len(sec)
        if current_len + sec_len + 2 > max_chars:
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = [sec]
                current_len = sec_len
            else:
                chunks.append(sec)
                current_chunk = []
                current_len = 0
        else:
            current_chunk.append(sec)
            current_len += sec_len + 2

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks
