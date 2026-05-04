"""
Trading Lab — Multi-agent LLM dành CHỈ cho admin (nghiên cứu / paper strategy).

Khác chat công khai: được thảo luận mua/bán/giữ như giả thuyết trong sandbox.
Không kết nối broker; mọi "lệnh" đều giả định trừ khi tích hợp riêng.

Kích hoạt: đặt ADMIN_TRADING_LAB_KEY trong .env và gọi API với header
X-Admin-Trading-Lab-Key.
"""
from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from risk_dashboard.agents.tools.fundamental import get_financial_metrics
from risk_dashboard.agents.tools.macro import get_macro_indicators
from risk_dashboard.agents.tools.quant import (
    compute_stock_risk_metrics,
    get_quant_risk_score,
    run_what_if_simulation,
    run_stress_test,
)
from risk_dashboard.quant.backtest import parse_ticker_list

load_dotenv()
logger = logging.getLogger(__name__)

_TRADING_LAB_LOG = Path("data/trading_lab/paper_notes.jsonl")

MAX_TOOL_ROUNDS = 4

llm_lab = ChatOpenAI(model=os.getenv("TRADING_LAB_MODEL", "gpt-4o-mini"), temperature=0.2)

STRATEGY_LAB_ROLE_META: dict[str, dict[str, str]] = {
    "analyst": {
        "label": "Nhà phân tích",
        "focus": "Làm rõ thesis, catalyst, điều kiện vô hiệu và mã phù hợp với bối cảnh.",
        "system": """Bạn là Agent Nhà phân tích trong Strategy Lab.

NHIỆM VỤ:
- Đọc thesis/backtest context và đề xuất 1 góc nhìn đầu tư khả thi.
- Nói rõ catalyst, luận điểm chính, điều gì có thể khiến luận điểm sai.
- Nếu người dùng chưa nêu mã, có thể gợi ý tối đa 5 mã VN phù hợp.

YÊU CẦU:
- Trả lời tiếng Việt, súc tích nhưng có cấu trúc.
- Không nói về broker/lệnh thật.
- Dùng các mục: Thesis, Catalyst, Mã nên xem, Điều kiện vô hiệu.
""",
    },
    "risk_manager": {
        "label": "Nhà quản trị rủi ro",
        "focus": "Đặt risk budget, kiểm soát tập trung, drawdown chấp nhận được và cảnh báo sai lệch.",
        "system": """Bạn là Agent Quản trị rủi ro trong Strategy Lab.

NHIỆM VỤ:
- Đánh giá risk budget, tập trung danh mục, rủi ro beta, drawdown và điều kiện cần giảm size.
- Đề xuất nguyên tắc quản trị vị thế phù hợp cho backtest paper.

YÊU CẦU:
- Trả lời tiếng Việt.
- Dùng các mục: Risk budget, Rủi ro chính, Giới hạn vị thế, Điều kiện giảm size.
""",
    },
    "stop_loss": {
        "label": "Agent Stop-loss",
        "focus": "Thiết kế nguyên tắc SL/thoát lệnh/take-profit ở mức policy để người dùng kiểm thử sau.",
        "system": """Bạn là Agent Stop-loss trong Strategy Lab.

NHIỆM VỤ:
- Đề xuất stop-loss policy, trailing logic, take-profit logic và khi nào thoát vì thesis hỏng.
- Lưu ý rõ đây là policy research; engine backtest hiện tại có thể chưa mô phỏng execution rule này.

YÊU CẦU:
- Trả lời tiếng Việt.
- Dùng các mục: Stop-loss cứng, Stop-loss động, Chốt lời, Thoát theo thesis.
""",
    },
    "portfolio_designer": {
        "label": "Kiến trúc sư danh mục",
        "focus": "Đề xuất danh sách mã, trọng số và cấu trúc danh mục để đổ vào backtest.",
        "system": """Bạn là Agent Kiến trúc sư danh mục trong Strategy Lab.

NHIỆM VỤ:
- Đề xuất cấu trúc danh mục gọn để backtest: số mã, trọng số, lý do phân bổ.
- Nếu người dùng đã nêu mã, hãy ưu tiên dùng chính các mã đó.

YÊU CẦU:
- Trả lời tiếng Việt.
- Dùng các mục: Danh mục đề xuất, Trọng số, Vì sao phân bổ như vậy.
""",
    },
}
_DEFAULT_STRATEGY_ROLES = ["analyst", "risk_manager", "stop_loss", "portfolio_designer"]


def list_strategy_lab_roles() -> list[dict[str, str]]:
    return [
        {"id": role_id, "label": meta["label"], "focus": meta["focus"]}
        for role_id, meta in STRATEGY_LAB_ROLE_META.items()
    ]


def _normalize_strategy_roles(roles: list[str] | None) -> list[str]:
    if not roles:
        return list(_DEFAULT_STRATEGY_ROLES)

    aliases = {
        "analysis": "analyst",
        "analyst_agent": "analyst",
        "research": "analyst",
        "risk": "risk_manager",
        "risk_manager_agent": "risk_manager",
        "sl": "stop_loss",
        "stoploss": "stop_loss",
        "stop_loss_agent": "stop_loss",
        "portfolio": "portfolio_designer",
        "portfolio_manager": "portfolio_designer",
        "portfolio_designer_agent": "portfolio_designer",
    }

    out: list[str] = []
    for raw in roles:
        key = re.sub(r"[^a-z_]+", "", str(raw or "").strip().lower())
        key = aliases.get(key, key)
        if key in STRATEGY_LAB_ROLE_META and key not in out:
            out.append(key)
    return out or list(_DEFAULT_STRATEGY_ROLES)


def _build_strategy_context(
    *,
    brief: str,
    tickers: list[str] | None,
    start_date: str | None,
    end_date: str | None,
    initial_capital: float | None,
    risk_budget_pct: float | None,
    holding_period: str | None,
    notes: str | None,
) -> str:
    tickers_text = ", ".join(tickers or []) if tickers else "Chưa khóa mã, cho phép đề xuất mới"
    cap_text = f"{initial_capital:,.0f} VNĐ" if initial_capital is not None else "Chưa nêu"
    risk_text = f"{risk_budget_pct:.2f}%" if risk_budget_pct is not None else "Chưa nêu"
    return "\n".join(
        [
            f"Brief chiến lược: {brief.strip()}",
            f"Mã ưu tiên / vũ trụ hiện tại: {tickers_text}",
            f"Khoảng backtest: {start_date or '--'} -> {end_date or '--'}",
            f"Vốn dự kiến: {cap_text}",
            f"Risk budget tối đa: {risk_text}",
            f"Holding period mong muốn: {holding_period or 'Chưa nêu'}",
            f"Ghi chú thêm: {(notes or '').strip() or 'Không có'}",
        ]
    )


def _invoke_strategy_role(role_id: str, context_text: str) -> str:
    meta = STRATEGY_LAB_ROLE_META[role_id]
    response = llm_lab.invoke(
        [
            SystemMessage(content=meta["system"]),
            HumanMessage(content=context_text),
        ]
    )
    return str(response.content or "").strip()


def _extract_json_object(text: str) -> dict[str, Any] | None:
    raw = str(text or "").strip()
    if not raw:
        return None

    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()

    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    candidate = raw[start : end + 1]
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _sanitize_backtest_ready(payload: dict[str, Any], requested_tickers: list[str] | None) -> dict[str, Any]:
    raw_tickers = payload.get("tickers")
    if isinstance(raw_tickers, list):
        tickers_source = [str(x) for x in raw_tickers]
    elif requested_tickers:
        tickers_source = requested_tickers
    else:
        tickers_source = []

    try:
        tickers = parse_ticker_list(tickers_source)[:8] if tickers_source else []
    except ValueError:
        tickers = requested_tickers or []

    raw_weights = payload.get("weights")
    weights_clean: dict[str, float] = {}
    if isinstance(raw_weights, dict):
        for key, value in raw_weights.items():
            tk = re.sub(r"[^A-Za-z0-9]", "", str(key or "").upper())
            if tk in tickers:
                try:
                    weights_clean[tk] = float(value)
                except (TypeError, ValueError):
                    continue

    positive_sum = sum(v for v in weights_clean.values() if v > 0)
    if tickers and len(weights_clean) == len(tickers) and positive_sum > 0:
        weights_clean = {k: round(v / positive_sum, 4) for k, v in weights_clean.items()}
        equal_weight = False
    elif tickers:
        equal_weight = True
        weights_clean = {tk: round(1.0 / len(tickers), 4) for tk in tickers}
    else:
        equal_weight = True

    return {
        "tickers": tickers,
        "equal_weight": equal_weight,
        "weights": weights_clean,
    }


def _sanitize_execution_rule(payload: dict[str, Any] | None) -> dict[str, Any]:
    raw = dict(payload or {})
    strategy_type = str(raw.get("strategy_type") or "").strip().lower()
    if strategy_type not in {"volume_btc_confirm_stop_loss"}:
        strategy_type = ""

    params_raw = raw.get("params") if isinstance(raw.get("params"), dict) else {}
    try:
        volume_spike_multiplier = float(params_raw.get("volume_spike_multiplier", 2.0))
    except (TypeError, ValueError):
        volume_spike_multiplier = 2.0
    try:
        btc_daily_change_min_pct = float(params_raw.get("btc_daily_change_min_pct", 3.0))
    except (TypeError, ValueError):
        btc_daily_change_min_pct = 3.0
    try:
        stop_loss_pct = float(params_raw.get("stop_loss_pct", 4.0))
    except (TypeError, ValueError):
        stop_loss_pct = 4.0

    unsupported_parts = raw.get("unsupported_parts")
    if not isinstance(unsupported_parts, list):
        unsupported_parts = []
    unsupported_parts = [str(item) for item in unsupported_parts if str(item).strip()]

    summary = str(raw.get("summary") or "").strip()
    parser_notes = raw.get("parser_notes")
    if not isinstance(parser_notes, list):
        parser_notes = []
    parser_notes = [str(item) for item in parser_notes if str(item).strip()]

    enabled = bool(raw.get("enabled")) and bool(strategy_type)
    return {
        "enabled": enabled,
        "strategy_type": strategy_type or None,
        "summary": summary or "Chưa parse được rule execution cụ thể từ prompt.",
        "params": {
            "volume_spike_multiplier": max(1.0, min(volume_spike_multiplier, 20.0)),
            "btc_daily_change_min_pct": max(-50.0, min(btc_daily_change_min_pct, 50.0)),
            "stop_loss_pct": max(0.1, min(stop_loss_pct, 50.0)),
        },
        "parser_notes": parser_notes,
        "unsupported_parts": unsupported_parts,
    }


def _fallback_strategy_blueprint(
    *,
    brief: str,
    requested_tickers: list[str] | None,
    risk_budget_pct: float | None,
    holding_period: str | None,
    role_ids: list[str],
) -> dict[str, Any]:
    backtest_ready = _sanitize_backtest_ready({}, requested_tickers)
    return {
        "title": "Blueprint chiến lược nháp",
        "summary": "Chưa parse được JSON chiến lược từ mô hình, nên hệ thống trả một khung nháp để bạn chỉnh tiếp.",
        "thesis": brief.strip(),
        "universe": backtest_ready["tickers"],
        "suggested_weights": backtest_ready["weights"],
        "holding_period": holding_period or "1-3 tháng",
        "rebalance_policy": "Backtest hiện tại là buy-and-hold, chưa tái cân bằng động.",
        "entry_policy": "Ưu tiên vào lệnh khi thesis còn nguyên vẹn và phân bổ không vượt risk budget.",
        "exit_policy": "Thoát khi thesis hỏng hoặc rủi ro danh mục vượt mức chấp nhận.",
        "stop_loss_policy": "Policy SL cần rà lại thủ công; engine hiện chưa mô phỏng execution/SL.",
        "take_profit_policy": "Chốt lời theo target hoặc khi xác suất bất lợi tăng mạnh.",
        "risk_budget_pct": risk_budget_pct,
        "agent_order": role_ids,
        "checklist": [
            "Xác nhận thesis và catalyst còn hợp lệ.",
            "Rà lại trọng số để tránh tập trung quá mức.",
            "Đọc cảnh báo của agent quản trị rủi ro trước khi backtest.",
        ],
        "warnings": [
            "Đây là bản nháp paper strategy.",
            "Backtest engine hiện mới mô phỏng buy-and-hold, chưa mô phỏng stop-loss execution.",
        ],
        "execution_rule": {
            "enabled": False,
            "strategy_type": None,
            "summary": "Chưa có execution rule chạy được vì hệ thống không parse được rule từ prompt.",
            "params": {},
            "parser_notes": ["Cần prompt rõ hơn về tín hiệu vào/thoát nếu muốn chạy backtest rule-based."],
            "unsupported_parts": [],
        },
        "backtest_ready": backtest_ready,
    }


def run_backtest_strategy_lab(
    *,
    brief: str,
    roles: list[str] | None = None,
    tickers: list[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    initial_capital: float | None = None,
    risk_budget_pct: float | None = None,
    holding_period: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    role_ids = _normalize_strategy_roles(roles)
    try:
        requested_tickers = parse_ticker_list(tickers) if tickers else []
    except ValueError as exc:
        raise ValueError(f"Ticker cho Strategy Lab không hợp lệ: {exc}") from exc
    context_text = _build_strategy_context(
        brief=brief,
        tickers=requested_tickers,
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital,
        risk_budget_pct=risk_budget_pct,
        holding_period=holding_period,
        notes=notes,
    )

    agent_outputs: list[dict[str, str]] = []
    for role_id in role_ids:
        memo = _invoke_strategy_role(role_id, context_text)
        meta = STRATEGY_LAB_ROLE_META[role_id]
        agent_outputs.append(
            {
                "role": role_id,
                "label": meta["label"],
                "focus": meta["focus"],
                "memo": memo,
            }
        )

    final_prompt = f"""Bạn là Chief Strategist trong Strategy Lab.

Mục tiêu: hợp nhất các memo bên dưới thành một blueprint chiến lược để người dùng có thể đổ ngay vào form backtest paper.

Bối cảnh:
{context_text}

Ý kiến từ các agent:
{json.dumps(agent_outputs, ensure_ascii=False, indent=2)}

Trả về DUY NHẤT một JSON object hợp lệ với schema:
{{
  "title": "string",
  "summary": "string",
  "thesis": "string",
  "universe": ["FPT", "VCB"],
  "suggested_weights": {{"FPT": 0.5, "VCB": 0.5}},
  "holding_period": "string",
  "rebalance_policy": "string",
  "entry_policy": "string",
  "exit_policy": "string",
  "stop_loss_policy": "string",
  "take_profit_policy": "string",
  "risk_budget_pct": 8.0,
  "agent_order": ["analyst", "risk_manager"],
  "checklist": ["string", "string"],
  "warnings": ["string", "string"],
  "execution_rule": {{
    "enabled": true,
    "strategy_type": "volume_btc_confirm_stop_loss",
    "summary": "string",
    "params": {{
      "volume_spike_multiplier": 2.0,
      "btc_daily_change_min_pct": 3.0,
      "stop_loss_pct": 4.0
    }},
    "parser_notes": ["string"],
    "unsupported_parts": ["string"]
  }},
  "backtest_ready": {{
    "tickers": ["FPT", "VCB"],
    "equal_weight": false,
    "weights": {{"FPT": 0.5, "VCB": 0.5}}
  }}
}}

Quy tắc:
- universe tối đa 8 mã.
- Ưu tiên mã người dùng đã nêu.
- Nếu chưa rõ trọng số thì vẫn phải điền weights hợp lệ.
- execution_rule hiện chỉ hỗ trợ đúng loại: volume_btc_confirm_stop_loss.
- Nếu prompt của người dùng có thể quy đổi về loại hỗ trợ này, hãy điền enabled=true và params cụ thể.
- Nếu prompt chứa phần chưa chạy được trong engine hiện tại, ghi chúng vào unsupported_parts thay vì bịa rule.
- Không thêm markdown hay text ngoài JSON.
"""

    final_response = llm_lab.invoke(
        [
            SystemMessage(
                content="Bạn là Chief Strategist tổng hợp output nhiều agent thành một blueprint backtest research."
            ),
            HumanMessage(content=final_prompt),
        ]
    )
    blueprint = _extract_json_object(str(final_response.content or ""))
    if blueprint is None:
        blueprint = _fallback_strategy_blueprint(
            brief=brief,
            requested_tickers=requested_tickers,
            risk_budget_pct=risk_budget_pct,
            holding_period=holding_period,
            role_ids=role_ids,
        )

    backtest_ready = _sanitize_backtest_ready(blueprint.get("backtest_ready") or {}, requested_tickers)
    execution_rule = _sanitize_execution_rule(blueprint.get("execution_rule"))
    blueprint["backtest_ready"] = backtest_ready
    blueprint["execution_rule"] = execution_rule
    blueprint["universe"] = blueprint.get("universe") or backtest_ready["tickers"]
    blueprint["suggested_weights"] = blueprint.get("suggested_weights") or backtest_ready["weights"]
    blueprint["agent_order"] = blueprint.get("agent_order") or role_ids
    if "risk_budget_pct" not in blueprint or blueprint.get("risk_budget_pct") is None:
        blueprint["risk_budget_pct"] = risk_budget_pct

    return {
        "mode": "backtest_strategy_lab",
        "agents": agent_outputs,
        "blueprint": blueprint,
        "supported_roles": list_strategy_lab_roles(),
        "limitations": [
            "Blueprint này phục vụ research và paper backtest.",
            "Execution rule hiện mới hỗ trợ một nhóm chiến lược đã được compile sang engine rule-based.",
            "LLM/NLP là lớp diễn giải chiến lược; tính đúng/sai cuối cùng vẫn phụ thuộc các primitive mà engine hỗ trợ.",
        ],
        "provenance": {
            "model": os.getenv("TRADING_LAB_MODEL", "gpt-4o-mini"),
            "role_count": len(role_ids),
            "sandbox": True,
            "no_broker": True,
        },
    }


@tool
def log_paper_strategy_note(note: str, tags: str = "") -> str:
    """Ghi chú chiến thuật paper / giả lập vào nhật ký cục bộ (audit). tags: ví dụ FPT,VNINDEX."""
    _TRADING_LAB_LOG.parent.mkdir(parents=True, exist_ok=True)
    line = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "note": note[:8000],
        "tags": (tags or "")[:500],
    }
    try:
        with _TRADING_LAB_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
    except OSError as e:
        logger.warning("trading_lab log write failed: %s", e)
        return f"Không ghi được log: {e}"
    return "Đã lưu ghi chú vào data/trading_lab/paper_notes.jsonl"


TRADING_LAB_TOOLS = [
    get_macro_indicators,
    get_financial_metrics,
    get_quant_risk_score,
    compute_stock_risk_metrics,
    run_what_if_simulation,
    run_stress_test,
    log_paper_strategy_note,
]

TRADING_LAB_SYSTEM = """Bạn là trợ lý trong Trading Lab — sandbox nghiên cứu CHỈ dành cho quản trị viên.

BỐI CẢNH:
- Được phân tích chiến lược giao dịch, giả thuyết mua/bán/giữ, sizing, điều kiện vào/thoát — như nội dung nghiên cứu và kiểm thử.
- Luôn gắn nhãn rõ: đây là paper / giả lập / giả thuyết, KHÔNG phải lệnh thật và hệ thống không gửi lệnh tới broker.

CÔNG CỤ:
- Dùng get_macro_indicators, get_financial_metrics, get_quant_risk_score, compute_stock_risk_metrics,
  run_what_if_simulation, run_stress_test khi cần số liệu thật.
- Dùng log_paper_strategy_note để ghi lại quyết định hoặc giả thuyết chiến lược cần lưu vết (audit).

QUY ƯỚC:
- Tiếng Việt, không emoji.
- Nêu số liệu cụ thể kèm đơn vị khi trích từ tool.
- Nhắc rủi ro mô hình và giới hạn dữ liệu khi suy luận dài hạn.
"""


def _run_trading_lab_loop(user_message: str) -> str:
    agent_llm = llm_lab.bind_tools(TRADING_LAB_TOOLS)
    msgs: list[Any] = [
        SystemMessage(content=TRADING_LAB_SYSTEM),
        HumanMessage(content=user_message),
    ]
    tool_map = {t.name: t for t in TRADING_LAB_TOOLS}

    for _ in range(MAX_TOOL_ROUNDS + 1):
        response = agent_llm.invoke(msgs)
        if not (hasattr(response, "tool_calls") and response.tool_calls):
            return str(response.content or "")

        msgs.append(response)
        for tc in response.tool_calls:
            name = tc["name"]
            logger.info("[TRADING_LAB] tool %s %s", name, tc.get("args"))
            try:
                result = tool_map[name].invoke(tc["args"])
            except Exception as e:
                result = f"Tool error: {e}"
            msgs.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

    final = agent_llm.invoke(msgs)
    return str(final.content or "")


def run_trading_lab_chat(user_message: str) -> dict[str, Any]:
    """Entrypoint API — trả về text + provenance."""
    text = _run_trading_lab_loop(user_message.strip())
    return {
        "text": text or "(Không có nội dung phản hồi.)",
        "mode": "trading_lab_admin",
        "provenance": {
            "model": os.getenv("TRADING_LAB_MODEL", "gpt-4o-mini"),
            "sandbox": True,
            "no_broker": True,
        },
    }
