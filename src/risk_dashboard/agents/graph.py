from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

import pandas as pd

from risk_dashboard.agents.narrative import build_narrative_bundle
from risk_dashboard.agents.reviewer import extract_assumption_number, verify_narrative_against_quant
from risk_dashboard.agents.router import Intent, route_intent
from risk_dashboard.data.sector_connector import sector_winners_losers
from risk_dashboard.quant.eod_pipeline import run_quant_eod
from risk_dashboard.quant.scenario import rerun_with_macro_override
from risk_dashboard.schemas.snapshots import EODRunManifest, QuantEngineOutput


@dataclass
class AgentState:
    panel: pd.DataFrame
    as_of: date
    last_quant: QuantEngineOutput | None = None
    sector_panel: pd.DataFrame | None = None
    messages: list[dict[str, str]] = field(default_factory=list)


def run_eod_narrative(panel: pd.DataFrame, as_of: date, *, run_id: str | None = None) -> EODRunManifest:
    q = run_quant_eod(panel, as_of, run_id=run_id)
    narrative = build_narrative_bundle(q)
    review = verify_narrative_against_quant(narrative.body, q)
    return EODRunManifest(run_id=q.run_id, as_of=as_of, quant=q, narrative=narrative, review=review)


def run_intent(state: AgentState, user_message: str) -> dict[str, Any]:
    """Luồng đơn giản thay LangGraph: router → tool → trả lời có provenance."""
    intent = route_intent(user_message)
    state.messages.append({"role": "user", "content": user_message})

    if state.last_quant is None:
        state.last_quant = run_quant_eod(state.panel, state.as_of)

    q0 = state.last_quant
    reply: dict[str, Any] = {
        "intent": intent.value,
        "provenance": {"run_id": q0.run_id, "model_version": q0.model_version},
    }

    if intent == Intent.explain:
        reply["text"] = (
            f"Decision score: {q0.decision_score*100:.1f}/100. "
            f"Rủi ro 1 tuần {q0.horizons.p_decline_1w*100:.1f}%, "
            f"2 tuần {q0.horizons.p_decline_2w*100:.1f}%, "
            f"1 tháng {q0.horizons.p_decline_1m*100:.1f}%. "
            f"Biến chi phối SHAP: {q0.dominant_feature}."
        )
    elif intent == Intent.what_if:
        rate = extract_assumption_number(user_message)
        if rate is None:
            reply["text"] = "Vui lòng nêu rõ mức tỷ giá giả định (ví dụ 25000)."
        else:
            q1 = rerun_with_macro_override(state.panel, state.as_of, usd_vnd_rate=rate, run_id=None)
            reply["text"] = (
                f"Mô phỏng: nếu USD/VND = {rate:.0f}, decision score "
                f"{q1.decision_score*100:.1f}/100 (trước đó {q0.decision_score*100:.1f}/100), "
                f"rủi ro 2 tuần {q1.horizons.p_decline_2w*100:.1f}% "
                f"(trước đó {q0.horizons.p_decline_2w*100:.1f}%)."
            )
            reply["provenance"]["scenario_run_id"] = q1.run_id
    elif intent == Intent.historical_sector:
        if state.sector_panel is not None and not state.sector_panel.empty:
            wl = sector_winners_losers(state.sector_panel, state.as_of, window_months=6, top_k=5)
            w_txt = ", ".join(f"{c} ({v:+.1f}%)" for c, v in wl.winners[:5])
            l_txt = ", ".join(f"{c} ({v:+.1f}%)" for c, v in wl.losers[:5])
            reply["text"] = (
                f"Tổng lợi ~{wl.window_months} tháng (mô hình đơn giản trên dữ liệu đã nạp): "
                f"mạnh: {w_txt or '—'}; yếu: {l_txt or '—'}."
            )
        else:
            reply["text"] = (
                "Chưa có bảng ngành — cung cấp CSV (month_end, sector_code, return_pct) "
                "và gán AgentState.sector_panel."
            )
    else:
        reply["text"] = "Tôi là trợ lý định lượng: hãy hỏi về rủi ro, SHAP hoặc kịch bản tỷ giá."

    state.messages.append({"role": "assistant", "content": reply["text"]})
    return reply
