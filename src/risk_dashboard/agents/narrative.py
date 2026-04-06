from risk_dashboard.schemas.snapshots import NarrativeBundle, QuantEngineOutput


def build_narrative_bundle(q: QuantEngineOutput) -> NarrativeBundle:
    """Sinh narrative từ output định lượng — template deterministic để reviewer kiểm được."""
    decision = q.decision_score * 100.0
    p1 = q.horizons.p_decline_1w * 100.0
    p2 = q.horizons.p_decline_2w * 100.0
    p1m = q.horizons.p_decline_1m * 100.0
    dd = q.horizons.expected_drawdown_pct
    fx = float(q.narrative_inputs.get("usd_vnd_rate", 0.0))
    vn = float(q.narrative_inputs.get("vn_index", 0.0))
    headline = f"DECISION SCORE: {decision:.0f}/100, rủi ro 2 tuần ~{p2:.0f}%"
    body = (
        f"Decision score hiện tại: {decision:.1f}/100, regime {q.risk_regime}. "
        f"Xác suất điều chỉnh 1 tuần tới: {p1:.1f}%. "
        f"Xác suất thị trường điều chỉnh trong 2 tuần tới: {p2:.1f}%. "
        f"Xác suất điều chỉnh 1 tháng tới: {p1m:.1f}%. "
        f"Mức giảm kỳ vọng (mô hình): {dd:.2f}%. "
        f"Biến chi phối chính: {q.dominant_feature}. "
        f"VN-Index tham chiếu {vn:.2f} điểm; tỷ giá USD/VND {fx:.2f}. "
        f"{q.var_summary.note}"
    )
    bullets = [
        f"Decision score {decision:.1f}/100 với risk regime {q.risk_regime}",
        f"SHAP: trọng số cao nhất thuộc {q.dominant_feature}",
        "Ưu tiên giảm rủi ro khi các horizon ngắn và trung bình cùng xấu đi",
    ]
    mobile = f"Score {decision:.0f}/100, rủi ro 2 tuần ~{p2:.0f}%, chính: {q.dominant_feature}"
    return NarrativeBundle(
        headline=headline,
        body=body,
        bullet_highlights=bullets,
        verification_flag=True,
        mobile_one_liner=mobile,
    )
