from __future__ import annotations

import hashlib
import html
import math
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol
from uuid import uuid4

from risk_dashboard.modules.learning.domain.entities import LearningLesson
from risk_dashboard.modules.learning.domain.ports import LearningCatalogReader
from risk_dashboard.modules.learning.infrastructure.catalog_reader import SqliteLearningCatalog
from risk_dashboard.modules.learning.infrastructure.video_agent_repository import (
    VideoAgentRepository,
)
from risk_dashboard.modules.learning.schemas.video_agent import (
    VideoAgentAskResponse,
    VideoAgentCheckpointResponse,
    VideoAgentCitationResponse,
    VideoAgentGradeResponse,
    VideoAgentPrepareResponse,
    VideoAgentQuestionResponse,
    VideoAgentStatusResponse,
    VideoEvidenceResponse,
)

MAX_SEGMENTS = 20_000
MAX_TRANSCRIPT_CHARS = 200_000
_SPACE_RE = re.compile(r"\s+")
_TAG_RE = re.compile(r"<[^>]+>")
_SENTENCE_RE = re.compile(r"(?<=[.!?。！？])\s+")
_UNSAFE_INSTRUCTION_RE = re.compile(
    r"ignore\s+(all\s+)?previous\s+instructions|system\s+prompt\s*:|you\s+are\s+now\s+a\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class TranscriptSegment:
    segment_id: str
    start_seconds: float
    end_seconds: float
    text: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "start_seconds": self.start_seconds,
            "end_seconds": self.end_seconds,
            "text": self.text,
        }


@dataclass(frozen=True)
class TranscriptDocument:
    source: str
    language: str
    segments: tuple[TranscriptSegment, ...]
    transcript_hash: str
    duration_seconds: float
    warnings: tuple[str, ...] = ()


class TranscriptProvider(Protocol):
    def fetch(self, source_url: str, *, language: str) -> tuple[TranscriptSegment, ...]: ...


def _clean_text(value: str) -> str:
    value = html.unescape(_TAG_RE.sub(" ", value or ""))
    value = _UNSAFE_INSTRUCTION_RE.sub(" ", value)
    return _SPACE_RE.sub(" ", value).strip()


def _safe_url(source_url: str) -> str:
    parsed = urllib.parse.urlparse(source_url)
    host = (parsed.hostname or "").lower().rstrip(".")
    if parsed.scheme != "https" or host not in {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}:
        raise ValueError("source_url chỉ hỗ trợ URL YouTube HTTPS được phép.")
    if host == "youtu.be":
        video_id = parsed.path.strip("/").split("/")[0]
    else:
        video_id = urllib.parse.parse_qs(parsed.query).get("v", [""])[0]
    if not re.fullmatch(r"[A-Za-z0-9_-]{6,20}", video_id or ""):
        raise ValueError("source_url không chứa YouTube video id hợp lệ.")
    return f"https://www.youtube.com/watch?v={video_id}"


def youtube_video_id(source_url: str) -> str:
    canonical = _safe_url(source_url)
    return urllib.parse.parse_qs(urllib.parse.urlparse(canonical).query)["v"][0]


class YouTubeTranscriptProvider:
    """Small, dependency-free provider for public YouTube timed-text captions.

    The provider deliberately does not download video or bypass access controls.
    An unavailable caption track is represented as a normal provider error so the
    service can use an owner-supplied transcript or lesson fallback.
    """

    def __init__(self, *, timeout_seconds: float = 8.0) -> None:
        self.timeout_seconds = timeout_seconds

    def fetch(self, source_url: str, *, language: str) -> tuple[TranscriptSegment, ...]:
        video_id = youtube_video_id(source_url)
        languages = [language.split("-")[0], "en", "vi"]
        seen: set[str] = set()
        for lang in languages:
            if not lang or lang in seen:
                continue
            seen.add(lang)
            query = urllib.parse.urlencode({"v": video_id, "lang": lang, "fmt": "srv3"})
            url = f"https://www.youtube.com/api/timedtext?{query}"
            request = urllib.request.Request(url, headers={"User-Agent": "Northstar-Learning-Agent/1.0"})
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                    final_host = (urllib.parse.urlparse(response.geturl()).hostname or "").lower().rstrip(".")
                    if final_host not in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
                        raise RuntimeError("Phản hồi phụ đề chuyển hướng khỏi YouTube.")
                    payload = response.read(2_000_000)
            except Exception:
                continue
            try:
                root = ET.fromstring(payload)
            except ET.ParseError:
                continue
            segments: list[TranscriptSegment] = []
            for index, node in enumerate(root.findall(".//text")):
                text = _clean_text("".join(node.itertext()))
                try:
                    start = float(node.attrib.get("start", "0"))
                    duration = float(node.attrib.get("dur", "0"))
                except (TypeError, ValueError):
                    continue
                if text and math.isfinite(start) and math.isfinite(duration) and start >= 0 and duration > 0:
                    segments.append(TranscriptSegment(f"seg_{index + 1}", start, start + duration, text))
            if segments:
                return tuple(segments[:MAX_SEGMENTS])
        raise RuntimeError("Video không có phụ đề công khai ở ngôn ngữ đã chọn.")


def _hash_segments(segments: tuple[TranscriptSegment, ...]) -> str:
    canonical = "\n".join(
        f"{s.start_seconds:.3f}|{s.end_seconds:.3f}|{s.text}" for s in segments
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _normalize_segments(raw: list[TranscriptSegment]) -> tuple[TranscriptSegment, ...]:
    result: list[TranscriptSegment] = []
    for index, item in enumerate(raw[:MAX_SEGMENTS]):
        text = _clean_text(item.text)
        start = float(item.start_seconds)
        end = float(item.end_seconds)
        if not text or not math.isfinite(start) or not math.isfinite(end) or start < 0:
            continue
        if end <= start:
            end = start + max(1.0, min(30.0, len(text.split()) / 2.2))
        result.append(TranscriptSegment(f"seg_{index + 1}", round(start, 3), round(end, 3), text[:2000]))
    result.sort(key=lambda item: (item.start_seconds, item.end_seconds))
    # Re-number after sorting and ensure strictly positive intervals.
    return tuple(TranscriptSegment(f"seg_{i + 1}", s.start_seconds, s.end_seconds, s.text) for i, s in enumerate(result))


def _text_to_segments(text: str, *, duration_seconds: float = 0) -> tuple[TranscriptSegment, ...]:
    clean = _clean_text(text)[:MAX_TRANSCRIPT_CHARS]
    if not clean:
        return ()
    sentences = [item.strip() for item in _SENTENCE_RE.split(clean) if item.strip()]
    if not sentences:
        sentences = [clean]
    # Keep chunks short enough for retrieval and for a grounded prompt.
    chunks: list[str] = []
    for sentence in sentences:
        words = sentence.split()
        for offset in range(0, len(words), 70):
            chunks.append(" ".join(words[offset: offset + 70]))
    total_words = max(1, sum(len(c.split()) for c in chunks))
    inferred_duration = max(1.0, duration_seconds or total_words / 2.2)
    raw: list[TranscriptSegment] = []
    cursor = 0.0
    for chunk in chunks:
        share = inferred_duration * len(chunk.split()) / total_words
        raw.append(TranscriptSegment("", cursor, cursor + max(1.0, share), chunk))
        cursor += max(1.0, share)
    return _normalize_segments(raw)


def _evidence_for_text(segments: tuple[TranscriptSegment, ...], text: str) -> tuple[TranscriptSegment, ...]:
    tokens = {token.lower() for token in re.findall(r"[\wÀ-ỹ]{4,}", text)}
    scored = sorted(
        segments,
        key=lambda item: len(tokens.intersection({t.lower() for t in re.findall(r"[\wÀ-ỹ]{4,}", item.text)})),
        reverse=True,
    )
    return tuple(scored[:1]) if scored else ()


def _evidence_response(segments: tuple[TranscriptSegment, ...]) -> tuple[VideoEvidenceResponse, ...]:
    return tuple(
        VideoEvidenceResponse(
            segment_id=s.segment_id,
            start_seconds=s.start_seconds,
            end_seconds=s.end_seconds,
            label=f"{int(s.start_seconds // 60):02d}:{int(s.start_seconds % 60):02d}–{int(s.end_seconds // 60):02d}:{int(s.end_seconds % 60):02d}",
        )
        for s in segments
    )


class VideoLearningAgentService:
    def __init__(
        self,
        *,
        catalog: LearningCatalogReader | None = None,
        repository: VideoAgentRepository | None = None,
        transcript_provider: TranscriptProvider | None = None,
    ) -> None:
        self.catalog = catalog or SqliteLearningCatalog()
        self.repository = repository or VideoAgentRepository()
        self.transcript_provider = transcript_provider or YouTubeTranscriptProvider()

    def _lesson(self, lesson_id: str) -> LearningLesson:
        try:
            return self.catalog.get_lesson(lesson_id=lesson_id)
        except KeyError:
            raise
        except Exception as exc:
            raise KeyError(lesson_id) from exc

    def _source_key(self, source_url: str | None, transcript_text: str | None) -> str:
        if transcript_text:
            return "provided:" + hashlib.sha256(transcript_text.encode("utf-8")).hexdigest()
        return "url:" + (_safe_url(source_url) if source_url else "lesson-body")

    def _load_transcript(
        self,
        lesson: LearningLesson,
        *,
        source_url: str | None,
        transcript_text: str | None,
        language: str,
        force_refresh: bool,
    ) -> TranscriptDocument:
        if source_url:
            # Validate even when an owner-supplied transcript is present; this
            # keeps the request contract deterministic and prevents an invalid
            # URL from being silently accepted by the alternate source path.
            source_url = _safe_url(source_url)
        if not source_url and not transcript_text and not force_refresh:
            latest = self.repository.get_latest_transcript(lesson_id=lesson.lesson_id)
            if latest:
                segments = tuple(TranscriptSegment(**s) for s in latest["segments"])
                return TranscriptDocument(
                    source=latest["source"], language=latest["language"], segments=segments,
                    transcript_hash=latest["transcript_hash"], duration_seconds=latest["duration_seconds"],
                    warnings=tuple(latest.get("warnings", ())),
                )
        source_key = self._source_key(source_url, transcript_text)
        if not force_refresh:
            cached = self.repository.get_transcript(lesson_id=lesson.lesson_id, source_key=source_key)
            if cached:
                segments = tuple(TranscriptSegment(**s) for s in cached["segments"])
                return TranscriptDocument(
                    source=cached["source"], language=cached["language"], segments=segments,
                    transcript_hash=cached["transcript_hash"], duration_seconds=cached["duration_seconds"],
                    warnings=tuple(cached.get("warnings", ())),
                )

        warnings: list[str] = []
        source = "lesson_body"
        segments: tuple[TranscriptSegment, ...] = ()
        if transcript_text:
            segments = _text_to_segments(transcript_text, duration_seconds=lesson.estimated_minutes * 60)
            source = "provided"
        elif source_url:
            canonical_url = source_url
            try:
                segments = _normalize_segments(self.transcript_provider.fetch(canonical_url, language=language))
                source = "youtube_captions"
            except Exception as exc:
                warnings.append("Không lấy được phụ đề video; agent đang dùng nội dung bài học đã xuất bản làm fallback.")
                # Do not persist provider internals (which can include a URL or
                # network error) in a user-facing response.
                _ = exc
        if not segments:
            segments = _text_to_segments(" ".join(lesson.body), duration_seconds=lesson.estimated_minutes * 60)
            source = "lesson_body"
        if not segments:
            raise ValueError("Bài học chưa có transcript hoặc nội dung để agent học.")
        transcript_hash = _hash_segments(segments)
        duration = max(segment.end_seconds for segment in segments)
        now = datetime.now(timezone.utc).isoformat()
        self.repository.save_transcript(
            {
                "lesson_id": lesson.lesson_id, "source_key": source_key, "status": "ready",
                "source": source, "language": language, "transcript_hash": transcript_hash,
                "segments": [segment.as_dict() for segment in segments], "duration_seconds": duration,
                "warnings": tuple(warnings), "created_at": now, "updated_at": now,
            }
        )
        return TranscriptDocument(source, language, segments, transcript_hash, duration, tuple(warnings))

    def _generate_questions(self, lesson: LearningLesson, transcript: TranscriptDocument) -> list[dict[str, Any]]:
        cached = self.repository.get_quiz(lesson_id=lesson.lesson_id, transcript_hash=transcript.transcript_hash)
        if cached:
            return cached
        candidates = list(transcript.segments)
        questions: list[dict[str, Any]] = []
        # Existing editorial questions are preferred because their pedagogy has
        # already been reviewed by Content Ops.
        for source_question in lesson.quiz_questions:
            options = list(dict.fromkeys(item.strip() for item in source_question.options if item.strip()))
            if source_question.correct_answer not in options:
                options.insert(0, source_question.correct_answer)
            if len(options) < 3:
                options.extend(
                    candidate
                    for candidate in (
                        "Nội dung này không được đề cập trong video.",
                        "Video không đưa ra kết luận này.",
                    )
                    if candidate not in options
                )
            if len(options) > 4:
                # Keep the answer key in the public option set if an editorial
                # question contains more than four distractors.
                options = [source_question.correct_answer] + [item for item in options if item != source_question.correct_answer]
            options = options[:4]
            evidence = _evidence_for_text(transcript.segments, source_question.prompt)
            questions.append({
                "question_id": f"video_{source_question.question_id}",
                "prompt": source_question.prompt,
                "options": options,
                "correct_answer": source_question.correct_answer,
                "explanation": source_question.explanation,
                "difficulty": getattr(source_question, "difficulty", "beginner") or "beginner",
                "evidence": [s.as_dict() for s in evidence],
            })
            if len(questions) >= 3:
                break
        # Generate simple comprehension checks when a lesson has no editorial
        # bank (or only one reviewed question).
        for index, segment in enumerate(candidates):
            if len(questions) >= 3:
                break
            correct = segment.text[:180]
            if len(correct.split()) < 4 or any(q["correct_answer"] == correct for q in questions):
                continue
            distractors = [other.text[:180] for other in candidates if other.segment_id != segment.segment_id and len(other.text.split()) >= 4]
            options = [correct, *distractors[:2]]
            options.extend(["Nội dung này không được đề cập trong video.", "Video không đưa ra kết luận này."])
            options = list(dict.fromkeys(options))[:4]
            seed = hashlib.sha256(f"{transcript.transcript_hash}:{index}".encode()).digest()
            # Stable shuffle keeps a learner from seeing a new correct letter on
            # each request while still avoiding a predictable first option.
            order = sorted(range(len(options)), key=lambda i: seed[i % len(seed)])
            shuffled = [options[i] for i in order]
            questions.append({
                "question_id": f"video_auto_{index + 1}",
                "prompt": "Theo nội dung video, phát biểu nào đúng?",
                "options": shuffled,
                "correct_answer": correct,
                "explanation": "Đối chiếu phát biểu với đoạn transcript được trích dẫn trong video.",
                "difficulty": "beginner",
                "evidence": [segment.as_dict()],
            })
        if not questions:
            raise ValueError("Không đủ nội dung để tạo câu hỏi trắc nghiệm.")
        self.repository.save_quiz(
            lesson_id=lesson.lesson_id,
            transcript_hash=transcript.transcript_hash,
            questions=questions,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        return questions

    def prepare(self, lesson_id: str, *, source_url: str | None = None, transcript_text: str | None = None,
                language: str = "vi", force_refresh: bool = False) -> VideoAgentPrepareResponse:
        lesson = self._lesson(lesson_id)
        transcript = self._load_transcript(
            lesson, source_url=source_url, transcript_text=transcript_text,
            language=language, force_refresh=force_refresh,
        )
        questions = self._generate_questions(lesson, transcript)
        return VideoAgentPrepareResponse(
            lesson_id=lesson.lesson_id, status="ready", source=transcript.source,
            language=transcript.language, transcript_hash=transcript.transcript_hash,
            segment_count=len(transcript.segments), duration_seconds=transcript.duration_seconds,
            quiz_count=len(questions), warnings=transcript.warnings,
            prepared_at=datetime.now(timezone.utc).isoformat(),
        )

    def status(self, lesson_id: str, *, source_url: str | None = None) -> VideoAgentStatusResponse:
        lesson = self._lesson(lesson_id)
        source_key = self._source_key(source_url, None)
        cached = (
            self.repository.get_transcript(lesson_id=lesson.lesson_id, source_key=source_key)
            if source_url
            else self.repository.get_latest_transcript(lesson_id=lesson.lesson_id)
        )
        if not cached:
            return VideoAgentStatusResponse(lesson_id=lesson.lesson_id, status="not_prepared")
        questions = self.repository.get_quiz(lesson_id=lesson.lesson_id, transcript_hash=cached["transcript_hash"]) or []
        return VideoAgentStatusResponse(
            lesson_id=lesson.lesson_id, status=cached["status"], source=cached["source"],
            language=cached["language"], transcript_hash=cached["transcript_hash"],
            segment_count=len(cached["segments"]), duration_seconds=cached["duration_seconds"],
            quiz_count=len(questions), warnings=tuple(cached.get("warnings", ())), updated_at=cached["updated_at"],
        )

    def create_checkpoint(self, account_id: str, lesson_id: str, *, source_url: str | None = None,
                          current_time_seconds: float = 0) -> VideoAgentCheckpointResponse:
        lesson = self._lesson(lesson_id)
        transcript = self._load_transcript(lesson, source_url=source_url, transcript_text=None, language="vi", force_refresh=False)
        questions = self._generate_questions(lesson, transcript)
        # Prefer a question whose evidence is closest to the current playback
        # position, making the checkpoint test what was just watched.
        def distance(question: dict[str, Any]) -> float:
            evidence = question.get("evidence") or []
            if not evidence:
                return float("inf")
            return abs(float(evidence[0]["start_seconds"]) - current_time_seconds)
        question = min(questions, key=distance)
        checkpoint_id = f"vcp_{uuid4().hex}"
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=15)
        self.repository.save_checkpoint({
            "checkpoint_id": checkpoint_id, "account_id": account_id, "lesson_id": lesson.lesson_id,
            "transcript_hash": transcript.transcript_hash, "question": question,
            "expires_at": expires.isoformat(), "created_at": now.isoformat(),
        })
        return VideoAgentCheckpointResponse(
            checkpoint_id=checkpoint_id, lesson_id=lesson.lesson_id,
            question=VideoAgentQuestionResponse(
                question_id=question["question_id"], prompt=question["prompt"],
                options=tuple(question["options"]), difficulty=question.get("difficulty", "beginner"),
                evidence=_evidence_response(tuple(TranscriptSegment(**s) for s in question.get("evidence", []))),
            ), expires_at=expires.isoformat(),
        )

    @staticmethod
    def _normalize_answer(value: str, options: list[str]) -> str:
        normalized = _clean_text(value).casefold()
        match = re.fullmatch(r"(?:đáp án|option|phương án)?\s*([a-d]|[1-4])", normalized)
        if match:
            token = match.group(1)
            index = ord(token) - ord("a") if token.isalpha() else int(token) - 1
            if 0 <= index < len(options):
                return options[index].casefold()
        return normalized

    def grade(self, account_id: str, checkpoint_id: str, response: str) -> VideoAgentGradeResponse:
        record = self.repository.get_checkpoint(checkpoint_id=checkpoint_id)
        if not record:
            raise ValueError("Không tìm thấy checkpoint video.")
        if record["account_id"] != account_id:
            raise PermissionError("Checkpoint video không thuộc tài khoản hiện tại.")
        try:
            expires = datetime.fromisoformat(record["expires_at"])
        except ValueError as exc:
            raise ValueError("Checkpoint video có thời hạn không hợp lệ.") from exc
        if datetime.now(timezone.utc) > expires:
            raise ValueError("Checkpoint video đã hết hạn.")
        question = record["question"]
        options = list(question["options"])
        passed = self._normalize_answer(response, options) == _clean_text(question["correct_answer"]).casefold()
        evidence = _evidence_response(tuple(TranscriptSegment(**s) for s in question.get("evidence", [])))
        return VideoAgentGradeResponse(
            checkpoint_id=checkpoint_id, lesson_id=record["lesson_id"], passed=passed,
            score=100 if passed else 0,
            feedback="Chính xác. Em đã đối chiếu với transcript của video." if passed else "Chưa chính xác. Hãy xem lại đoạn video được trích dẫn và thử lại.",
            explanation=question.get("explanation", "Đối chiếu lại đoạn transcript được trích dẫn."), evidence=evidence,
        )

    def ask(self, lesson_id: str, *, question: str, source_url: str | None = None,
            current_time_seconds: float = 0, window_seconds: float = 45, language: str = "vi") -> VideoAgentAskResponse:
        lesson = self._lesson(lesson_id)
        transcript = self._load_transcript(lesson, source_url=source_url, transcript_text=None, language=language, force_refresh=False)
        query_tokens = {t.casefold() for t in re.findall(r"[\wÀ-ỹ]{3,}", question)}
        nearby = [s for s in transcript.segments if s.end_seconds >= current_time_seconds - window_seconds and s.start_seconds <= current_time_seconds + window_seconds]
        scored = sorted(
            transcript.segments,
            key=lambda s: len(query_tokens.intersection({t.casefold() for t in re.findall(r"[\wÀ-ỹ]{3,}", s.text)})),
            reverse=True,
        )
        matched = [
            segment
            for segment in scored
            if query_tokens.intersection({token.casefold() for token in re.findall(r"[\wÀ-ỹ]{3,}", segment.text)})
        ]
        relevant = []
        for item in [*matched, *nearby, *scored]:
            if item not in relevant:
                relevant.append(item)
            if len(relevant) >= 3:
                break
        # Only answer when there is lexical support; this is an explicit guard
        # against confident answers to questions outside the video.
        overlap = max(
            (
                len(query_tokens.intersection({token.casefold() for token in re.findall(r"[\wÀ-ỹ]{3,}", segment.text)}))
                for segment in relevant
            ),
            default=0,
        )
        context_cue = any(
            cue in question.casefold()
            for cue in ("đoạn này", "nội dung này", "phần này", "mốc này", "tóm tắt")
        )
        grounded = bool(relevant) and (overlap > 0 or (bool(nearby) and context_cue))
        if grounded:
            answer = "Theo đoạn video liên quan: " + " ".join(s.text for s in relevant[:2])
            limitations = transcript.warnings
        else:
            answer = "Em chưa tìm thấy thông tin đủ rõ trong transcript của video để trả lời câu hỏi này. Anh hãy chỉ rõ mốc thời gian hoặc xem lại phần liên quan nhé."
            limitations = (*transcript.warnings, "Câu hỏi nằm ngoài nội dung transcript hiện có.")
            relevant = []
        citations = tuple(
            VideoAgentCitationResponse(
                segment_id=s.segment_id, start_seconds=s.start_seconds, end_seconds=s.end_seconds,
                label=f"{int(s.start_seconds // 60):02d}:{int(s.start_seconds % 60):02d}", text=s.text,
            ) for s in relevant[:3]
        )
        return VideoAgentAskResponse(lesson_id=lesson.lesson_id, answer=answer, grounded=grounded, citations=citations, limitations=tuple(limitations))
