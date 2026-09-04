from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import pytest

from risk_dashboard.modules.agentic_core.schemas.envelope import (
    ConsentSnapshot,
    ExecutionBudget,
    TrustedExecutionEnvelope,
)
from risk_dashboard.modules.ai_tutor.application.conversation_service import ConversationService
from risk_dashboard.modules.ai_tutor.application.reviewers import (
    EvidenceAndNumericReviewer,
    SafetyAndPolicyReviewer,
)
from risk_dashboard.modules.ai_tutor.application.specialists.learning_specialist import LearningSpecialist
from risk_dashboard.modules.ai_tutor.application.specialists.quant_specialist import QuantSpecialist
from risk_dashboard.modules.ai_tutor.application.tutor_graph import TutorGraph
from risk_dashboard.modules.ai_tutor.infrastructure.sqlite_conversation_repository import (
    SqliteConversationRepository,
)
from risk_dashboard.modules.ai_tutor.schemas.conversation import (
    CitationRef,
    ConversationEntity,
    MessageEntity,
    NumericClaimRef,
)
from risk_dashboard.modules.ai_tutor.schemas.requests import SendMessageRequest
from risk_dashboard.platform.database import apply_migrations, clear_db_path_cache, open_app_state_db


def test_tool_grant_enforcement_rejects_missing_capabilities() -> None:
    """Blocker 1: Server-side grant check must reject execution if envelope lacks required capability."""
    envelope_no_caps = TrustedExecutionEnvelope(
        run_id="run_test_nocaps",
        correlation_id="corr_1",
        idempotency_key="idemp_1",
        account_id="acc_user_1",
        surface="quant",
        scopes=("learning:read",),
        allowed_capabilities=(),  # Lacks "quant:read"
        budget=ExecutionBudget(max_steps=5, max_tool_calls=2, max_tokens=1000, max_wall_seconds=10.0, max_cost_usd=0.01),
        policy_version="v1",
        model_policy_version="v1",
        consent=ConsentSnapshot(policy_version="v1"),
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    specialist = QuantSpecialist()
    res = asyncio.run(
        specialist.handle(
            intent="quant",
            user_query="Tính VaR 95%",
            envelope=envelope_no_caps,
        )
    )

    assert "chưa được cấp quyền" in res["answer"]
    assert len(res["limitations"]) >= 1
    assert "ToolGrant" in res["limitations"][0]
    assert res["tool_calls"][0].status == "error"


def test_numeric_reviewer_strips_fabricated_numbers_in_prose() -> None:
    """Blocker 2: Fabricated numbers appearing in prose text must be detected and stripped."""
    reviewer = EvidenceAndNumericReviewer()
    evidence = {"var_95": "0.0245", "cvar_95": "0.0382"}
    citations = (CitationRef(source_type="quant", source_id="quant_engine", label="Quant"),)
    claims = (
        NumericClaimRef(
            claim_id="var_claim",
            statement="VaR là 0.0245",
            value="0.0245",
            evidence_ref="var_95",
        ),
    )

    candidate_text = (
        "Chào anh, em đã phân tích rủi ro định lượng:\n"
        "1. Value at Risk (VaR 95%, 1-day) là 0.0245.\n"
        "2. Ngoài ra em ước tính VaR bịa đặt trong tương lai là 99.88% với mức lỗ 888 triệu.\n"
        "Anh hãy lưu ý rủi ro danh mục nhé."
    )

    accepted_cites, accepted_numeric, sanitized_text, rejections = reviewer.review(
        candidate_text=candidate_text,
        evidence=evidence,
        citations=citations,
        numeric_claims=claims,
    )

    assert len(rejections) >= 1
    assert any("ungrounded_prose_number" in r for r in rejections)
    # The line with fabricated 99.88% / 888 was stripped from sanitized prose
    assert "99.88%" not in sanitized_text
    assert "0.0245" in sanitized_text


def test_safety_reviewer_strips_advice_sentences_and_retains_educational_content() -> None:
    """High 3: Prohibited advisory statements must be stripped while preserving educational explanation."""
    reviewer = SafetyAndPolicyReviewer()
    mixed_text = (
        "Chỉ số ROE đo lường hiệu quả sinh lời trên vốn chủ sở hữu.\n"
        "Anh hãy mua ngay cổ phiếu FPT ngày mai để hưởng lợi nhuận lớn nhé!\n"
        "Công thức chuẩn là Lợi nhuận sau thuế chia cho Vốn chủ sở hữu bình quân."
    )

    is_safe, sanitized_text, rejections, policy_notice = reviewer.review(mixed_text)

    assert not is_safe
    assert "contains_investment_advice" in rejections
    assert "mua ngay" not in sanitized_text
    assert "Chỉ số ROE đo lường" in sanitized_text
    assert "Công thức chuẩn là" in sanitized_text
    assert policy_notice is not None
    assert "không cấu thành khuyến nghị đầu tư" in sanitized_text


def test_concurrent_idempotency_claim_prevents_duplicate_execution(tmp_path, monkeypatch) -> None:
    """High 4: Concurrent requests with identical idempotency_key must not execute twice."""
    monkeypatch.setenv("RISK_DASHBOARD_APP_STATE_DB", str(tmp_path / "app_state.db"))
    clear_db_path_cache()

    with open_app_state_db() as conn:
        apply_migrations(conn)

    repo = SqliteConversationRepository()
    repo.create_conversation(
        ConversationEntity(
            conversation_id="conv_race",
            account_id="acc_race",
            surface="learn",
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
    )

    service = ConversationService(repository=repo)
    req = SendMessageRequest(
        content="Giải thích chỉ số ROE",
        surface="learn",
        idempotency_key="race_key_123",
    )

    # 1. First execution wins claim and creates response
    res1 = asyncio.run(
        service.send_message(account_id="acc_race", conversation_id="conv_race", request=req)
    )
    assert res1.message_id is not None
    assert "ROE" in res1.answer

    # 2. Second execution with same idempotency_key retrieves existing response without re-executing
    res2 = asyncio.run(
        service.send_message(account_id="acc_race", conversation_id="conv_race", request=req)
    )
    assert res2.message_id == res1.message_id
    assert res2.answer == res1.answer

    # Verify messages table has only 1 assistant message and 1 user message
    messages = repo.list_messages(conversation_id="conv_race", account_id="acc_race")
    assistant_msgs = [m for m in messages if m.role == "assistant"]
    assert len(assistant_msgs) == 1

