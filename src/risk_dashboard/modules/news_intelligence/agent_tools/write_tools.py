from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from risk_dashboard.modules.agentic_core.schemas.envelope import TrustedExecutionEnvelope
from risk_dashboard.modules.news_intelligence.agent_tools.helpers import check_scope
from risk_dashboard.modules.news_intelligence.application.brief_builder import calculate_evidence_hash
from risk_dashboard.modules.news_intelligence.domain.entities import utc_now_iso
from risk_dashboard.modules.news_intelligence.domain.ports import BriefRepositoryPort
from risk_dashboard.modules.news_intelligence.infrastructure.brief_repository import SqliteBriefRepository
from risk_dashboard.modules.news_intelligence.schemas.agent_tools import (
    NewsEvidenceBriefArtifact,
    SaveBriefInput,
    SaveBriefOutput,
)


async def save_brief(
    payload: SaveBriefInput,
    envelope: TrustedExecutionEnvelope,
    repo: BriefRepositoryPort | None = None,
) -> SaveBriefOutput:
    check_scope(envelope, ("public:news:write",))

    if envelope.account_id in ("anonymous", "") or envelope.account_id.startswith("anon_"):
        raise PermissionError("Anonymous accounts are not permitted to save briefs.")

    expected_hash = calculate_evidence_hash(payload.evidence_rows)
    if payload.evidence_hash != expected_hash:
        raise ValueError("NEWS_BRIEF_STALE: Evidence hash does not match current evidence rows. Please regenerate.")

    brief_repo = repo or SqliteBriefRepository()

    brief_id = f"brief_{uuid4().hex[:12]}"
    artifact_id = f"art_{uuid4().hex[:12]}"
    receipt_id = f"rcpt_{uuid4().hex[:12]}"
    now_iso = utc_now_iso()
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()

    cluster_ids = payload.cluster_ids
    if not cluster_ids:
        cluster_ids = tuple(sorted({aid for row in payload.evidence_rows for aid in row.article_ids})) or ("cluster_default",)

    artifact = NewsEvidenceBriefArtifact(
        schema_version="1.0.0",
        brief_id=brief_id,
        artifact_id=artifact_id,
        authoring_run_id=envelope.run_id,
        account_id=envelope.account_id,
        title=payload.title,
        objective=payload.objective,
        cluster_ids=cluster_ids,
        evidence_rows=payload.evidence_rows,
        source_coverage=1.0,
        limitations=payload.limitations,
        review_status="reviewed",
        evidence_hash=expected_hash,
        version=1,
        created_at=now_iso,
        expires_at=expires_at,
    )

    brief_repo.save(artifact)

    return SaveBriefOutput(
        schema_version="1.0.0",
        brief_id=brief_id,
        artifact_id=artifact_id,
        receipt_id=receipt_id,
        version=1,
        status="saved",
        created_at=now_iso,
        expires_at=expires_at,
    )
