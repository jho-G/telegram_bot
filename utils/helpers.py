"""Shared helper utilities."""

import logging
from datetime import date, datetime, timezone

from telegram import Update
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

from config import ADMIN_ID

logger = logging.getLogger(__name__)

OPTION_LABELS = {1: "A", 2: "B", 3: "C", 4: "D"}


def md(text: str | None) -> str:
    """Escape user-provided text for Telegram legacy Markdown messages."""
    return escape_markdown(str(text) if text is not None else "", version=1)


def today_str() -> str:
    """Return today's date as YYYY-MM-DD (UTC)."""
    return datetime.now(timezone.utc).date().isoformat()


def is_admin(user_id: int | None) -> bool:
    return user_id is not None and user_id == ADMIN_ID


async def require_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Return True if the caller is the configured admin; otherwise reply and return False."""
    user = update.effective_user
    if not user or not is_admin(user.id):
        message = update.effective_message
        if message:
            await message.reply_text("⛔ This command is for admins only.")
        elif update.callback_query:
            await update.callback_query.answer("Admins only.", show_alert=True)
        return False
    return True


def format_option(index: int, text: str) -> str:
    label = OPTION_LABELS.get(index, str(index))
    return f"{label}. {md(text)}"


def format_question_preview(row: dict) -> str:
    lines = [
        f"📝 *Question #{row['id']}*",
        "",
        md(row["question"]),
        "",
        format_option(1, row["option_a"]),
        format_option(2, row["option_b"]),
        format_option(3, row["option_c"]),
        format_option(4, row["option_d"]),
        "",
        f"✅ Correct: {OPTION_LABELS[row['correct_option']]}",
        f"Status: {'🟢 Active' if row['is_active'] else '⚪ Draft'}",
    ]
    return "\n".join(lines)


def parse_callback_parts(data: str, expected_prefix: str, min_parts: int) -> list[str] | None:
    """
    Validate callback data format: prefix:part1:part2...
    Returns parts after prefix or None if invalid.
    """
    if not data or not data.startswith(expected_prefix + ":"):
        return None
    parts = data.split(":")
    if len(parts) < min_parts:
        return None
    return parts
