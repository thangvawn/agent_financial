from __future__ import annotations

from dataclasses import dataclass, field
import logging
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ParsedCommand:
    update_id: int
    chat_id: str
    user_id: str
    text: str
    command: str | None
    args: list[str] = field(default_factory=list)
    callback_query_id: str | None = None
    callback_data: str | None = None


def parse_update(update: dict[str, Any]) -> ParsedCommand | None:
    """Extracts chat_id, user_id, command, args, and callback query from Telegram update JSON."""
    update_id = update.get("update_id")
    if update_id is None:
        return None

    # Handle Callback Query (Inline Button Click)
    callback_query = update.get("callback_query")
    if callback_query:
        cb_id = str(callback_query.get("id", ""))
        from_user = callback_query.get("from") or {}
        user_id = str(from_user.get("id", ""))
        msg = callback_query.get("message") or {}
        chat = msg.get("chat") or {}
        chat_id = str(chat.get("id", "")).strip() or user_id
        data = str(callback_query.get("data", "")).strip()
        logger.info(
            f"Parsed CallbackQuery: update_id={update_id}, cb_id={cb_id}, chat_id={chat_id}, user_id={user_id}, data={data}"
        )
        return ParsedCommand(
            update_id=update_id,
            chat_id=chat_id,
            user_id=user_id,
            text=data,
            command="/callback",
            args=[data],
            callback_query_id=cb_id,
            callback_data=data,
        )

    # Handle Normal Text / Message
    message = update.get("message") or update.get("edited_message")
    if not message:
        return None

    chat = message.get("chat") or {}
    chat_id = str(chat.get("id", ""))
    from_user = message.get("from") or {}
    user_id = str(from_user.get("id", ""))
    text = str(message.get("text", "")).strip()

    if not text:
        return ParsedCommand(
            update_id=update_id,
            chat_id=chat_id,
            user_id=user_id,
            text="",
            command=None,
            args=[],
        )

    parts = text.split()
    first_word = parts[0] if parts else ""

    if first_word.startswith("/"):
        # Handle slash command, e.g. /market@botname -> /market
        cmd_raw = first_word.split("@")[0].lower()
        args = parts[1:]
        return ParsedCommand(
            update_id=update_id,
            chat_id=chat_id,
            user_id=user_id,
            text=text,
            command=cmd_raw,
            args=args,
        )

    return ParsedCommand(
        update_id=update_id,
        chat_id=chat_id,
        user_id=user_id,
        text=text,
        command=None,
        args=[],
    )
