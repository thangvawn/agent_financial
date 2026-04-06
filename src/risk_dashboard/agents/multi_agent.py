"""
Multi-Agent Investment Committee — LangGraph Orchestrator
=========================================================
Điều phối các Agent chuyên biệt thông qua LLM Structured Output.
Mỗi Agent được trang bị Tools riêng (import từ agents/tools/).
NGUYÊN TẮC: CHỈ PHÂN TÍCH & HỖ TRỢ — KHÔNG KHUYẾN NGHỊ MUA/BÁN.
"""
from __future__ import annotations

import logging
import os
import traceback
from typing import Annotated, Any, Dict, List, Literal, TypedDict
from dotenv import load_dotenv

from pydantic import BaseModel, Field
from langchain_core.messages import (
    BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage,
)
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END

# Tools — mỗi file một chức năng, không trộn lẫn
from risk_dashboard.agents.tools.macro import get_macro_indicators
from risk_dashboard.agents.tools.fundamental import get_financial_metrics
from risk_dashboard.agents.tools.quant import (
    get_quant_risk_score, run_what_if_simulation,
    compute_stock_risk_metrics, run_stress_test, run_var_backtest,
)
from risk_dashboard.agents.tools.sector import get_sector_money_flow, get_sector_top_movers
from risk_dashboard.agents.tools.portfolio import compute_portfolio_metrics

logger = logging.getLogger(__name__)

# ── Khởi tạo ────────────────────────────────────────────
load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.15)

GUARDRAIL = (
    "\n\n⚠️ NGUYÊN TẮC BẮT BUỘC: "
    "Bạn CHỈ được phân tích, giải thích, cung cấp dữ liệu. "
    "TUYỆT ĐỐI KHÔNG được đưa ra khuyến nghị MUA, BÁN, GIỮ, "
    "hay bất kỳ lời xúi giục giao dịch nào. "
    "Nếu người dùng yêu cầu, hãy từ chối lịch sự."
    "\n\nĐỊNH DẠNG PHẢN HỒI: Trả lời bằng Tiếng Việt, ngắn gọn nhưng sâu sắc. "
    "Nêu con số CỤ THỂ (có đơn vị). Giọng văn chuyên nghiệp như một "
    "Senior Analyst đang brief cho CIO. Dùng emoji nếu phù hợp (📊 📉 ⚠️ ✅)."
)


# ── 1. STATE ─────────────────────────────────────────────
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], "Lịch sử hội thoại"]
    next_agent: str
    quant_data: Dict[str, Any]
    simulation_params: Dict[str, Any]
    review_status: str
    final_response: str


# ── 2. SUPERVISOR (LLM Router) ───────────────────────────
class RouteDecision(BaseModel):
    """LLM trả về đúng tên Agent cần chuyển tiếp."""
    next_agent: Literal[
        "macro_agent",
        "fundamental_agent",
        "quant_risk_agent",
        "portfolio_agent",
        "sector_agent",
        "strategist_agent",
    ] = Field(..., description="Tên Agent phù hợp nhất")


SUPERVISOR_PROMPT = """
Bạn là Giám đốc Điều hành Khối Đầu tư của một quỹ quản lý tài sản.
Đọc câu hỏi của người dùng và chọn ĐÚNG 1 chuyên gia phù hợp nhất.

QUY TẮC ROUTING:
- macro_agent: Câu hỏi về kinh tế vĩ mô, lãi suất, tỷ giá, CPI, lạm phát, FED,
  chính sách tiền tệ, NHNN, "FED tăng lãi suất", "tỷ giá USD/VND".
- fundamental_agent: Câu hỏi về BCTC, P/E, P/B, ROE, doanh thu, lợi nhuận,
  sức khỏe tài chính của một mã cổ phiếu CỤ THỂ (VD: "FPT", "VCB").
- quant_risk_agent: Câu hỏi về rủi ro, VaR, drawdown, stress test, mô phỏng,
  xác suất giảm, risk score, "rủi ro FPT", "stress test", "What-if tỷ giá".
  Bao gồm cả câu hỏi đại ý "VN-INDEX thế nào", "thị trường ra sao".
- portfolio_agent: Câu hỏi về cấu trúc danh mục, phân bổ tài sản, tỷ trọng,
  beta portfolio, "danh mục 30% VCB 40% FPT".
- sector_agent: Câu hỏi về ngành, dòng tiền ngành, so sánh ngành,
  "ngân hàng vs bất động sản", nhóm cổ phiếu.
- strategist_agent: Câu hỏi tổng hợp, không rõ ý định, hoặc câu chào.

LƯU Ý QUAN TRỌNG:
- Nếu câu hỏi nhắc đến "stress test" hoặc "kịch bản cực đoan" → quant_risk_agent
- Nếu câu hỏi so sánh GIỮA các ngành → sector_agent
- Nếu câu hỏi nhắc đến tỷ giá/lãi suất kết hợp "nếu...thì" → quant_risk_agent (what-if)
- Nếu câu hỏi chung về FED, kinh tế → macro_agent
- "VN-INDEX hôm nay" → quant_risk_agent
"""


def supervisor_agent(state: AgentState) -> AgentState:
    last_msg = state["messages"][-1].content
    logger.info(f"[SUPERVISOR] Routing: '{last_msg[:80]}...'")
    decision = llm.with_structured_output(RouteDecision).invoke([
        {"role": "system", "content": SUPERVISOR_PROMPT},
        {"role": "user", "content": last_msg},
    ])
    logger.info(f"[SUPERVISOR] → {decision.next_agent}")
    return {"next_agent": decision.next_agent}


# ── 3. TOOL-CALLING ENGINE (ReAct Loop) ──────────────────
MAX_TOOL_ROUNDS = 2  # Cho phép agent gọi tools tối đa 2 lần liên tiếp

def _run_agent(system_prompt: str, tools: list, state: AgentState) -> str:
    """Vòng lặp ReAct cho mọi Agent — tự chọn tool, đọc kết quả, lý luận."""
    agent_llm = llm.bind_tools(tools) if tools else llm
    msgs = [SystemMessage(content=system_prompt + GUARDRAIL)] + list(state["messages"])

    for round_i in range(MAX_TOOL_ROUNDS + 1):
        response = agent_llm.invoke(msgs)

        # Nếu không gọi tool → đây là câu trả lời cuối cùng
        if not (hasattr(response, "tool_calls") and response.tool_calls):
            return response.content

        # Có tool calls → thực thi và nối kết quả
        msgs.append(response)
        tool_map = {t.name: t for t in tools}
        for tc in response.tool_calls:
            tool_name = tc["name"]
            logger.info(f"  [TOOL CALL] {tool_name}({tc['args']})")
            try:
                result = tool_map[tool_name].invoke(tc["args"])
            except Exception as e:
                result = f"Tool error: {e}"
            msgs.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

    # Fallback: lần cuối sau khi đã gọi tools
    response = agent_llm.invoke(msgs)
    return response.content


# ── 4. SPECIALIZED AGENTS ────────────────────────────────
def macro_agent(state: AgentState) -> AgentState:
    logger.info("[MACRO_AGENT] Running...")
    return {"final_response": _run_agent(
        "Bạn là Chuyên gia Kinh tế Vĩ mô cao cấp (Senior Macro Economist).\n"
        "Nhiệm vụ: Phân tích chuyên sâu tỷ giá USD/VND, lãi suất, CPI, chính sách tiền tệ.\n"
        "LUÔN gọi tool get_macro_indicators để lấy dữ liệu THẬT trước khi phân tích.\n"
        "Kết hợp dữ liệu với bối cảnh vĩ mô (FED, NHNN, dòng vốn ASEAN).\n"
        "Đưa ra nhận định rõ ràng với con số cụ thể.",
        [get_macro_indicators],
        state,
    )}

def fundamental_agent(state: AgentState) -> AgentState:
    logger.info("[FUNDAMENTAL_AGENT] Running...")
    return {"final_response": _run_agent(
        "Bạn là Phân tích viên Tài chính (Equity Research Analyst).\n"
        "Nhiệm vụ: Đọc và phân tích BCTC, P/E, P/B, ROE, EPS.\n"
        "LUÔN gọi tool get_financial_metrics để lấy dữ liệu THẬT.\n"
        "So sánh với trung bình ngành, nhận xét sức khỏe tài chính, "
        "chất lượng lợi nhuận, mức định giá hiện tại.",
        [get_financial_metrics],
        state,
    )}

def quant_risk_agent(state: AgentState) -> AgentState:
    logger.info("[QUANT_RISK_AGENT] Running...")
    return {"final_response": _run_agent(
        "Bạn là Quản trị Rủi ro Định lượng (Head of Quantitative Risk).\n"
        "Nhiệm vụ: Phân tích rủi ro thị trường với các chỉ số CHUYÊN SÂU.\n\n"
        "CÓ 5 TOOLS:\n"
        "1. get_quant_risk_score() — Risk Score tổng thể (HMM, GARCH, VaR, XGBoost)\n"
        "2. compute_stock_risk_metrics(ticker) — VaR, Beta, Sharpe cho 1 mã cụ thể\n"
        "3. run_what_if_simulation(usd_vnd_rate) — What-if tỷ giá\n"
        "4. run_stress_test() — Giả lập Thiên nga đen (COVID, Lehman, 1997)\n"
        "5. run_var_backtest() — Kiểm định Basel III (Kupiec, Christoffersen)\n\n"
        "QUY TẮC:\n"
        "- Nếu hỏi về rủi ro MỘT MÃ (FPT, VCB...) → dùng compute_stock_risk_metrics\n"
        "- Nếu hỏi 'VN-INDEX thế nào' / 'thị trường ra sao' → dùng get_quant_risk_score\n"
        "- Nếu hỏi 'nếu tỷ giá...' → dùng run_what_if_simulation\n"
        "- Nếu hỏi 'stress test' → dùng run_stress_test\n"
        "- Nếu hỏi 'kiểm định mô hình' → dùng run_var_backtest\n"
        "Có thể gọi nhiều tools cùng lúc để trả lời đầy đủ.",
        [get_quant_risk_score, run_what_if_simulation, compute_stock_risk_metrics,
         run_stress_test, run_var_backtest],
        state,
    )}

def sector_agent(state: AgentState) -> AgentState:
    logger.info("[SECTOR_AGENT] Running...")
    return {"final_response": _run_agent(
        "Bạn là Chuyên gia Phân tích Ngành (Sector Strategist).\n"
        "Nhiệm vụ: Phân tích dòng tiền luân chuyển giữa các nhóm ngành, "
        "xác định winner/loser, đánh giá sector rotation.\n"
        "LUÔN gọi get_sector_money_flow() trước để có dữ liệu thật.\n"
        "Khi so sánh ngành, hãy dùng cả get_sector_top_movers cho từng ngành.",
        [get_sector_money_flow, get_sector_top_movers],
        state,
    )}

def portfolio_agent(state: AgentState) -> AgentState:
    logger.info("[PORTFOLIO_AGENT] Running...")
    return {"final_response": _run_agent(
        "Bạn là Quản lý Danh mục Đầu tư (Portfolio Manager).\n"
        "Nhiệm vụ: Tính toán rủi ro danh mục, đánh giá phân bổ tài sản.\n"
        "LUÔN gọi compute_portfolio_metrics để tính toán THẬT bằng covariance matrix.\n"
        "Input format: 'TICKER:WEIGHT' phân cách dấu phẩy. VD: 'VCB:0.3,FPT:0.3,CASH:0.4'\n"
        "Phân tích: Sharpe, Vol, Max Drawdown dự kiến, mức đa dạng hóa.",
        [compute_portfolio_metrics],
        state,
    )}

def strategist_agent(state: AgentState) -> AgentState:
    logger.info("[STRATEGIST_AGENT] Synthesizing...")
    # Strategist nhận kết quả từ agent trước (nếu có) trong final_response
    existing = state.get("final_response", "")
    
    synthesis_prompt = (
        "Bạn là Chiến lược gia Trưởng (Chief Investment Strategist).\n"
        "Nhiệm vụ: Tổng hợp phân tích thành bản tin ngắn gọn, sắc bén.\n\n"
    )
    if existing:
        synthesis_prompt += (
            f"Đồng nghiệp chuyên gia đã phân tích như sau:\n"
            f"---\n{existing}\n---\n"
            f"Hãy TỔNG HỢP và bổ sung góc nhìn chiến lược. Giữ nguyên các con số quan trọng. "
            f"Thêm nhận định về bức tranh toàn cảnh và gợi ý góc phân tích tiếp theo."
        )
    else:
        synthesis_prompt += (
            "Bạn KHÔNG có dữ liệu phân tích từ chuyên gia. "
            "Hãy trả lời bằng kiến thức tổng quát, nhưng nêu rõ đây là nhận định chung, "
            "không dựa trên dữ liệu real-time."
        )
    
    return {"final_response": _run_agent(
        synthesis_prompt,
        [],  # Strategist dùng não thuần túy
        state,
    )}

def reviewer_agent(state: AgentState) -> AgentState:
    """Kiểm toán viên — chặn hallucination và nội dung vi phạm."""
    response = state.get("final_response", "")
    
    # Quick check: chặn các từ khóa mua/bán
    forbidden = ["nên mua", "nên bán", "hãy mua", "hãy bán", "khuyến nghị mua", "khuyến nghị bán"]
    for word in forbidden:
        if word in response.lower():
            logger.warning(f"[REVIEWER] BLOCKED: Phát hiện '{word}' trong phản hồi")
            return {
                "review_status": "FAIL",
                "final_response": (
                    "⚠️ Hệ thống phát hiện nội dung vi phạm quy định (khuyến nghị giao dịch). "
                    "Phản hồi đã bị chặn theo nguyên tắc an toàn. "
                    "Vui lòng hỏi lại theo hướng phân tích rủi ro."
                ),
            }
    
    logger.info("[REVIEWER] PASS")
    return {"review_status": "PASS", "final_response": response}


# ── 5. GRAPH EDGES ───────────────────────────────────────
def _route_after_supervisor(state: AgentState) -> str:
    return state["next_agent"]

def _check_review(state: AgentState) -> str:
    return END if state["review_status"] == "PASS" else END  # Không loop lại, chỉ block


# ── 6. BUILD GRAPH ───────────────────────────────────────
_graph_instance = None

def build_multi_agent_graph():
    g = StateGraph(AgentState)

    g.add_node("supervisor",        supervisor_agent)
    g.add_node("macro_agent",       macro_agent)
    g.add_node("fundamental_agent", fundamental_agent)
    g.add_node("quant_risk_agent",  quant_risk_agent)
    g.add_node("portfolio_agent",   portfolio_agent)
    g.add_node("sector_agent",      sector_agent)
    g.add_node("strategist_agent",  strategist_agent)
    g.add_node("reviewer",          reviewer_agent)

    g.add_edge(START, "supervisor")

    g.add_conditional_edges("supervisor", _route_after_supervisor, {
        "macro_agent":       "macro_agent",
        "fundamental_agent": "fundamental_agent",
        "quant_risk_agent":  "quant_risk_agent",
        "portfolio_agent":   "portfolio_agent",
        "sector_agent":      "sector_agent",
        "strategist_agent":  "strategist_agent",
    })

    for agent in ["macro_agent", "fundamental_agent", "quant_risk_agent",
                  "portfolio_agent", "sector_agent"]:
        g.add_edge(agent, "strategist_agent")

    g.add_edge("strategist_agent", "reviewer")
    g.add_conditional_edges("reviewer", _check_review, {
        END: END,
    })

    return g.compile()


def get_graph():
    """Singleton — build graph 1 lần, tái sử dụng."""
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = build_multi_agent_graph()
    return _graph_instance


# ── 7. PUBLIC API ────────────────────────────────────────
def run_chat(user_message: str) -> dict:
    """
    Entry point cho chat API — chạy full multi-agent pipeline.
    Returns: {"text": str, "route": str, "provenance": dict}
    """
    graph = get_graph()
    
    state = {
        "messages": [HumanMessage(content=user_message)],
        "next_agent": "",
        "quant_data": {},
        "simulation_params": {},
        "review_status": "",
        "final_response": "",
    }
    
    try:
        result = graph.invoke(state)
        return {
            "text": result.get("final_response", "Không có phản hồi từ hệ thống."),
            "route": result.get("next_agent", "unknown"),
            "provenance": {
                "model_version": "multi-agent-v2",
                "run_id": f"chat-{id(result)}",
                "agent_pipeline": f"supervisor → {result.get('next_agent', '?')} → strategist → reviewer",
            },
        }
    except Exception as e:
        logger.error(f"[MULTI-AGENT ERROR] {traceback.format_exc()}")
        return {
            "text": f"⚠️ Hệ thống gặp lỗi khi xử lý: {str(e)}",
            "route": "error",
            "provenance": {"model_version": "multi-agent-v2", "error": str(e)},
        }


# ── 8. CLI TEST ──────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    test_questions = [
        "Phân tích rủi ro FPT cho tôi",
        "VN-INDEX hôm nay thế nào?",
        "Nếu Fed tăng lãi suất 50bps thì sao?",
        "So sánh rủi ro ngân hàng vs bất động sản",
        "Stress test danh mục 30% VCB, 30% FPT, 40% tiền mặt",
    ]
    
    for q in test_questions:
        print(f"\n{'='*60}")
        print(f"[USER]: {q}")
        print("-" * 60)
        result = run_chat(q)
        print(f"[ROUTE]: {result['route']}")
        print(f"[ANSWER]: {result['text'][:300]}...")
        print(f"[PIPELINE]: {result['provenance'].get('agent_pipeline', 'N/A')}")
