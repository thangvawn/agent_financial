"""Topic taxonomy for the learning catalog.

Three tiers aligned with the existing learning module: ``financial_basics``,
``basic_investing_literacy``, ``product_tool_literacy``. Topics are slugged
identifiers used both in seed rows of ``learning_topics`` and in the per-
resource ``topics_json`` arrays so we can render UI groupings without joins
for the common case.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Topic:
    topic_id: str
    label_vi: str
    label_en: str
    tier: str
    description: str
    sort_order: int


TOPICS: tuple[Topic, ...] = (
    # Tier 1 – Financial basics
    Topic("budgeting", "Lập ngân sách cá nhân", "Personal budgeting",
          "financial_basics", "Quản lý thu chi, dòng tiền cá nhân.", 10),
    Topic("saving", "Tiết kiệm & quỹ dự phòng", "Saving & emergency fund",
          "financial_basics", "Quỹ dự phòng, kỷ luật tiết kiệm.", 20),
    Topic("time_value_of_money", "Giá trị thời gian của tiền", "Time value of money",
          "financial_basics", "Lãi suất, chiết khấu, lãi kép.", 30),
    Topic("inflation", "Lạm phát", "Inflation",
          "financial_basics", "CPI, kỳ vọng lạm phát, ảnh hưởng đến chi tiêu.", 40),
    Topic("banking_products", "Sản phẩm ngân hàng", "Banking products",
          "financial_basics", "Tiết kiệm có kỳ hạn, thẻ tín dụng, vay tiêu dùng.", 50),

    # Tier 2 – Basic investing literacy
    Topic("portfolio_theory", "Lý thuyết danh mục", "Portfolio theory",
          "basic_investing_literacy", "MPT, đa dạng hoá, hiệu quả biên.", 110),
    Topic("asset_classes", "Lớp tài sản", "Asset classes",
          "basic_investing_literacy", "Cổ phiếu, trái phiếu, hàng hoá, BĐS.", 120),
    Topic("stocks", "Cổ phiếu", "Stocks",
          "basic_investing_literacy", "Phân tích cổ phiếu, định giá cơ bản.", 130),
    Topic("bonds", "Trái phiếu", "Bonds",
          "basic_investing_literacy", "Lợi suất, duration, đường cong lợi suất.", 140),
    Topic("etfs_funds", "ETF & quỹ", "ETFs & funds",
          "basic_investing_literacy", "Quỹ mở, ETF, phí, tracking error.", 150),
    Topic("risk_management", "Quản trị rủi ro", "Risk management",
          "basic_investing_literacy", "VaR, drawdown, position sizing.", 160),
    Topic("behavioral_finance", "Tài chính hành vi", "Behavioral finance",
          "basic_investing_literacy", "Bias nhận thức, kỷ luật giao dịch.", 170),

    # Tier 3 – Product / tool literacy
    Topic("financial_statements", "Báo cáo tài chính", "Financial statements",
          "product_tool_literacy", "Đọc BCTC, phân tích chất lượng lợi nhuận.", 210),
    Topic("valuation", "Định giá", "Valuation",
          "product_tool_literacy", "DCF, multiples, residual income.", 220),
    Topic("technical_analysis", "Phân tích kỹ thuật", "Technical analysis",
          "product_tool_literacy", "Trend, momentum, mean reversion.", 230),
    Topic("quantitative_finance", "Tài chính định lượng", "Quantitative finance",
          "product_tool_literacy", "Mô hình factor, machine learning trong tài chính.", 240),
    Topic("derivatives", "Phái sinh", "Derivatives",
          "product_tool_literacy", "Future, option, swap.", 250),
    Topic("macroeconomics", "Kinh tế vĩ mô", "Macroeconomics",
          "product_tool_literacy", "Chính sách tiền tệ, tài khoá, cycles.", 260),
    Topic("vietnam_market", "Thị trường Việt Nam", "Vietnam market",
          "product_tool_literacy", "Đặc thù sàn HOSE/HNX, vĩ mô VN.", 270),
)


TOPIC_BY_ID: dict[str, Topic] = {t.topic_id: t for t in TOPICS}


def tier_for_topic(topic_id: str) -> str:
    topic = TOPIC_BY_ID.get(topic_id)
    return topic.tier if topic else "basic_investing_literacy"


def normalize_topics(topics: list[str]) -> list[str]:
    return [t for t in topics if t in TOPIC_BY_ID]
