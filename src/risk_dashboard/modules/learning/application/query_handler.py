"""On-demand interactive query handler for Learning Telegram requests."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, List
import urllib.parse

from risk_dashboard.modules.learning.domain.entities import LearningLesson
from risk_dashboard.platform.telegram.command_parser import ParsedCommand
from risk_dashboard.platform.telegram.formatter import escape_html, safe_bold, safe_italic
from risk_dashboard.platform.telegram.section_packer import pack_sections

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LearningCard:
    card_id: str
    title: str
    topic: str
    difficulty: str
    summary: str
    key_takeaway: str
    example: str | None = None
    source_url: str | None = None


DEFAULT_LEARNING_CARDS: List[LearningCard] = [
    LearningCard(
        card_id="card_roe_01",
        title="Chỉ số ROE (Return on Equity)",
        topic="dinh_gia",
        difficulty="Cơ bản",
        summary="ROE đo lường hiệu quả sử dụng vốn chủ sở hữu của doanh nghiệp. ROE = LNST / Vốn chủ sở hữu.",
        key_takeaway="Doanh nghiệp tốt duy trì ROE > 15% liên tục trong 3-5 năm.",
        example="FPT đạt ROE ~25%, phản ánh năng lực sinh lời cao trên mỗi đồng vốn cổ đông.",
    ),
    LearningCard(
        card_id="card_cfo_01",
        title="Chất lượng dòng tiền CFO / LNST",
        topic="bctc",
        difficulty="Trung cấp",
        summary="Tỷ lệ CFO / LNST đánh giá liệu lợi nhuận báo cáo có thực sự tạo ra tiền mặt hay chỉ nằm trên sổ sách.",
        key_takeaway="Tỷ lệ CFO / LNST > 1.0 cho thấy lợi nhuận có chất lượng cao.",
        example="Nếu doanh nghiệp báo lãi 1,000 tỷ nhưng CFO âm, cần kiểm tra các khoản phải thu và tồn kho.",
    ),
    LearningCard(
        card_id="card_risk_01",
        title="Quản trị rủi ro & Tỷ lệ Nợ / Vốn CSH",
        topic="quan_tri_rui_ro",
        difficulty="Cơ bản",
        summary="Tỷ lệ Nợ vay / Vốn CSH đo lường mức độ đòn bẩy tài chính của doanh nghiệp.",
        key_takeaway="Nợ/VCSH > 1.5x có thể gia tăng rủi ro thanh khoản khi lãi suất tăng.",
        example="Trong ngành sản xuất, doanh nghiệp duy trì Nợ/VCSH < 0.8x có vùng đệm an toàn cao.",
    ),
    LearningCard(
        card_id="card_ta_01",
        title="Đường trung bình động (SMA 20/50)",
        topic="phan_tich_ky_thuat",
        difficulty="Cơ bản",
        summary="SMA 20 đo xu hướng giá ngắn hạn, SMA 50 đo xu hướng trung hạn.",
        key_takeaway="Khi SMA 20 cắt lên SMA 50 (Golden Cross), báo hiệu xu hướng tăng điểm hình thành.",
        example="VN-Index duy trì nằm trên đường SMA 20 thể hiện xu hướng tăng giá ngắn hạn tích cực.",
    ),
]

AVAILABLE_TOPICS = {
    "dinh_gia": "Định giá & Tỷ số tài chính",
    "bctc": "Đọc hiểu Báo cáo tài chính",
    "quan_tri_rui_ro": "Quản trị rủi ro & Đòn bẩy",
    "phan_tich_ky_thuat": "Phân tích kỹ thuật & Xu hướng",
}


def sanitize_url(url: str | None) -> str | None:
    if not url:
        return None
    url_clean = url.strip()
    if url_clean.startswith("http://") or url_clean.startswith("https://"):
        return urllib.parse.quote(url_clean, safe=":/?&=%#~-")
    return None


class LearningTelegramQueryHandler:
    def __init__(self, cards: List[LearningCard] | None = None) -> None:
        self.cards = cards or DEFAULT_LEARNING_CARDS

    def handle(self, cmd: ParsedCommand) -> List[str]:
        """Handles /learn and /learn <topic> queries."""
        topic_arg: str | None = None
        if cmd.args:
            raw_topic = cmd.args[0].strip().lower()
            if raw_topic in AVAILABLE_TOPICS:
                topic_arg = raw_topic
            else:
                # Check for friendly aliases
                alias_map = {
                    "dinhgia": "dinh_gia",
                    "risk": "quan_tri_rui_ro",
                    "ta": "phan_tich_ky_thuat",
                    "bctc": "bctc",
                }
                topic_arg = alias_map.get(raw_topic)
                if not topic_arg:
                    topics_fmt = ", ".join([f"<code>{k}</code>" for k in AVAILABLE_TOPICS.keys()])
                    return [
                        f"ℹ️ <b>Không tìm thấy chủ đề:</b> <code>{escape_html(raw_topic)}</code>\n\n"
                        f"Các chủ đề hiện có: {topics_fmt}"
                    ]

        matching_cards = [c for c in self.cards if c.topic == topic_arg] if topic_arg else self.cards
        if not matching_cards:
            return ["ℹ️ <b>Chưa có bài học phù hợp cho chủ đề này.</b>"]

        # Return first matching card
        card = matching_cards[0]
        sections = render_learning_card(card)
        return pack_sections(sections)


def render_learning_card(card: LearningCard) -> List[str]:
    title_escaped = escape_html(card.title)
    topic_label = escape_html(AVAILABLE_TOPICS.get(card.topic, card.topic))
    diff_escaped = escape_html(card.difficulty)
    summary_escaped = escape_html(card.summary)
    takeaway_escaped = escape_html(card.key_takeaway)

    lines = [
        f"💡 {safe_bold(title_escaped)}\n"
        f"🏷 <i>Chủ đề: {topic_label} · Mức độ: {diff_escaped}</i>\n",
        f"📝 <b>Tóm tắt:</b> {summary_escaped}\n",
        f"🎯 <b>Điểm cốt lõi:</b> {takeaway_escaped}",
    ]

    if card.example:
        lines.append(f"\n📌 <b>Ví dụ minh họa:</b> {escape_html(card.example)}")

    clean_url = sanitize_url(card.source_url)
    if clean_url:
        lines.append(f'\n🔗 <a href="{clean_url}">Xem chi tiết bài học</a>')

    return ["\n".join(lines)]
