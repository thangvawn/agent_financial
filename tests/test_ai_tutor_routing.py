from __future__ import annotations

import pytest

from risk_dashboard.modules.ai_tutor.application.tutor_graph import classify_intent


@pytest.mark.parametrize(
    "surface, query, expected_intent",
    [
        ("learn", "Giải thích giúp em bài học về chỉ số ROE", "learn"),
        ("learn", "Cho em gợi ý câu hỏi trắc nghiệm số 2 với", "learn"),
        ("learn", "Ý nghĩa dòng tiền CFO là gì?", "learn"),
        ("quant", "Tính giúp em VaR 95% 1 ngày của danh mục", "quant"),
        ("quant", "Chỉ số CVaR phản ánh điều gì?", "quant"),
        ("quant", "Mô phỏng Monte Carlo rủi ro", "quant"),
        ("quant", "Báo cáo kiểm định mô hình benchmark", "quant"),
        ("checkpoint", "Kiểm tra kiến thức sau bài học", "checkpoint"),
        ("general", "Xin chào AI Tutor", "general"),
        ("general", "Bạn có thể làm được những gì?", "general"),
    ],
)
def test_deterministic_routing_accuracy(surface: str, query: str, expected_intent: str) -> None:
    intent = classify_intent(surface, query)
    assert intent == expected_intent


def test_unknown_query_falls_back_to_general() -> None:
    intent = classify_intent("unknown", "Thời tiết hôm nay thế nào?")
    assert intent == "general"

