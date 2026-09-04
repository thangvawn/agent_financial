from __future__ import annotations

from abc import ABC, abstractmethod

from risk_dashboard.modules.learning.domain.entities import (
    CheckpointRecord,
    LearningCmsDocument,
    LearningCourse,
    LearningHomeState,
    LearningLesson,
    LearningPath,
    LearningProgress,
    ProgressReceiptRecord,
    VerifiedEventRecord,
)


class LearningCatalogReader(ABC):
    @abstractmethod
    def get_course(self, *, course_id: str) -> LearningCourse:
        raise NotImplementedError

    @abstractmethod
    def get_path(self, *, path_id: str) -> LearningPath:
        raise NotImplementedError

    @abstractmethod
    def get_lesson(self, *, lesson_id: str) -> LearningLesson:
        raise NotImplementedError

    @abstractmethod
    def get_path_for_persona(self, *, persona_segment: str, primary_route: str) -> LearningPath:
        raise NotImplementedError

    @abstractmethod
    def get_context_lesson_id(self, *, trigger: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def list_courses(self) -> list[LearningCourse]:
        raise NotImplementedError

    @abstractmethod
    def list_paths(self) -> list[LearningPath]:
        raise NotImplementedError

    @abstractmethod
    def list_lessons(self) -> list[LearningLesson]:
        raise NotImplementedError


class LearningProgressRepository(ABC):
    @abstractmethod
    def get_progress(self, *, user_id: str, lesson_id: str) -> LearningProgress | None:
        raise NotImplementedError

    @abstractmethod
    def list_by_path(self, *, user_id: str, path_id: str) -> list[LearningProgress]:
        raise NotImplementedError

    @abstractmethod
    def save_progress(self, progress: LearningProgress) -> LearningProgress:
        raise NotImplementedError


class LearningHomeReader(ABC):
    @abstractmethod
    def get_home_state(self, *, user_id: str) -> LearningHomeState:
        raise NotImplementedError


class LearningHomeWriter(ABC):
    @abstractmethod
    def save_home_state(self, state: LearningHomeState) -> LearningHomeState:
        raise NotImplementedError


class LearningCmsRepository(ABC):
    @abstractmethod
    def get_document(self, *, doc_type: str, doc_id: str) -> LearningCmsDocument | None:
        raise NotImplementedError

    @abstractmethod
    def list_documents(self, *, doc_type: str) -> list[LearningCmsDocument]:
        raise NotImplementedError

    @abstractmethod
    def save_document(self, document: LearningCmsDocument) -> LearningCmsDocument:
        raise NotImplementedError


class LearningCheckpointRepository(ABC):
    @abstractmethod
    def save_checkpoint(self, checkpoint: CheckpointRecord) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_checkpoint(self, *, checkpoint_id: str) -> CheckpointRecord | None:
        raise NotImplementedError

    @abstractmethod
    def save_verified_event(self, event: VerifiedEventRecord) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_verified_event(self, *, event_id: str) -> VerifiedEventRecord | None:
        raise NotImplementedError

    @abstractmethod
    def get_receipt_by_idempotency_key(self, *, account_id: str, idempotency_key: str) -> ProgressReceiptRecord | None:
        raise NotImplementedError

    @abstractmethod
    def save_receipt(self, receipt: ProgressReceiptRecord) -> None:
        raise NotImplementedError

