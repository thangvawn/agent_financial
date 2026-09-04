from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from typing import Any

from risk_dashboard.modules.home_onboarding.schemas.journey import (
    HomeDomainSummaryV1,
    SummarySourceRefV1,
)

logger = logging.getLogger(__name__)


def _calc_simulation_expires_at(created_at_iso: str) -> str:
    try:
        dt = datetime.fromisoformat(created_at_iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    except Exception as exc:
        logger.warning(f"Error parsing date {created_at_iso}: {exc}")
        dt = datetime.now(timezone.utc)
    return (dt + timedelta(days=14)).isoformat()


class SimulationSummaryReader:
    surface: str = "simulation"

    def __init__(self, repo: Any | None = None) -> None:
        self._repo = repo

    def _get_repo(self) -> Any | None:
        if self._repo is not None:
            return self._repo
        try:
            from risk_dashboard.modules.pro_lab.infrastructure.repositories.sqlite import (
                SqliteProLabExperimentRepository,
            )
            return SqliteProLabExperimentRepository()
        except Exception as exc:
            logger.warning(f"Failed to initialize SqliteProLabExperimentRepository: {exc}")
            return None

    def list_reviewed_summaries(
        self,
        *,
        account_id: str,
        scopes: tuple[str, ...],
        as_of: str,
        limit: int = 4,
    ) -> tuple[HomeDomainSummaryV1, ...]:
        repo = self._get_repo()
        if repo is None:
            return ()

        try:
            experiments = repo.list_by_user(user_id=account_id)
        except Exception as exc:
            logger.warning(
                f"Error fetching simulation experiments for account {account_id}: {exc}",
                exc_info=True,
            )
            return ()

        summaries: list[HomeDomainSummaryV1] = []
        for exp in experiments:
            rev_status = getattr(exp, "review_status", "")
            if rev_status not in ("accepted", "approved"):
                continue

            exp_id = str(getattr(exp, "experiment_id", ""))
            exp_type = getattr(exp, "experiment_type", "backtest")
            status = getattr(exp, "status", "")
            notes = getattr(exp, "review_notes", "") or ""
            summary_text = (
                notes
                if notes
                else f"Thực nghiệm mô phỏng danh mục {exp_type} ({status})."
            )

            created_at = getattr(exp, "created_at", "") or as_of
            updated_at = getattr(exp, "reviewed_at", "") or created_at
            expires_at = _calc_simulation_expires_at(created_at)
            if expires_at <= as_of:
                continue

            state = "stale" if status == "stale" else "ready"
            kind = "stale_artifact" if state == "stale" else "research_artifact"

            # Map domain review_status to HomeDomainSummaryV1 review_status Literal
            mapped_status = "accepted" if rev_status == "approved" else rev_status

            source_ref = SummarySourceRefV1(
                surface="simulation",
                resource_type="simulation_experiment",
                resource_id=exp_id,
                resource_version=1,
            )

            summaries.append(
                HomeDomainSummaryV1(
                    summary_id=f"summary:simulation:{account_id}:{exp_id}",
                    account_id=account_id,
                    surface="simulation",
                    kind=kind,
                    title=f"Mô phỏng: {exp_type.capitalize()}"[:120],
                    compact_summary=summary_text[:500],
                    source_ref=source_ref,
                    review_status=mapped_status,
                    review_policy_version="simulation-methodology-v1",
                    allowed_action_type="refresh_artifact",
                    allowed_cta_path=f"/simulation?experiment_id={exp_id}",
                    state=state,
                    created_at=created_at,
                    updated_at=updated_at,
                    expires_at=expires_at,
                )
            )
            if len(summaries) >= limit:
                break

        return tuple(summaries)

