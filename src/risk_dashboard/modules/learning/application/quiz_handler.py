"""Interactive Quiz Telegram Handler with persistent sessions and deterministic scoring."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import uuid
from typing import Any, Dict, List, Optional

from risk_dashboard.platform.telegram.command_parser import ParsedCommand
from risk_dashboard.platform.telegram.formatter import escape_html, safe_bold, safe_italic
from risk_dashboard.platform.telegram.quiz_repository import QuizSessionRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class QuizQuestion:
    question_id: str
    topic: str
    difficulty: str
    prompt: str
    choices: List[tuple[str, str]]  # e.g. [("A", "10%"), ("B", "20%")]
    correct_choice_id: str
    explanation: str


QUIZ_QUESTION_BANK: Dict[str, QuizQuestion] = {
    "quiz_roe_01": QuizQuestion(
        question_id="quiz_roe_01",
        topic="dinh_gia",
        difficulty="Cơ bản",
        prompt="Doanh nghiệp A đạt Lợi nhuận sau thuế 200 tỷ đồng và Vốn chủ sở hữu trung bình 1,000 tỷ đồng. Chỉ số ROE là bao nhiêu?",
        choices=[("A", "10%"), ("B", "20%"), ("C", "25%"), ("D", "15%")],
        correct_choice_id="B",
        explanation="ROE = (LNST / Vốn CSH) * 100% = (200 / 1000) * 100% = 20%.",
    ),
    "quiz_cfo_01": QuizQuestion(
        question_id="quiz_cfo_01",
        topic="bctc",
        difficulty="Trung cấp",
        prompt="Dấu hiệu nào sau đây cho thấy lợi nhuận của doanh nghiệp có chất lượng dòng tiền thực sự cao?",
        choices=[
            ("A", "Dòng tiền CFO âm liên tục"),
            ("B", "Tỷ lệ CFO / LNST > 1.0"),
            ("C", "Các khoản phải thu tăng vọt"),
            ("D", "Tồn kho gia tăng đột biến"),
        ],
        correct_choice_id="B",
        explanation="Tỷ lệ CFO / LNST > 1.0 cho thấy lợi nhuận báo cáo được chuyển đổi thành tiền mặt thực tế.",
    ),
}


class QuizTelegramHandler:
    def __init__(
        self,
        repository: QuizSessionRepository | None = None,
        questions: Dict[str, QuizQuestion] | None = None,
    ) -> None:
        self.repository = repository or QuizSessionRepository()
        self.questions = questions or QUIZ_QUESTION_BANK

    def handle_command(self, cmd: ParsedCommand) -> tuple[List[str], Optional[Dict[str, Any]]]:
        """Handles /quiz command, creating a new session and returning prompt with inline keyboard."""
        topic_arg: str | None = None
        if cmd.args:
            topic_arg = cmd.args[0].strip().lower()

        # Pick matching question
        matching = [q for q in self.questions.values() if q.topic == topic_arg] if topic_arg else list(self.questions.values())
        if not matching:
            matching = list(self.questions.values())

        question = matching[0]
        session_id = f"q_{uuid.uuid4().hex[:10]}"

        # Save session to persistent repository
        self.repository.create_session(
            session_id=session_id,
            chat_id=cmd.chat_id,
            user_id=cmd.user_id,
            question_id=question.question_id,
            expires_in_seconds=600,
        )

        # Build inline keyboard buttons
        buttons = []
        for choice_id, text in question.choices:
            btn_text = f"[{choice_id}] {text}"
            cb_data = f"quiz:{session_id}:{choice_id}"
            buttons.append({"text": btn_text, "callback_data": cb_data})

        # Format inline keyboard in 2 columns
        keyboard = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
        reply_markup = {"inline_keyboard": keyboard}

        prompt_html = (
            f"❓ {safe_bold('CÂU HỎI TRẮC NGHIỆM TÀI CHÍNH')}\n"
            f"🏷 <i>Chủ đề: {escape_html(question.topic)} · Mức độ: {escape_html(question.difficulty)}</i>\n\n"
            f"{escape_html(question.prompt)}\n\n"
            "<i>Vui lòng chọn đáp án bên dưới:</i>"
        )

        return [prompt_html], reply_markup

    def handle_callback(self, cmd: ParsedCommand) -> List[str]:
        """Handles inline button callback query 'quiz:<session_id>:<choice_id>'."""
        logger.info(f"Quiz handle_callback received: callback_data={cmd.callback_data}, user_id={cmd.user_id}, chat_id={cmd.chat_id}")
        if not cmd.callback_data:
            logger.warning("Callback query missing callback_data")
            return ["⚠️ Callback không hợp lệ."]

        parts = cmd.callback_data.split(":")
        if len(parts) != 3 or parts[0] != "quiz":
            logger.warning(f"Invalid quiz callback_data format: {cmd.callback_data}")
            return ["⚠️ Dữ liệu callback không hợp lệ."]

        _, session_id, choice_id = parts

        # Atomic transaction check
        result_code = self.repository.answer_session_atomically(
            session_id=session_id,
            user_id=cmd.user_id,
            choice_id=choice_id,
        )
        logger.info(f"Quiz session atomic answer result: session_id={session_id}, user_id={cmd.user_id}, choice={choice_id}, result_code={result_code}")

        if result_code == "wrong_user":
            return ["⛔ <b>Bạn không thể trả lời câu hỏi thuộc session của người khác.</b>"]
        if result_code == "already_answered":
            return ["⚠️ <b>Câu hỏi này đã được trả lời trước đó.</b>"]
        if result_code == "expired":
            return ["⌛ <b>Câu hỏi này đã hết hạn (quá 10 phút).</b>"]
        if result_code != "success":
            return ["⚠️ <b>Không tìm thấy phiên trắc nghiệm.</b>"]

        # Fetch session to get question
        session = self.repository.get_session(session_id)
        if not session:
            return ["⚠️ Không tìm thấy phiên trắc nghiệm."]

        question = self.questions.get(session["question_id"])
        if not question:
            return ["⚠️ Không tìm thấy thông tin câu hỏi."]

        is_correct = (choice_id.upper() == question.correct_choice_id.upper())
        status_icon = "✅" if is_correct else "❌"
        status_text = "Chính xác!" if is_correct else f"Chưa chính xác (Đáp án đúng: {question.correct_choice_id})"

        return [
            f"{status_icon} <b>{status_text}</b>\n\n"
            f"💡 <b>Lời giải thích:</b> {escape_html(question.explanation)}"
        ]
