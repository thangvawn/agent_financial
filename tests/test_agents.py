import pandas as pd

from risk_dashboard.agents.graph import AgentState, run_eod_narrative, run_intent
from risk_dashboard.agents.reviewer import verify_narrative_against_quant
from risk_dashboard.agents.router import Intent, route_intent
from risk_dashboard.quant.eod_pipeline import run_quant_eod
from risk_dashboard.agents.narrative import build_narrative_bundle


def test_router_what_if():
    assert route_intent("Nếu NHNN ép tỷ giá về 25000 thì sao?") == Intent.what_if


def test_reviewer_accepts_template_narrative(synthetic_panel, as_of_date):
    q = run_quant_eod(synthetic_panel, as_of_date)
    n = build_narrative_bundle(q)
    r = verify_narrative_against_quant(n.body, q)
    assert r.ok, r.mismatches


def test_eod_manifest_review_ok(synthetic_panel, as_of_date):
    m = run_eod_narrative(synthetic_panel, as_of_date)
    assert m.review.ok


def test_chat_what_if(synthetic_panel, as_of_date):
    st = AgentState(panel=synthetic_panel, as_of=as_of_date)
    out = run_intent(st, "Giả sử tỷ giá về 20000")
    assert out["intent"] == "what_if"
    assert "20000" in out["text"] or "20" in out["text"]


def test_chat_sector_historical(synthetic_panel, as_of_date):
    ts = pd.Timestamp(as_of_date)
    m0 = ts + pd.offsets.MonthEnd(-1)
    m1 = ts + pd.offsets.MonthEnd(-2)
    sector = pd.DataFrame(
        {
            "month_end": [m1, m0],
            "sector_code": ["EXPORT", "BANK"],
            "return_pct": [1.2, -0.5],
        }
    )
    st = AgentState(panel=synthetic_panel, as_of=as_of_date, sector_panel=sector)
    out = run_intent(st, "nhóm ngành nào mạnh nhất theo lịch sử?")
    assert out["intent"] == "historical_sector"
    assert "EXPORT" in out["text"] or "mạnh" in out["text"]
