"""Handlers for regular users."""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from services.user_service import register_user

logger = logging.getLogger(__name__)

WELCOME_TEXT = (
    "👋 Welcome to the *Daily Quiz Bot*!\n\n"
    "Test your knowledge with today's quiz.\n\n"
    "📌 *Commands*\n"
    "/quiz — Start today's quiz\n"
    "/help — Show help\n\n"
    "Good luck! 🍀"
)

HELP_TEXT = (
    "ℹ️ *Help*\n\n"
    "/start — Register and see welcome message\n"
    "/quiz — Take today's active quiz (one attempt per day)\n"
    "/help — Show this message\n\n"
    "Answer each question using the buttons below the message."
)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return

    register_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
    )
    logger.info("User registered/updated: %s (%s)", user.id, user.username)

    if update.message:
        await update.message.reply_text(WELCOME_TEXT, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")
