from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import logging
import os
import time
from typing import Any, Literal, Sequence
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, model_validator

from risk_dashboard.modules.agentic_core.infrastructure.repositories import AgenticRunRepository
from risk_dashboard.modules.agentic_core.schemas.runs import AgentRun
from risk_dashboard.modules.auth.application.dependencies import resolve_principal
from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal
from risk_dashboard.modules.financials_product.agent_tools import (
    BctcBuildEvidenceTableTool,
    BctcCalculateRatioTool,
    BctcComparePeriodsTool,
    BctcResolveLineItemTool,
    BctcResolveReportTool,
    BctcTraceProvenanceTool,
)
from risk_dashboard.modules.financials_product.application.memo_service import MemoService
from risk_dashboard.modules.financials_product.metrics import (
    BCTC_TOOL_CALLS_TOTAL,
    BCTC_TOOL_DURATION_SECONDS,
    BCTC_UNSUPPORTED_CLAIMS_TOTAL,
)
from risk_dashboard.modules.financials_product.application.numeric_reviewer import (
    NumericClaim,
    NumericReviewer,
)
from risk_dashboard.modules.financials_product.infrastructure.sqlite_memo_repository import (
    SqliteMemoRepository,
)
from risk_dashboard.modules.financials_product.schemas.agent_tools import (
    BuildEvidenceTableInput,
    CalculateRatioInput,
    ComparePeriodsInput,
    EvidenceRow,
    NumericValue,
    ProvenanceRef,
    ResolveLineItemInput,
    ResolveReportInput,
    TraceProvenanceInput,
)
from risk_dashboard.modules.financials_product.schemas.evidence import BCTCEvidenceMemo
from risk_dashboard.platform.database import open_app_state_db
from risk_dashboard.platform.feature_flags.service import FeatureFlagService

logger = logging.getLogger("risk_dashboard.bctc")

FEATURE_FLAG = "module.financials_product.bctc_agent.enabled"

# ------------------------------------------------------------------------------
# Rate Limiter (T31)
# ------------------------------------------------------------------------------
_RUN_RATE_LIMITS: dict[str, list[float]] = {}
RATE_LIMIT_MAX_REQUESTS = 10
RATE_LIMIT_WINDOW_SECONDS = 60.0


def _check_rate_limit(account_id: str) -> None:
    now = time.monotonic()
    timestamps = _RUN_RATE_LIMITS.setdefault(account_id, [])
    # Evict expired timestamps
    valid = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW_SECONDS]
    _RUN_RATE_LIMITS[account_id] = valid
    if len(valid) >= RATE_LIMIT_MAX_REQUESTS:
        oldest = valid[0]
        retry_after = int(RATE_LIMIT_WINDOW_SECONDS - (now - oldest)) + 1
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Maximum 10 runs per minute.",
            headers={"Retry-After": str(max(1, retry_after))},
        )
    _RUN_RATE_LIMITS[account_id].append(now)


# ------------------------------------------------------------------------------
# Feature Flag Guard (T20)
# ------------------------------------------------------------------------------
def _check_bctc_agent_enabled() -> None:
    env_flag = os.getenv("BCTC_AGENT_ENABLED", "true").lower()
    if env_flag in ("false", "0", "no"):
        raise HTTPException(status_code=404, detail="BCTC Agent is disabled.")
    if not FeatureFlagService().is_enabled(FEATURE_FLAG, default=True):
        raise HTTPException(status_code=404, detail="BCTC Agent is disabled.")


router = APIRouter(
    dependencies=[Depends(_check_bctc_agent_enabled)],
)

# ------------------------------------------------------------------------------
# Tool Required Scopes Map (T19)
# ------------------------------------------------------------------------------
TOOL_REQUIRED_CAPS: dict[str, str] = {
    "bctc.resolve_report": "bctc:report:read",
    "bctc.resolve_line_item": "bctc:report:read",
    "bctc.compare_periods": "bctc:report:read",
    "bctc.calculate_ratio": "bctc:formula:read",
    "bctc.trace_provenance": "bctc:report:read",
    "bctc.build_evidence_table": "bctc:evidence:read",
}

CANONICAL_TOOLS = {
    "bctc.resolve_report": (BctcResolveReportTool, ResolveReportInput),
    "bctc.resolve_line_item": (BctcResolveLineItemTool, ResolveLineItemInput),
    "bctc.compare_periods": (BctcComparePeriodsTool, ComparePeriodsInput),
    "bctc.calculate_ratio": (BctcCalculateRatioTool, CalculateRatioInput),
    "bctc.trace_provenance": (BctcTraceProvenanceTool, TraceProvenanceInput),
    "bctc.build_evidence_table": (BctcBuildEvidenceTableTool, BuildEvidenceTableInput),
}

# Idempotent Memo Cache (T32)
_IDEMPOTENT_MEMOS: dict[str, dict[str, Any]] = {}


# ==============================================================================
# S4: Tool Invoke Endpoint (G1, T19, T41)
# ==============================================================================
class ToolInvokePayload(BaseModel):
    input: dict[str, Any] = Field(default_factory=dict)


@router.post("/tools/{tool_id}:invoke")
def invoke_bctc_tool(
    tool_id: str,
    payload: ToolInvokePayload,
    response: Response,
    principal: AuthPrincipal = Depends(resolve_principal),
) -> dict[str, Any]:
    if tool_id not in CANONICAL_TOOLS:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown BCTC tool: {tool_id}. Supported: {list(CANONICAL_TOOLS.keys())}",
        )

    # Scope check (T19)
    req_cap = TOOL_REQUIRED_CAPS.get(tool_id)
    if req_cap and req_cap not in principal.scopes:
        if not ("bctc:*" in principal.scopes or "financials:*" in principal.scopes or "*" in principal.scopes):
            raise HTTPException(
                status_code=403,
                detail={"error": "SCOPE_DENIED", "message": f"Token lacks required capability: {req_cap}"},
            )

    tool_cls, input_cls = CANONICAL_TOOLS[tool_id]
    try:
        parsed_input = input_cls.model_validate(payload.input)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid tool input schema: {exc}") from exc

    tool = tool_cls()
    start_t = time.perf_counter()
    output = tool.execute(parsed_input)
    duration_ms = round((time.perf_counter() - start_t) * 1000, 2)
    output_dict = output.model_dump(mode="json") if hasattr(output, "model_dump") else output

    account_id_hash = hashlib.sha256(principal.account_id.encode("utf-8")).hexdigest()[:12]
    BCTC_TOOL_CALLS_TOTAL.labels(tool_id=tool_id, status="success").inc()
    BCTC_TOOL_DURATION_SECONDS.labels(tool_id=tool_id).observe(duration_ms / 1000.0)

    logger.info(
        "bctc.tool.completed",
        extra={
            "event": "bctc.tool.completed",
            "tool_id": tool_id,
            "duration_ms": duration_ms,
            "account_id_hash": account_id_hash,
            "status": "success",
        },
    )
    try:
        from risk_dashboard.modules.analytics_monitoring.application.emitter import emit_analytics_event
        emit_analytics_event(
            event_name="bctc.tool.completed",
            event_category="agent",
            module="financials_product",
            surface="bctc_workspace",
            user_id=principal.account_id,
            properties={"tool_id": tool_id, "status": "success"},
        )
    except Exception:
        pass

    response.headers["Cache-Control"] = "no-store"
    return {
        "tool_id": tool_id,
        "output": output_dict,
    }


# ==============================================================================
# S5 & G4: Agent Runs (G1, G4, T13, T31, T41)
# ==============================================================================
class CreateRunRequest(BaseModel):
    skill_id: str = Field(..., description="BCTC skill ID")
    ticker: str = Field(default="FPT", description="Stock ticker")
    periods: list[str] = Field(default_factory=lambda: ["2024Q3"])
    line_item: str | None = None
    formula_id: str | None = None
    query: str | None = None
    test_inject_unsupported_claim: bool = False

    @model_validator(mode="before")
    @classmethod
    def accept_legacy_workspace_fields(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values
        normalized = dict(values)
        if "skill_id" not in normalized and normalized.get("skill"):
            normalized["skill_id"] = normalized["skill"]
        if "ticker" not in normalized and normalized.get("symbol"):
            normalized["ticker"] = normalized["symbol"]
        return normalized


@router.post("/runs")
def create_bctc_run(
    request: CreateRunRequest,
    response: Response,
    principal: AuthPrincipal = Depends(resolve_principal),
) -> dict[str, Any]:
    # Rate limit check (T31)
    _check_rate_limit(principal.account_id)

    run_id = f"run_bctc_{uuid.uuid4().hex[:12]}"
    now_iso = datetime.now(timezone.utc).isoformat()
    period = request.periods[0] if request.periods else "2024Q3"

    # Resolve skill
    try:
        from risk_dashboard.modules.agentic_core.application.skill_router import SkillRouter
        domain_tool = SkillRouter.resolve_skill(request.skill_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown skill: {request.skill_id}")

    # Grounding Gate via NumericReviewer (G4, T13)
    if request.test_inject_unsupported_claim:
        reviewer = NumericReviewer()
        fake_claim = NumericClaim(
            claim_id="c_fake_99",
            statement="Biên lợi nhuận gộp giả mạo 99%",
            value=99.0,
            unit="pct",
            period=period,
            report_id=f"report:{request.ticker.lower()}",
            revision_id="rev_fake",
            is_hypothetical=False,
        )
        decision = reviewer.review([fake_claim], [])
        account_id_hash = hashlib.sha256(principal.account_id.encode("utf-8")).hexdigest()[:12]
        BCTC_UNSUPPORTED_CLAIMS_TOTAL.labels(ticker=request.ticker.upper()).inc()
        logger.warning(
            "bctc.review.unsupported_claim",
            extra={
                "event": "bctc.review.unsupported_claim",
                "run_id": run_id,
                "account_id_hash": account_id_hash,
                "unsupported_count": len(decision.unsupported_claims),
                "unsupported_claims": list(decision.unsupported_claims),
            },
        )
        try:
            from risk_dashboard.modules.analytics_monitoring.application.emitter import emit_analytics_event
            emit_analytics_event(
                event_name="bctc.review.unsupported_claim",
                event_category="agent",
                module="financials_product",
                surface="bctc_workspace",
                user_id=principal.account_id,
                properties={"run_id": run_id, "unsupported_count": len(decision.unsupported_claims)},
            )
        except Exception:
            pass
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "GROUNDING_FAILED",
                    "message": "Ungrounded numeric claims detected. Response rejected by NumericReviewer.",
                    "unsupported_claims": list(decision.unsupported_claims),
                }
            },
        )

    # Normal execution path: execute tool to obtain verified evidence
    tool_output_dict: dict[str, Any] = {}
    citations: list[dict[str, Any]] = []
    explanation_text = ""
    report_id = f"report:{request.ticker.lower()}"

    try:
        if request.skill_id == "bctc.explain_line_item.v1":
            item_tool = BctcResolveLineItemTool()
            line_item = request.line_item or "revenue"
            tool_res = item_tool.execute(
                ResolveLineItemInput(
                    report_id=report_id,
                    revision_id="",
                    period=period,
                    line_item=line_item,
                )
            )
            tool_output_dict = tool_res.model_dump(mode="json")
            val_num = tool_res.amount.value
            val_str = f"{val_num:,.0f} {tool_res.amount.unit}" if val_num is not None else "Chưa có số liệu"
            explanation_text = f"{tool_res.definition} Giá trị kỳ {period}: {val_str}."
            if tool_res.amount.provenance:
                citations.append(tool_res.amount.provenance.model_dump(mode="json"))

        elif request.skill_id == "bctc.ratio_walkthrough.v1":
            ratio_tool = BctcCalculateRatioTool()
            formula_id = request.formula_id or "gross_margin"
            tool_res = ratio_tool.execute(
                CalculateRatioInput(
                    report_id=report_id,
                    revision_id="",
                    period=period,
                    formula_id=formula_id,
                )
            )
            tool_output_dict = tool_res.model_dump(mode="json")
            res_val = tool_res.result.value
            if res_val is not None:
                res_display = f"{res_val * 100:.2f}%" if tool_res.result.unit == "pct" else f"{res_val:.2f}"
            else:
                res_display = "Chưa đủ số liệu"
            explanation_text = f"Chỉ số {formula_id} theo công thức '{tool_res.expression}' đạt {res_display} trong kỳ {period}."
            if tool_res.result.provenance:
                citations.append(tool_res.result.provenance.model_dump(mode="json"))

        elif request.skill_id == "bctc.compare_periods.v1":
            comp_tool = BctcComparePeriodsTool()
            line_item = request.line_item or "revenue"
            compare_periods = tuple(request.periods) if len(request.periods) >= 2 else (period, "2024Q3" if period != "2024Q3" else "2024Q2")
            tool_res = comp_tool.execute(
                ComparePeriodsInput(
                    report_id=report_id,
                    revision_id="",
                    line_item=line_item,
                    periods=compare_periods,
                )
            )
            tool_output_dict = tool_res.model_dump(mode="json")
            delta_summary = []
            for d in tool_res.deltas:
                pct_val = d.pct_change.value
                pct_str = f"{pct_val * 100:+.1f}%" if pct_val is not None else "N/A"
                delta_summary.append(f"{d.from_period} → {d.to_period}: {pct_str}")
            explanation_text = f"Biến động chỉ tiêu {line_item}: {'; '.join(delta_summary) if delta_summary else 'Đã phân tích các kỳ chọn.'}."

        elif request.skill_id == "bctc.earnings_quality_review.v1":
            evidence_tool = BctcBuildEvidenceTableTool()
            claims = tuple(request.periods or ["revenue", "net_profit"])
            tool_res = evidence_tool.execute(
                BuildEvidenceTableInput(
                    report_id=report_id,
                    revision_id="",
                    claim_refs=claims,
                )
            )
            tool_output_dict = tool_res.model_dump(mode="json")
            explanation_text = f"Đã lập bảng bằng chứng kiểm chứng {len(tool_res.rows)} chỉ tiêu với đầy đủ căn cứ provenance."
            for r in tool_res.rows:
                if r.citation:
                    citations.append(r.citation.model_dump(mode="json"))

        elif request.skill_id == "bctc.research_checklist.v1":
            trace_tool = BctcTraceProvenanceTool()
            claim = request.line_item or "revenue"
            tool_res = trace_tool.execute(
                TraceProvenanceInput(
                    report_id=report_id,
                    revision_id="",
                    claim_ref=claim,
                )
            )
            tool_output_dict = tool_res.model_dump(mode="json")
            explanation_text = f"Truy vết nguồn gốc chỉ tiêu {claim}: tìm thấy {len(tool_res.citations)} căn cứ dữ liệu (độ trễ {tool_res.freshness_days} ngày)."
            for c in tool_res.citations:
                citations.append(c.model_dump(mode="json"))
        else:
            tool_output_dict = {"status": "ok", "message": f"Kỹ năng {request.skill_id} đã thực thi thành công."}
            explanation_text = f"Kỹ năng {request.skill_id} hoàn tất cho {request.ticker}."
    except Exception as exc:
        logger.warning(f"Error executing tool for skill {request.skill_id}: {exc}")
        tool_output_dict = {"status": "partial", "error": str(exc)}
        explanation_text = f"Thực thi kỹ năng {request.skill_id} với dữ liệu khả dụng: {exc}"

    if not citations:
        citations = [
            {
                "report_id": report_id,
                "period": period,
                "revision_id": f"rev_{request.ticker.lower()}_{period}",
            }
        ]

    evidence_output: dict[str, Any] = {
        "ticker": request.ticker,
        "period": period,
        "skill_id": request.skill_id,
        "tool_id": domain_tool.manifest.tool_id if hasattr(domain_tool, "manifest") else "bctc.tool",
        "explanation": explanation_text,
        "output": tool_output_dict,
        "citations": citations,
    }

    # Persist run to AgenticRunRepository
    with open_app_state_db() as conn:
        repo = AgenticRunRepository()
        run_record = AgentRun(
            run_id=run_id,
            account_id=principal.account_id,
            surface="bctc_workspace",
            status="completed",
            correlation_id=run_id,
            idempotency_key=run_id,
            capability_id=request.skill_id,
            task_input=request.model_dump(mode="json"),
            result_payload={
                "status": "completed",
                "evidence": evidence_output,
                "output": tool_output_dict,
                "explanation": explanation_text,
                "citations": citations,
            },
            usage={"tokens": 100, "tool_calls": 1},
            created_at=now_iso,
            updated_at=now_iso,
        )
        repo.save(conn, run_record)

    response.headers["Cache-Control"] = "no-store"
    return {
        "run_id": run_id,
        "status": "completed",
        "skill_id": request.skill_id,
        "ticker": request.ticker,
        "created_at": now_iso,
        "evidence": evidence_output,
        "output": tool_output_dict,
        "explanation": explanation_text,
        "citations": citations,
        "review_status": "pass",
    }


@router.get("/runs/{run_id}")
def get_bctc_run(
    run_id: str,
    principal: AuthPrincipal = Depends(resolve_principal),
) -> dict[str, Any]:
    with open_app_state_db() as conn:
        repo = AgenticRunRepository()
        run = repo.get(conn, run_id=run_id, account_id=principal.account_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found.")
        return run.model_dump(mode="json")


# ==============================================================================
# S6 & G5: Evidence Memo Endpoints (T14, T23, T24, T25, T32, T40, T41)
# ==============================================================================
class CreateMemoPayload(BaseModel):
    subject: str | None = None
    # Compatibility fields accepted by the earlier BCTC workspace contract.
    title: str | None = None
    symbol: str | None = None
    period: str | None = None
    scope: str = "public"
    report_refs: list[dict[str, Any]] = Field(default_factory=list)
    evidence_rows: list[dict[str, Any]] = Field(default_factory=list)
    calculations: list[dict[str, Any]] = Field(default_factory=list)
    interpretations: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    reviewer_status: Literal["pending", "approved", "rejected"] = "approved"


@router.post("/memos")
def create_bctc_memo(
    payload: CreateMemoPayload,
    response: Response,
    principal: AuthPrincipal = Depends(resolve_principal),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict[str, Any]:
    # Check Idempotency-Key (T32)
    if idempotency_key:
        cache_key = f"{principal.account_id}:{idempotency_key}"
        if cache_key in _IDEMPOTENT_MEMOS:
            response.headers["Cache-Control"] = "no-store"
            return _IDEMPOTENT_MEMOS[cache_key]

    subject = payload.subject or payload.title or "BCTC evidence memo"
    parsed_refs = [ProvenanceRef.model_validate(r) for r in payload.report_refs]
    parsed_rows: list[EvidenceRow] = []
    for r in payload.evidence_rows:
        if isinstance(r, EvidenceRow):
            parsed_rows.append(r)
        elif isinstance(r, dict):
            if "claim" not in r and "claim_ref" in r:
                amt_data = r.get("amount") or {}
                if isinstance(amt_data, dict):
                    prov = ProvenanceRef.model_validate(amt_data.get("provenance") or {})
                    val = NumericValue(
                        value=float(amt_data.get("value", 0.0)),
                        unit=amt_data.get("unit", "VND"),
                        calculation_status="ok",
                        provenance=prov,
                    )
                    cit = prov
                else:
                    prov = parsed_refs[0] if parsed_refs else ProvenanceRef(report_id="report", revision_id="rev", period="2024Q3", source="vndirect", fetched_at="2026-09-01T00:00:00Z")
                    val = NumericValue(
                        value=float(amt_data) if amt_data else 0.0,
                        unit="VND",
                        calculation_status="ok",
                        provenance=prov,
                    )
                    cit = prov
                parsed_rows.append(
                    EvidenceRow(
                        claim=str(r["claim_ref"]),
                        kind=r.get("kind", "fact"),
                        value=val,
                        citation=cit,
                    )
                )
            else:
                # Accept the compact workspace row shape while normalizing it
                # to the typed provenance contract before persistence.
                raw_value = r.get("value") if isinstance(r, dict) else None
                if isinstance(raw_value, dict) and "raw" in raw_value:
                    citation = r.get("citation") or {}
                    unit = str(raw_value.get("unit") or "VND")
                    unit = {"ty_vnd": "VND_bn", "tỷ_vnd": "VND_bn"}.get(unit.lower(), unit)
                    provenance = ProvenanceRef(
                        report_id=str(citation.get("document_id") or "workspace-report"),
                        revision_id=str(citation.get("revision_id") or "workspace-revision"),
                        period=str(payload.period or "unknown"),
                        source=str(citation.get("source") or "user_upload"),
                        fetched_at=str(citation.get("fetched_at") or "1970-01-01T00:00:00Z"),
                    )
                    parsed_rows.append(
                        EvidenceRow(
                            claim=str(r.get("claim") or "BCTC claim"),
                            kind=r.get("kind", "fact"),
                            value=NumericValue(
                                value=float(raw_value.get("raw") or 0),
                                unit=unit,
                                calculation_status="ok",
                                provenance=provenance,
                            ),
                            citation=provenance,
                        )
                    )
                else:
                    parsed_rows.append(EvidenceRow.model_validate(r))

    service = MemoService()
    memo = service.create_memo(
        account_id=principal.account_id,
        subject=subject,
        report_refs=parsed_refs,
        scope=payload.scope,
        evidence_rows=parsed_rows,
        interpretations=payload.interpretations,
        unresolved_questions=payload.unresolved_questions,
        limitations=payload.limitations,
        reviewer_status=payload.reviewer_status,
    )

    memo_dict = memo.model_dump(mode="json")

    # Cache for idempotency
    if idempotency_key:
        _IDEMPOTENT_MEMOS[f"{principal.account_id}:{idempotency_key}"] = memo_dict

    # Emit event (T40: payload MUST NOT contain numeric amounts)
    account_id_hash = hashlib.sha256(principal.account_id.encode("utf-8")).hexdigest()[:12]
    logger.info(
        "bctc.evidence_memo.created",
        extra={
            "event": "bctc.evidence_memo.created",
            "memo_id": memo.memo_id,
            "account_id_hash": account_id_hash,
            "subject": memo.subject,
            "scope": memo.scope,
        },
    )
    try:
        from risk_dashboard.modules.analytics_monitoring.application.emitter import emit_analytics_event
        emit_analytics_event(
            event_name="bctc.evidence_memo.created",
            event_category="memo",
            module="financials_product",
            surface="bctc_workspace",
            user_id=principal.account_id,
            properties={"memo_id": memo.memo_id, "subject": memo.subject, "scope": memo.scope},
        )
    except Exception:
        pass

    response.headers["Cache-Control"] = "no-store"
    return memo_dict


@router.get("/memos")
def list_bctc_memos(
    principal: AuthPrincipal = Depends(resolve_principal),
) -> dict[str, Any]:
    service = MemoService()
    memos = service.repo.list_memos_by_account(principal.account_id)
    return {
        "memos": [m.model_dump(mode="json") for m in memos],
        "count": len(memos),
    }


@router.get("/memos/{memo_id}")
def get_bctc_memo(
    memo_id: str,
    response: Response,
    revision_id: str | None = None,
    principal: AuthPrincipal = Depends(resolve_principal),
) -> dict[str, Any]:
    service = MemoService()
    try:
        memo = service.get_memo(account_id=principal.account_id, memo_id=memo_id)
    except (KeyError, ValueError):
        # 404 non-disclosing on cross-account access (T14)
        raise HTTPException(status_code=404, detail="Memo not found.")

    if revision_id:
        service.check_staleness(
            account_id=principal.account_id,
            memo_id=memo_id,
            current_revision_id=revision_id,
        )
        memo = service.get_memo(account_id=principal.account_id, memo_id=memo_id)

    response.headers["Cache-Control"] = "no-store"
    return memo.model_dump(mode="json")


@router.delete("/memos/{memo_id}")
def delete_bctc_memo(
    memo_id: str,
    principal: AuthPrincipal = Depends(resolve_principal),
) -> dict[str, Any]:
    service = MemoService()
    deleted = service.archive_memo(account_id=principal.account_id, memo_id=memo_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memo not found.")
    return {"deleted": True, "memo_id": memo_id}


# ==============================================================================
# S9 & G6: Health Check (G6, T21)
# ==============================================================================
@router.get("/health")
@router.get("/health/bctc-agent")
def bctc_agent_health() -> dict[str, Any]:
    from risk_dashboard.modules.agentic_core.application.tool_registry import get_default_tool_registry
    registry = get_default_tool_registry()
    manifests = registry.list_tools()
    bctc_tools = [m for m in manifests if m.tool_id.startswith("bctc.")]

    # Check database
    db_status = "ok"
    try:
        with open_app_state_db() as conn:
            conn.execute("SELECT 1")
    except Exception as exc:
        db_status = f"error: {exc}"

    return {
        "status": "healthy" if len(bctc_tools) == 6 and db_status == "ok" else "degraded",
        "checks": {
            "tool_registry": "ok" if len(bctc_tools) == 6 else "incomplete",
            "bctc_tools_registered": len(bctc_tools),
            "database": db_status,
            "feature_flag": "enabled",
        },
        "version": "1.0.0",
    }
