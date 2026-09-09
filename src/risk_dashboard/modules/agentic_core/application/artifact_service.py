from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from risk_dashboard.modules.agentic_core.infrastructure.repositories import AgenticArtifactRepository
from risk_dashboard.modules.agentic_core.schemas.artifact import AgentArtifact
from risk_dashboard.platform.database import open_app_state_db


class ArtifactTransitionError(Exception):
    """Raised when an invalid artifact lifecycle transition is attempted."""

    def __init__(self, message: str, status_code: int = 409) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ArtifactService:
    def __init__(self, artifact_repo: AgenticArtifactRepository | None = None) -> None:
        self._artifact_repo = artifact_repo or AgenticArtifactRepository()

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def _check_expired(self, artifact: AgentArtifact) -> bool:
        if artifact.expires_at is None:
            return False
        return artifact.expires_at < self._now_iso()

    def submit_for_review(self, *, artifact_id: str, account_id: str) -> AgentArtifact:
        with open_app_state_db() as conn:
            artifact = self._artifact_repo.get(conn, artifact_id=artifact_id, account_id=account_id)
            if artifact is None:
                raise ArtifactTransitionError("Artifact not found.", status_code=404)

            if self._check_expired(artifact):
                expired_artifact = artifact.model_copy(update={"review_status": "expired"})
                self._artifact_repo.save(conn, expired_artifact)
                raise ArtifactTransitionError("Artifact has expired.", status_code=409)

            if artifact.review_status not in ("draft", "reviewed"):
                raise ArtifactTransitionError(
                    f"Cannot submit artifact in status '{artifact.review_status}' for review.",
                    status_code=409,
                )

            updated = artifact.model_copy(update={"review_status": "reviewed"})
            self._artifact_repo.save(conn, updated)
            return updated

    def accept(self, *, artifact_id: str, account_id: str) -> AgentArtifact:
        with open_app_state_db() as conn:
            artifact = self._artifact_repo.get(conn, artifact_id=artifact_id, account_id=account_id)
            if artifact is None:
                raise ArtifactTransitionError("Artifact not found.", status_code=404)

            if self._check_expired(artifact) or artifact.review_status == "expired":
                if artifact.review_status != "expired":
                    self._artifact_repo.save(conn, artifact.model_copy(update={"review_status": "expired"}))
                raise ArtifactTransitionError("Cannot accept expired artifact.", status_code=409)

            if artifact.review_status == "accepted":
                return artifact  # Idempotent

            if artifact.review_status != "reviewed":
                raise ArtifactTransitionError(
                    f"Cannot accept unreviewed artifact in status '{artifact.review_status}'.",
                    status_code=409,
                )

            updated = artifact.model_copy(update={"review_status": "accepted"})
            self._artifact_repo.save(conn, updated)
            return updated

    def export(self, *, artifact_id: str, account_id: str) -> dict[str, Any]:
        with open_app_state_db() as conn:
            artifact = self._artifact_repo.get(conn, artifact_id=artifact_id, account_id=account_id)
            if artifact is None:
                raise ArtifactTransitionError("Artifact not found.", status_code=404)

            if self._check_expired(artifact) or artifact.review_status == "expired":
                raise ArtifactTransitionError("Cannot export expired artifact.", status_code=409)

            if artifact.review_status not in ("reviewed", "accepted", "exported"):
                raise ArtifactTransitionError(
                    f"Cannot export unreviewed artifact in status '{artifact.review_status}'.",
                    status_code=409,
                )

            updated = artifact.model_copy(update={"review_status": "exported"})
            self._artifact_repo.save(conn, updated)
            return {
                "artifact_id": artifact.artifact_id,
                "status": "exported",
                "payload": artifact.model_dump(mode="json"),
            }
