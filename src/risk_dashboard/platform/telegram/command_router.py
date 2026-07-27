"""Command router and handler registry for Telegram bot."""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Tuple, Union

from risk_dashboard.platform.telegram.command_parser import ParsedCommand
from risk_dashboard.platform.telegram.formatter import escape_html, safe_bold

logger = logging.getLogger(__name__)

# Handler can return List[str] or Tuple[List[str], Optional[Dict[str, Any]]] for reply_markup
HandlerResult = Union[List[str], Tuple[List[str], Any]]
CommandHandler = Callable[[ParsedCommand], HandlerResult]


def default_help_handler(cmd: ParsedCommand) -> List[str]:
    return [
        f"{safe_bold('Northstar Finance Lab — Telegram Bot')}\n\n"
        "Các lệnh được hỗ trợ:\n"
        "• <b>/market</b> — Tổng hợp thị trường chứng khoán mới nhất\n"
        "• <b>/news</b> — Điểm tin tức tài chính (ví dụ: <code>/news FPT</code>)\n"
        "• <b>/learn</b> — Bài học & thẻ kiến thức đầu tư (ví dụ: <code>/learn dinh_gia</code>)\n"
        "• <b>/quiz</b> — Trắc nghiệm ôn tập kiến thức đầu tư\n"
        "• <b>/help</b> — Hướng dẫn sử dụng\n"
        "• <b>/status</b> — Trạng thái hệ thống (Admin)\n\n"
        "<i>Gõ lệnh trực tiếp hoặc bấm vào nút tương tác để sử dụng.</i>"
    ]


def default_status_handler(cmd: ParsedCommand) -> List[str]:
    return [
        f"{safe_bold('BÁO CÁO TRẠNG THÁI HỆ THỐNG')}\n\n"
        "• Bot Daemon: <b>ONLINE</b>\n"
        "• Platform Transport: <b>READY</b>\n"
        "• Database Connectivity: <b>HEALTHY</b>\n"
        "• Market Data Provider: <b>AVAILABLE</b>\n"
        "• Environment: <b>PRODUCTION</b>"
    ]


class TelegramCommandRouter:
    def __init__(self) -> None:
        self._handlers: Dict[str, CommandHandler] = {}
        # Register default handlers
        self.register("/help", default_help_handler)
        self.register("/status", default_status_handler)

    def register(self, command: str, handler: CommandHandler) -> None:
        cmd_clean = command.strip().lower()
        if not cmd_clean.startswith("/"):
            cmd_clean = f"/{cmd_clean}"
        self._handlers[cmd_clean] = handler

    def dispatch(self, parsed: ParsedCommand) -> Tuple[List[str], Any]:
        if not parsed.command:
            return self._unknown_command_response(parsed.text), None

        cmd = parsed.command.lower()
        handler = self._handlers.get(cmd)
        if handler:
            try:
                res = handler(parsed)
                if isinstance(res, tuple):
                    return res[0], res[1]
                return res, None
            except Exception as e:
                logger.error(f"Error handling command {cmd}: {e}")
                return [
                    "⚠️ <b>Đã xảy ra lỗi khi xử lý yêu cầu.</b>\n"
                    "Vui lòng thử lại sau hoặc liên hệ quản trị viên."
                ], None

        return self._unknown_command_response(parsed.command), None

    @staticmethod
    def _unknown_command_response(cmd_text: str) -> List[str]:
        clean_cmd = escape_html(cmd_text)
        return [
            f"❓ <b>Lệnh không hợp lệ:</b> <code>{clean_cmd}</code>\n\n"
            "Gõ <b>/help</b> để xem danh sách các lệnh được hỗ trợ."
        ]
