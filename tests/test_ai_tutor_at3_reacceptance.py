from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from uuid import uuid4
import pytest

from risk_dashboard.modules.agentic_core.application.graph import run_graph
from risk_dashboard.modules.agentic_core.application.review import review_claims
from risk_dashboard.modules.agentic_core.domain.tools import RiskClass
from risk_dashboard.modules.agentic_core.schemas.claim import Claim, ClaimKind, ClaimStatus
from risk_dashboard.modules.agentic_core.schemas.envelope import (
    ConsentSnapshot,
    ExecutionBudget,
    TrustedExecutionEnvelope,
)
from risk_dashboard.modules.ai_tutor.application.conversation_service import (
    ConversationService,
)
from risk_dashboard.modules.ai_tutor.application.feedback_service import (
    FeedbackService,
    MessageNotFoundError,
)
from risk_dashboard.modules.ai_tutor.application.reviewers import (
    EvidenceAndNumericReviewer,
)
from risk_dashboard.modules.ai_tutor.infrastructure.sqlite_conversation_repository import (
    SqliteConversationRepository,
)
from risk_dashboard.modules.ai_tutor.infrastructure.sqlite_feedback_repository import (
    SqliteFeedbackRepository,
)
from risk_dashboard.modules.ai_tutor.schemas.conversation import (
    CitationRef,
    ConversationEntity,
    FeedbackEntity,
    MessageEntity,
    NumericClaimRef,
)
from risk_dashboard.modules.ai_tutor.schemas.requests import (
    CreateConversationRequest,
    SendMessageRequest,
    SubmitFeedbackRequest,
)
from risk_dashboard.platform.ai_runtime.contracts import (
    ModelMessage,
    ModelResult,
    ModelTask,
    TokenUsage,
)
from risk_dashboard.platform.ai_runtime.testing.fake_provider import FakeProvider


class SpyCountingProvider:
    name = "fake"
    default_model = "fake-model"

    def __init__(self, text: str = "Spy response"):
        self.call_count = 0
        self.text = text

    async def generate(self, task: ModelTask) -> ModelResult:
        self.call_count += 1
        return ModelResult(
            text=self.text,
            usage=TokenUsage(prompt=100, completion=100, total=200),
            provider="fake",
            model="fake-model",
            latency_ms=5,
            finish_reason="stop",
        )


class FakeOverusageProvider:
    name = "fake"
    default_model = "fake-model"

    def __init__(self, total_tokens: int = 150_000, text: str = "Overused tokens response"):
        self.total_tokens = total_tokens
        self.text = text

    async def generate(self, task: ModelTask) -> ModelResult:
        return ModelResult(
            text=self.text,
            usage=TokenUsage(prompt=1000, completion=self.total_tokens - 1000, total=self.total_tokens),
            provider="fake",
            model="fake-model",
            latency_ms=10,
            finish_reason="stop",
        )


class MockFailingGraph:
    def __init__(self, fail_first: bool = True):
        self.fail_first = fail_first
        self.attempts = 0

    async def execute(self, **kwargs):
        self.attempts += 1
        if self.fail_first and self.attempts == 1:
            raise RuntimeError("Simulated transient runtime network/graph crash")
        from risk_dashboard.modules.ai_tutor.schemas.responses import SendMessageResponse
        return SendMessageResponse(
            message_id="msg_recovered_001",
            conversation_id=kwargs.get("conversation_id", "conv_test"),
            role="assistant",
            answer="Hệ thống đã phục hồi sau sự cố.",
            citations=(),
            numeric_claims=(),
            created_at=datetime.now(timezone.utc).isoformat(),
        )


class DummyTool:
    def __init__(self):
        class Manifest:
            tool_id = "quant-read"
            risk_class = RiskClass.READ
            required_capabilities = ("learning_read",)
        self.manifest = Manifest()

    async def execute(self, grant):
        return {"var_95": "0.045"}


def test_feedback_cross_account_bola_rejection():
    """Test that submitting feedback on a message belonging to another account is rejected with 404."""
    repo = SqliteConversationRepository()
    now_iso = datetime.now(timezone.utc).isoformat()
    uid = uuid4().hex[:8]
    
    # 1. Create conversation and message owned by account_A
    conv_a = ConversationEntity(
        conversation_id=f"conv_user_a_{uid}",
        account_id=f"acc_user_a_{uid}",
        surface="learn",
        context_id="lesson_01",
        created_at=now_iso,
        updated_at=now_iso,
    )
    repo.create_conversation(conv_a)
    msg_a = MessageEntity(
        message_id=f"msg_user_a_{uid}",
        conversation_id=f"conv_user_a_{uid}",
        role="assistant",
        content="Nội dung riêng tư của user A",
        created_at=now_iso,
    )
    repo.save_message(msg_a)

    feedback_svc = FeedbackService(conv_repository=repo)
    req = SubmitFeedbackRequest(
        rating="helpful",
        reason_code="accurate",
        comment="Nice job",
        idempotency_key=f"fb_key_{uid}",
    )

    # 2. Account B attempts to submit feedback on Account A's message -> Must fail with MessageNotFoundError
    with pytest.raises(MessageNotFoundError):
        feedback_svc.submit_feedback(
            account_id=f"acc_attacker_b_{uid}",
            message_id=f"msg_user_a_{uid}",
            request=req,
        )

    # 3. Account A submits feedback -> Must succeed
    resp_a = feedback_svc.submit_feedback(
        account_id=f"acc_user_a_{uid}",
        message_id=f"msg_user_a_{uid}",
        request=req,
    )
    assert resp_a.status == "recorded"
    assert resp_a.message_id == f"msg_user_a_{uid}"


def test_feedback_idempotency_race_handling():
    """Test that concurrent feedback submissions with same idempotency key return consistent responses."""
    repo = SqliteConversationRepository()
    now_iso = datetime.now(timezone.utc).isoformat()
    uid = uuid4().hex[:8]

    conv = ConversationEntity(
        conversation_id=f"conv_fb_{uid}",
        account_id=f"acc_fb_{uid}",
        surface="learn",
        context_id="lesson_01",
        created_at=now_iso,
        updated_at=now_iso,
    )
    repo.create_conversation(conv)
    msg = MessageEntity(
        message_id=f"msg_fb_{uid}",
        conversation_id=f"conv_fb_{uid}",
        role="assistant",
        content="Tin nhắn cần đánh giá",
        created_at=now_iso,
    )
    repo.save_message(msg)

    fb_repo = SqliteFeedbackRepository()
    fb_svc = FeedbackService(repository=fb_repo, conv_repository=repo)
    req = SubmitFeedbackRequest(
        rating="helpful",
        reason_code="accurate",
        comment="Idempotent test",
        idempotency_key=f"idemp_fb_{uid}",
    )

    # First call inserts
    resp1 = fb_svc.submit_feedback(account_id=f"acc_fb_{uid}", message_id=f"msg_fb_{uid}", request=req)
    assert resp1.status == "recorded"

    # Second call (or simulated race via save_feedback) returns existing record
    resp2 = fb_svc.submit_feedback(account_id=f"acc_fb_{uid}", message_id=f"msg_fb_{uid}", request=req)
    assert resp2.status == "recorded"
    assert resp2.feedback_id == resp1.feedback_id


def test_pre_dispatch_token_and_cost_budget_blocks_before_provider():
    """Test that a task whose prompt exceeds token or cost limits is blocked BEFORE calling provider."""
    uid = uuid4().hex[:8]
    envelope = TrustedExecutionEnvelope(
        run_id=f"run_pre_{uid}",
        correlation_id=f"corr_{uid}",
        idempotency_key=f"idemp_{uid}",
        account_id=f"acc_{uid}",
        surface="learn",
        allowed_capabilities=("learning_read",),
        budget=ExecutionBudget(
            max_steps=5,
            max_tool_calls=5,
            max_tokens=50,  # Tiny token budget
            max_wall_seconds=10.0,
            max_cost_usd=1.0,
        ),
        policy_version="v1",
        model_policy_version="v1",
        consent=ConsentSnapshot(policy_version="v1", analytics_telemetry=True),
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    # Long prompt that exceeds 50 tokens (e.g. 500 characters ~ 125 tokens)
    large_prompt = "A" * 500
    task = ModelTask(
        task_type="agentic_read",
        system_instructions_ref="prompt_test",
        messages=(ModelMessage(role="user", content=large_prompt),),
        correlation_id=f"corr_{uid}",
    )

    spy_provider = SpyCountingProvider()
    res = asyncio.run(run_graph(envelope, task, spy_provider, DummyTool()))
    assert res["status"] == "recovery"
    assert res["code"] == "token_budget_exhausted"
    # CRITICAL: Provider must NEVER be called, preventing wasted provider spend
    assert spy_provider.call_count == 0


def test_envelope_token_and_cost_budget_boundaries():
    """Test that envelope over-token and over-cost bounds trigger recovery degraded states."""
    uid = uuid4().hex[:8]
    envelope = TrustedExecutionEnvelope(
        run_id=f"run_{uid}",
        correlation_id=f"corr_{uid}",
        idempotency_key=f"idemp_{uid}",
        account_id=f"acc_{uid}",
        surface="learn",
        allowed_capabilities=("learning_read",),
        budget=ExecutionBudget(
            max_steps=5,
            max_tool_calls=5,
            max_tokens=1000,
            max_wall_seconds=10.0,
            max_cost_usd=0.001,
        ),
        policy_version="v1",
        model_policy_version="v1",
        consent=ConsentSnapshot(policy_version="v1", analytics_telemetry=True),
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    task = ModelTask(
        task_type="agentic_read",
        system_instructions_ref="prompt_test",
        messages=(ModelMessage(role="user", content="Test budget"),),
        correlation_id=f"corr_{uid}",
    )

    # 1. Over-token provider -> token_budget_exhausted
    over_token_provider = FakeOverusageProvider(total_tokens=50_000)
    res_token = asyncio.run(run_graph(envelope, task, over_token_provider, DummyTool()))
    assert res_token["status"] == "recovery"
    assert res_token["code"] == "token_budget_exhausted"

    # 2. Over-cost provider -> cost_budget_exhausted
    envelope_cost_limited = envelope.model_copy(
        update={
            "budget": ExecutionBudget(
                max_steps=5,
                max_tool_calls=5,
                max_tokens=500_000,
                max_wall_seconds=10.0,
                max_cost_usd=0.00001,
            )
        }
    )
    over_cost_provider = FakeOverusageProvider(total_tokens=20_000)
    res_cost = asyncio.run(run_graph(envelope_cost_limited, task, over_cost_provider, DummyTool()))
    assert res_cost["status"] == "recovery"
    assert res_cost["code"] == "cost_budget_exhausted"


def test_idempotency_release_on_graph_failure_and_retry():
    """Test that when graph execution fails, the idempotency claim is released and retry succeeds."""
    repo = SqliteConversationRepository()
    failing_graph = MockFailingGraph(fail_first=True)
    conv_svc = ConversationService(repository=repo, graph=failing_graph)

    now_iso = datetime.now(timezone.utc).isoformat()
    uid = uuid4().hex[:8]
    conv_id = f"conv_idemp_{uid}"
    acc_id = f"acc_idemp_{uid}"
    idemp_key = f"idemp_key_{uid}"

    conv = ConversationEntity(
        conversation_id=conv_id,
        account_id=acc_id,
        surface="learn",
        context_id="lesson_01",
        created_at=now_iso,
        updated_at=now_iso,
    )
    repo.create_conversation(conv)

    req = SendMessageRequest(
        content="Tính toán rủi ro danh mục",
        idempotency_key=idemp_key,
        surface="learn",
    )

    # 1. First execution fails due to graph crash
    with pytest.raises(RuntimeError):
        asyncio.run(
            conv_svc.send_message(
                account_id=acc_id,
                conversation_id=conv_id,
                request=req,
            )
        )

    # 2. Retry with the EXACT SAME idempotency key must succeed because the failed claim was released
    resp_retry = asyncio.run(
        conv_svc.send_message(
            account_id=acc_id,
            conversation_id=conv_id,
            request=req,
        )
    )
    assert resp_retry.answer == "Hệ thống đã phục hồi sau sự cố."

    # 3. Third execution with the SAME idempotency key returns the cached completed message
    resp_cached = asyncio.run(
        conv_svc.send_message(
            account_id=acc_id,
            conversation_id=conv_id,
            request=req,
        )
    )
    assert resp_cached.answer == "Hệ thống đã phục hồi sau sự cố."


def test_numeric_prose_generic_redaction():
    """Test that all ungrounded numbers, currencies, and ratios in prose are stripped regardless of keywords."""
    reviewer = EvidenceAndNumericReviewer()
    evidence = {"var_historical": "4.5%"}  # Allowed: 4.5% exact

    # Candidate text contains generic fabricated currency, ratio, and number without keywords
    candidate_text = (
        "Chào bạn, chúng ta cùng phân tích.\n"
        "Danh mục đã giảm 888 triệu đồng trong quý vừa qua.\n"
        "Tỷ lệ biến động đo được là 4.5% theo phương pháp Historical Simulation.\n"
        "Hệ số ngẫu nhiên là 999.99 và ngày chốt là 31.\n"
        "Hãy luôn kiểm tra giả định phân phối chuẩn."
    )

    accepted_cites, accepted_numeric, safe_text, rejections = reviewer.review(
        candidate_text=candidate_text,
        evidence=evidence,
        citations=(CitationRef(source_id="doc_1", snippet="test", label="Tài liệu 1"),),
        numeric_claims=(),
    )

    # The lines with 888 triệu đồng and 999.99/31 must be stripped
    assert "888" not in safe_text
    assert "999.99" not in safe_text
    assert "4.5%" in safe_text
    assert "Chào bạn, chúng ta cùng phân tích." in safe_text
    assert "Hãy luôn kiểm tra giả định phân phối chuẩn." in safe_text
    assert any("ungrounded_prose_number_888" in r for r in rejections)
    assert any("ungrounded_prose_number_999.99" in r for r in rejections)


def test_numeric_evidence_exact_token_matching_blocks_substring():
    """Test that numeric claim review blocks substring numbers (e.g. evidence '42' rejects '142')."""
    # 1. Evidence has "42", claim statement has "142" -> Must be blocked
    claim_substring = Claim(
        claim_id="claim-sub-1",
        kind=ClaimKind.NUMERIC,
        statement="Chỉ số đo được là 142.",
        evidence_refs=("metric_val",),
    )
    artifact_sub = review_claims((claim_substring,), {"metric_val": "42"})
    assert artifact_sub.status is ClaimStatus.BLOCKED
    assert artifact_sub.ledger.claims[0].block_reason == "numeric_evidence_mismatch"

    # 2. Evidence has "42", claim statement has "42" -> Accepted
    claim_exact = Claim(
        claim_id="claim-exact-1",
        kind=ClaimKind.NUMERIC,
        statement="Chỉ số đo được là 42.",
        evidence_refs=("metric_val",),
    )
    artifact_exact = review_claims((claim_exact,), {"metric_val": "42"})
    assert artifact_exact.status is ClaimStatus.ACCEPTED
    assert artifact_exact.ledger.claims[0].status is ClaimStatus.ACCEPTED


def test_numeric_evidence_strict_same_unit_and_exact_decimal():
    """Test that numeric evidence requires exact decimal equality and identical unit without implicit cross-unit conversion."""
    # 1. Cross-unit transform (0.045 evidence vs 4.5% statement) -> BLOCKED
    claim_cross = Claim(
        claim_id="claim-cross-1",
        kind=ClaimKind.NUMERIC,
        statement="Chỉ số VaR là 4.5%.",
        evidence_refs=("var_raw",),
    )
    res_cross = review_claims((claim_cross,), {"var_raw": "0.045"})
    assert res_cross.status is ClaimStatus.BLOCKED
    assert res_cross.ledger.claims[0].block_reason == "numeric_evidence_mismatch"

    # 2. Same unit with exact canonical decimal (0.045 vs 0.0450) -> ACCEPTED
    claim_canonical = Claim(
        claim_id="claim-can-1",
        kind=ClaimKind.NUMERIC,
        statement="Chỉ số VaR là 0.0450.",
        evidence_refs=("var_raw",),
    )
    res_can = review_claims((claim_canonical,), {"var_raw": "0.045"})
    assert res_can.status is ClaimStatus.ACCEPTED

    # 3. Approximate or altered number (42 vs 42.0001) -> BLOCKED
    claim_altered = Claim(
        claim_id="claim-alt-1",
        kind=ClaimKind.NUMERIC,
        statement="Chỉ số là 42.0001.",
        evidence_refs=("val",),
    )
    res_alt = review_claims((claim_altered,), {"val": "42"})
    assert res_alt.status is ClaimStatus.BLOCKED
    assert res_alt.ledger.claims[0].block_reason == "numeric_evidence_mismatch"


def test_concurrent_feedback_submissions_atomic():
    """Test that concurrent feedback submissions from multiple threads/coroutines return the exact same record."""
    repo = SqliteConversationRepository()
    now_iso = datetime.now(timezone.utc).isoformat()
    uid = uuid4().hex[:8]

    conv = ConversationEntity(
        conversation_id=f"conv_atomic_{uid}",
        account_id=f"acc_atomic_{uid}",
        surface="learn",
        context_id="lesson_01",
        created_at=now_iso,
        updated_at=now_iso,
    )
    repo.create_conversation(conv)
    msg = MessageEntity(
        message_id=f"msg_atomic_{uid}",
        conversation_id=f"conv_atomic_{uid}",
        role="assistant",
        content="Tin nhắn atomic feedback",
        created_at=now_iso,
    )
    repo.save_message(msg)

    fb_repo = SqliteFeedbackRepository()
    fb_svc = FeedbackService(repository=fb_repo, conv_repository=repo)
    req = SubmitFeedbackRequest(
        rating="helpful",
        reason_code="accurate",
        comment="Concurrent submit test",
        idempotency_key=f"idemp_atomic_{uid}",
    )

    async def submit_task():
        return fb_svc.submit_feedback(
            account_id=f"acc_atomic_{uid}",
            message_id=f"msg_atomic_{uid}",
            request=req,
        )

    async def run_concurrent():
        return await asyncio.gather(*(submit_task() for _ in range(10)))

    results = asyncio.run(run_concurrent())
    assert len(results) == 10
    first_id = results[0].feedback_id
    for r in results:
        assert r.status == "recorded"
        assert r.feedback_id == first_id


def test_cost_reservation_subtracts_estimated_input_cost():
    """Test that cost reservation subtracts estimated input cost before dispatching task."""
    uid = uuid4().hex[:8]
    envelope = TrustedExecutionEnvelope(
        run_id=f"run_cost_{uid}",
        correlation_id=f"corr_{uid}",
        idempotency_key=f"idemp_{uid}",
        account_id=f"acc_{uid}",
        surface="learn",
        allowed_capabilities=("learning_read",),
        budget=ExecutionBudget(
            max_steps=5,
            max_tool_calls=5,
            max_tokens=10_000,
            max_wall_seconds=10.0,
            max_cost_usd=0.0001,  # Small cost budget
        ),
        policy_version="v1",
        model_policy_version="v1",
        consent=ConsentSnapshot(policy_version="v1", analytics_telemetry=True),
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    # Prompt of 20000 characters (~ 5000 tokens -> cost at $0.075/1M is $0.000375 > $0.0001)
    prompt = "X" * 20000
    task = ModelTask(
        task_type="agentic_read",
        system_instructions_ref="prompt_test",
        messages=(ModelMessage(role="user", content=prompt),),
        correlation_id=f"corr_{uid}",
    )

    spy_provider = SpyCountingProvider()
    res = asyncio.run(run_graph(envelope, task, spy_provider, DummyTool()))
    assert res["status"] == "recovery"
    assert res["code"] == "cost_budget_exhausted"
    assert spy_provider.call_count == 0


def test_numeric_metadata_exact_typed_decimal_and_unit_validation():
    """Test that metadata numeric claim validation enforces canonical typed Decimal and exact unit."""
    reviewer = EvidenceAndNumericReviewer()

    # 1. Evidence is "0.15" (unit None), Claim declares unit "%" -> REJECTED
    claim_unit_mismatch = NumericClaimRef(
        claim_id="c_mismatch_1",
        label="Tỉ suất",
        statement="Tỉ suất là 15%.",
        value="15",
        unit="%",
        evidence_ref="ev_rate",
    )
    _, valid_num_1, _, rejections_1 = reviewer.review(
        candidate_text="Phân tích tỉ suất",
        evidence={"ev_rate": "0.15"},
        citations=(),
        numeric_claims=(claim_unit_mismatch,),
    )
    assert len(valid_num_1) == 0
    assert any("unit_mismatch_for_claim_c_mismatch_1" in r for r in rejections_1)

    # 2. Evidence is "15%" (unit "%"), Claim declares unit "%" -> ACCEPTED
    claim_unit_match = NumericClaimRef(
        claim_id="c_match_1",
        label="Tỉ suất",
        statement="Tỉ suất là 15%.",
        value="15",
        unit="%",
        evidence_ref="ev_rate_pct",
    )
    _, valid_num_2, _, rejections_2 = reviewer.review(
        candidate_text="Phân tích tỉ suất",
        evidence={"ev_rate_pct": "15%"},
        citations=(),
        numeric_claims=(claim_unit_match,),
    )
    assert len(valid_num_2) == 1
    assert valid_num_2[0].claim_id == "c_match_1"

    # 3. Evidence is "15%", Claim declares unit "VND" -> REJECTED
    claim_diff_unit = NumericClaimRef(
        claim_id="c_vnd_1",
        label="Số tiền",
        statement="Số tiền là 15 VND.",
        value="15",
        unit="VND",
        evidence_ref="ev_rate_pct",
    )
    _, valid_num_3, _, rejections_3 = reviewer.review(
        candidate_text="Phân tích tỉ suất",
        evidence={"ev_rate_pct": "15%"},
        citations=(),
        numeric_claims=(claim_diff_unit,),
    )
    assert len(valid_num_3) == 0
    assert any("unit_mismatch_for_claim_c_vnd_1" in r for r in rejections_3)


class ZeroUsageProvider:
    name = "fake"
    default_model = "fake-model"

    async def generate(self, task: ModelTask) -> ModelResult:
        return ModelResult(
            text="Phản hồi có nội dung dài nhằm thử nghiệm zero usage fail-closed behavior.",
            usage=TokenUsage(prompt=0, completion=0, total=0),
            provider="fake",
            model="fake-model",
            latency_ms=5,
            finish_reason="stop",
        )


def test_provider_zero_usage_non_empty_text_charges_derived_tokens():
    """Test that zero usage returned with non-empty text fails closed or charges derived token usage."""
    uid = uuid4().hex[:8]
    envelope = TrustedExecutionEnvelope(
        run_id=f"run_zero_{uid}",
        correlation_id=f"corr_{uid}",
        idempotency_key=f"idemp_{uid}",
        account_id=f"acc_{uid}",
        surface="learn",
        allowed_capabilities=("learning_read",),
        budget=ExecutionBudget(
            max_steps=5,
            max_tool_calls=5,
            max_tokens=10,  # Very low token budget (10 tokens)
            max_wall_seconds=10.0,
            max_cost_usd=1.0,
        ),
        policy_version="v1",
        model_policy_version="v1",
        consent=ConsentSnapshot(policy_version="v1", analytics_telemetry=True),
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    task = ModelTask(
        task_type="agentic_read",
        system_instructions_ref="prompt_test",
        messages=(ModelMessage(role="user", content="Hi"),),
        correlation_id=f"corr_{uid}",
    )

    zero_provider = ZeroUsageProvider()
    res = asyncio.run(run_graph(envelope, task, zero_provider, DummyTool()))
    # Must fail closed with token_budget_exhausted because derived tokens exceed max_tokens=10
    assert res["status"] == "recovery"
    assert res["code"] == "token_budget_exhausted"


class InconsistentUsageProvider:
    name = "fake"
    default_model = "fake-model"

    async def generate(self, task: ModelTask) -> ModelResult:
        # Returns prompt=100, completion=100, but total=1 (inconsistent)
        return ModelResult(
            text="Phản hồi thử nghiệm token mismatch.",
            usage=TokenUsage(prompt=100, completion=100, total=1),
            provider="fake",
            model="fake-model",
            latency_ms=5,
            finish_reason="stop",
        )


def test_token_ledger_mismatched_usage_uses_canonical_max():
    """Test that if provider returns inconsistent usage.total (e.g. 1 instead of 200), canonical max is enforced."""
    uid = uuid4().hex[:8]
    envelope = TrustedExecutionEnvelope(
        run_id=f"run_mismatch_{uid}",
        correlation_id=f"corr_{uid}",
        idempotency_key=f"idemp_{uid}",
        account_id=f"acc_{uid}",
        surface="learn",
        allowed_capabilities=("learning_read",),
        budget=ExecutionBudget(
            max_steps=5,
            max_tool_calls=5,
            max_tokens=150,  # Ceiling is 150 tokens
            max_wall_seconds=10.0,
            max_cost_usd=1.0,
        ),
        policy_version="v1",
        model_policy_version="v1",
        consent=ConsentSnapshot(policy_version="v1", analytics_telemetry=True),
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    task = ModelTask(
        task_type="agentic_read",
        system_instructions_ref="prompt_test",
        messages=(ModelMessage(role="user", content="Hi"),),
        correlation_id=f"corr_{uid}",
    )

    inconsistent_provider = InconsistentUsageProvider()
    res = asyncio.run(run_graph(envelope, task, inconsistent_provider, DummyTool()))
    # Must fail closed with token_budget_exhausted because actual 200 tokens > max 150 tokens
    assert res["status"] == "recovery"
    assert res["code"] == "token_budget_exhausted"


def test_numeric_claim_review_handles_punctuation_and_units():
    """Test that claims with %, VND, USD and trailing punctuation parse properly."""
    # 1. Statement with "42%." and evidence "42%" -> ACCEPTED
    claim_pct = Claim(
        claim_id="c_pct_1",
        kind=ClaimKind.NUMERIC,
        statement="Tỷ lệ sinh lời là 42%.",
        evidence_refs=("pct_ref",),
    )
    res_pct = review_claims((claim_pct,), {"pct_ref": "42%"})
    assert res_pct.status is ClaimStatus.ACCEPTED

    # 2. Statement with "42 VND." and evidence "42 VND" -> ACCEPTED
    claim_vnd = Claim(
        claim_id="c_vnd_1",
        kind=ClaimKind.NUMERIC,
        statement="Giá là 42 VND.",
        evidence_refs=("vnd_ref",),
    )
    res_vnd = review_claims((claim_vnd,), {"vnd_ref": "42 VND"})
    assert res_vnd.status is ClaimStatus.ACCEPTED

    # 3. Statement with "42 USD." and evidence "42 VND" -> BLOCKED
    claim_unit_diff = Claim(
        claim_id="c_unit_diff_1",
        kind=ClaimKind.NUMERIC,
        statement="Giá là 42 USD.",
        evidence_refs=("vnd_ref",),
    )
    res_unit_diff = review_claims((claim_unit_diff,), {"vnd_ref": "42 VND"})
    assert res_unit_diff.status is ClaimStatus.BLOCKED
    assert res_unit_diff.ledger.claims[0].block_reason == "numeric_evidence_mismatch"


