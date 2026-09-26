from __future__ import annotations

import logging
import random
import re
import unicodedata
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from risk_dashboard.modules.learning.domain.entities import (
    CheckpointRecord,
    LearningProgress,
    ProgressReceiptRecord,
    VerifiedEventRecord,
    utc_now_iso,
)
from risk_dashboard.modules.learning.domain.policies import quiz_progress, refresh_learning_home_state
from risk_dashboard.modules.learning.domain.ports import (
    LearningCatalogReader,
    LearningCheckpointRepository,
    LearningHomeReader,
    LearningHomeWriter,
    LearningProgressRepository,
)
from risk_dashboard.modules.learning.infrastructure.catalog_reader import SqliteLearningCatalog
from risk_dashboard.modules.learning.infrastructure.repositories.sqlite import (
    SqliteLearningCheckpointRepository,
    SqliteLearningHomeRepository,
)
from risk_dashboard.modules.learning.schemas.agent_tools import (
    GetQuizItemOutput,
    GradeCheckpointOutput,
    UpdateProgressOutput,
)

logger = logging.getLogger(__name__)


class LearningCheckpointService:
    def __init__(
        self,
        checkpoint_repo: LearningCheckpointRepository | None = None,
        catalog: LearningCatalogReader | None = None,
        progress_repo: LearningProgressRepository | None = None,
        home_reader: LearningHomeReader | None = None,
        home_writer: LearningHomeWriter | None = None,
    ) -> None:
        self.checkpoint_repo = checkpoint_repo or SqliteLearningCheckpointRepository()
        self.catalog = catalog or SqliteLearningCatalog()
        self.progress_repo = progress_repo or SqliteLearningHomeRepository()
        self.home_reader = home_reader or SqliteLearningHomeRepository()
        self.home_writer = home_writer or SqliteLearningHomeRepository()

    def create_checkpoint(
        self,
        *,
        account_id: str,
        lesson_id: str,
        difficulty: str | None = None,
        ttl_seconds: int = 900,
    ) -> GetQuizItemOutput:
        """Protected item selector that generates an account-bound, TTL-bound checkpoint token without answer leakage."""
        if not account_id:
            raise ValueError("account_id is required")
        if not lesson_id:
            raise ValueError("lesson_id is required")

        try:
            lesson = self.catalog.get_lesson(lesson_id=lesson_id)
        except Exception as exc:
            logger.warning("Failed to resolve lesson %s for checkpoint: %s", lesson_id, exc)
            lesson = None

        if not lesson or not lesson.quiz_questions:
            fallback_lesson = None
            try:
                for cand_lesson in self.catalog.list_lessons():
                    if cand_lesson.quiz_questions:
                        fallback_lesson = cand_lesson
                        break
            except Exception:
                pass
            if fallback_lesson and fallback_lesson.quiz_questions:
                lesson = fallback_lesson
            else:
                raise ValueError(f"Lesson '{lesson_id}' has no quiz questions available.")

        # Question selection (can filter by difficulty if matching questions exist)
        candidates = lesson.quiz_questions
        if difficulty:
            matching = [q for q in candidates if getattr(q, "difficulty", None) == difficulty]
            if matching:
                candidates = matching
        question = random.choice(candidates)
        checkpoint_id = f"cp_{uuid4().hex}"
        now = datetime.now(timezone.utc)
        expires_at = (now + timedelta(seconds=ttl_seconds)).isoformat()
        created_at = now.isoformat()

        record = CheckpointRecord(
            checkpoint_id=checkpoint_id,
            account_id=account_id,
            lesson_id=lesson.lesson_id,
            question_id=question.question_id,
            prompt=question.prompt,
            options=tuple(question.options),
            correct_answer=question.correct_answer,
            explanation=question.explanation,
            expires_at=expires_at,
            created_at=created_at,
        )
        self.checkpoint_repo.save_checkpoint(record)

        return GetQuizItemOutput(
            schema_version="1.0.0",
            checkpoint_id=checkpoint_id,
            lesson_id=lesson.lesson_id,
            prompt=question.prompt,
            options=tuple(question.options),
            expires_at=expires_at,
        )

    def grade_checkpoint(
        self,
        *,
        account_id: str,
        checkpoint_id: str,
        response: str,
    ) -> GradeCheckpointOutput:
        """Server-side protected grading boundary. Evaluates answer without exposing secret key to model context."""
        if not account_id:
            raise ValueError("account_id is required")
        if not checkpoint_id:
            raise ValueError("checkpoint_id is required")

        checkpoint = self.checkpoint_repo.get_checkpoint(checkpoint_id=checkpoint_id)
        if checkpoint is None:
            raise ValueError(f"Checkpoint '{checkpoint_id}' not found.")

        # Account ownership check (zero cross-account leakage)
        if checkpoint.account_id != account_id:
            raise PermissionError("Checkpoint token does not belong to the authenticated account.")

        # Expiry check
        now = datetime.now(timezone.utc)
        expiry_dt = datetime.fromisoformat(checkpoint.expires_at)
        if expiry_dt < now:
            raise ValueError(f"Checkpoint '{checkpoint_id}' has expired at {checkpoint.expires_at}.")

        # Grade evaluation
        clean_response = _normalize_response(response)
        clean_correct = _normalize_response(checkpoint.correct_answer)
        resolved = _resolve_response(clean_response, options=checkpoint.options)
        passed = resolved.lower() == clean_correct.lower() or resolved == clean_correct

        score = 100 if passed else 0
        if passed:
            rubric_evidence = (
                f"Đáp án chính xác: phương án '{clean_response}' giải quyết đúng yêu cầu câu hỏi.",
                checkpoint.explanation,
            )
            misconceptions = ()
        else:
            rubric_evidence = (
                f"Phương án '{clean_response}' chưa chính xác theo nội dung bài giảng.",
                checkpoint.explanation,
            )
            misconceptions = (
                f"Học viên chọn '{clean_response}', cần làm rõ nguyên lý: {checkpoint.explanation}",
            )

        event_id = f"ev_{uuid4().hex}"
        event = VerifiedEventRecord(
            event_id=event_id,
            account_id=account_id,
            checkpoint_id=checkpoint_id,
            lesson_id=checkpoint.lesson_id,
            score=score,
            passed=passed,
            rubric_evidence=rubric_evidence,
            misconceptions=misconceptions,
            created_at=now.isoformat(),
        )
        self.checkpoint_repo.save_verified_event(event)

        return GradeCheckpointOutput(
            schema_version="1.0.0",
            checkpoint_id=checkpoint_id,
            lesson_id=checkpoint.lesson_id,
            passed=passed,
            score=score,
            rubric_evidence=rubric_evidence,
            misconceptions=misconceptions,
            verified_event_id=event_id,
        )

    def update_progress_confirmed(
        self,
        *,
        account_id: str,
        verified_event_id: str,
        idempotency_key: str,
        confirmation_id: str,
    ) -> UpdateProgressOutput:
        """Confirmed and idempotent progress update. Requires verified event and user confirmation."""
        if not account_id:
            raise ValueError("account_id is required")
        if not verified_event_id:
            raise ValueError("verified_event_id is required")
        if not idempotency_key:
            raise ValueError("idempotency_key is required")
        if not confirmation_id:
            raise ValueError("confirmation_id is required")

        # 1. Check idempotency receipt
        existing = self.checkpoint_repo.get_receipt_by_idempotency_key(
            account_id=account_id, idempotency_key=idempotency_key
        )
        if existing is not None:
            return UpdateProgressOutput(
                schema_version="1.0.0",
                receipt_id=existing.receipt_id,
                lesson_id=existing.lesson_id,
                status=existing.status,
                quiz_score=existing.quiz_score,
                updated_at=existing.created_at,
            )

        # 2. Check verified event
        event = self.checkpoint_repo.get_verified_event(event_id=verified_event_id)
        if event is None:
            raise ValueError(f"Verified event '{verified_event_id}' not found.")

        if event.account_id != account_id:
            raise PermissionError("Verified event does not belong to the authenticated account.")

        if not event.passed:
            raise ValueError("Cannot update progress from a failed checkpoint event.")

        # 3. Apply progress update
        try:
            home = self.home_reader.get_home_state(user_id=account_id)
            path_id = home.path_id
        except Exception:
            path_id = "starter-foundations"

        previous = self.progress_repo.get_progress(user_id=account_id, lesson_id=event.lesson_id)
        updated_progress = quiz_progress(
            user_id=account_id,
            path_id=path_id,
            lesson_id=event.lesson_id,
            score=event.score,
            previous=previous,
        )
        self.progress_repo.save_progress(updated_progress)

        # Refresh home state if possible
        try:
            path = self.catalog.get_path(path_id=path_id)
            lessons = [self.catalog.get_lesson(lesson_id=lid) for lid in path.lesson_ids]
            progress_items = self.progress_repo.list_by_path(user_id=account_id, path_id=path_id)
            refreshed_home = refresh_learning_home_state(
                user_id=account_id,
                path=path,
                lessons=lessons,
                progress_items=progress_items,
            )
            self.home_writer.save_home_state(refreshed_home)
        except Exception as exc:
            logger.warning(f"Could not refresh home state during checkpoint update: {exc}")

        # 4. Save idempotent receipt
        now_str = utc_now_iso()
        receipt_id = f"rcpt_{uuid4().hex}"
        receipt = ProgressReceiptRecord(
            receipt_id=receipt_id,
            account_id=account_id,
            verified_event_id=verified_event_id,
            idempotency_key=idempotency_key,
            confirmation_id=confirmation_id,
            lesson_id=event.lesson_id,
            status=updated_progress.status,
            quiz_score=event.score,
            created_at=now_str,
        )
        self.checkpoint_repo.save_receipt(receipt)

        return UpdateProgressOutput(
            schema_version="1.0.0",
            receipt_id=receipt_id,
            lesson_id=event.lesson_id,
            status=updated_progress.status,
            quiz_score=event.score,
            updated_at=now_str,
        )


def _normalize_response(value: str | None) -> str:
    """Normalize unicode and collapse whitespace so cosmetic differences don't fail grading."""
    if not value:
        return ""
    text = unicodedata.normalize("NFKC", value)
    text = re.sub(r"[​‌‍﻿]", "", text)
    return " ".join(text.split()).strip()


def _resolve_response(response: str, *, options: tuple[str, ...]) -> str:
    """Resolve shortcut answers ('Đáp án A', 'Option 2', bare 'B') to the option text when possible."""
    match = re.match(r"(?:đáp án|option)\s*([a-e1-5])\b", response, re.IGNORECASE)
    token = match.group(1) if match else None
    if token is None and re.fullmatch(r"[a-e1-5]", response, re.IGNORECASE):
        token = response

    if token is None or not options:
        return response

    upper = token.upper()
    if "A" <= upper <= "E":
        idx = ord(upper) - ord("A")
    else:
        idx = int(upper) - 1

    if 0 <= idx < len(options):
        return options[idx]
    return response

