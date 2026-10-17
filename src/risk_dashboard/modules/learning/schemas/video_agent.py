from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl, field_validator


class VideoTranscriptSegmentResponse(BaseModel):
    segment_id: str
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)
    text: str = Field(min_length=1, max_length=2000)


class VideoEvidenceResponse(BaseModel):
    segment_id: str
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)
    label: str = Field(min_length=1, max_length=160)


class VideoAgentPrepareRequest(BaseModel):
    source_url: HttpUrl | None = None
    # A transcript supplied by the course owner is useful when a provider does
    # not expose captions. It is deliberately bounded to protect the public API.
    transcript_text: str | None = Field(default=None, max_length=200_000)
    language: str = Field(default="vi", min_length=2, max_length=12)
    force_refresh: bool = False

    @field_validator("transcript_text")
    @classmethod
    def normalize_transcript(cls, value: str | None) -> str | None:
        if value is None:
            return None
        clean = " ".join(value.split())
        return clean or None


class VideoAgentPrepareResponse(BaseModel):
    lesson_id: str
    status: str
    source: str
    language: str
    transcript_hash: str
    segment_count: int = Field(ge=0)
    duration_seconds: float = Field(ge=0)
    quiz_count: int = Field(ge=0)
    warnings: tuple[str, ...] = ()
    prepared_at: str


class VideoAgentStatusResponse(BaseModel):
    lesson_id: str
    status: str
    source: str | None = None
    language: str | None = None
    transcript_hash: str | None = None
    segment_count: int = Field(default=0, ge=0)
    duration_seconds: float = Field(default=0, ge=0)
    quiz_count: int = Field(default=0, ge=0)
    warnings: tuple[str, ...] = ()
    updated_at: str | None = None


class VideoAgentQuestionResponse(BaseModel):
    question_id: str
    prompt: str
    options: tuple[str, ...] = Field(min_length=3, max_length=4)
    difficulty: str = "beginner"
    evidence: tuple[VideoEvidenceResponse, ...] = ()


class VideoAgentCheckpointResponse(BaseModel):
    checkpoint_id: str
    lesson_id: str
    question: VideoAgentQuestionResponse
    expires_at: str


class VideoAgentCheckpointRequest(BaseModel):
    source_url: HttpUrl | None = None
    current_time_seconds: float = Field(default=0, ge=0, le=86_400)


class VideoAgentGradeRequest(BaseModel):
    checkpoint_id: str = Field(min_length=8, max_length=100)
    response: str = Field(min_length=1, max_length=300)


class VideoAgentGradeResponse(BaseModel):
    checkpoint_id: str
    lesson_id: str
    passed: bool
    score: int = Field(ge=0, le=100)
    feedback: str
    explanation: str
    evidence: tuple[VideoEvidenceResponse, ...] = ()


class VideoAgentAskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1_000)
    source_url: HttpUrl | None = None
    current_time_seconds: float = Field(default=0, ge=0, le=86_400)
    window_seconds: float = Field(default=45, ge=10, le=180)
    language: str = Field(default="vi", min_length=2, max_length=12)


class VideoAgentCitationResponse(BaseModel):
    segment_id: str
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)
    label: str
    text: str = Field(min_length=1, max_length=2000)


class VideoAgentAskResponse(BaseModel):
    lesson_id: str
    answer: str
    grounded: bool
    citations: tuple[VideoAgentCitationResponse, ...] = ()
    limitations: tuple[str, ...] = ()
