"""Telegram Daily Quiz Bot — entry point."""

import logging
import sys

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from config import BOT_TOKEN
from database import init_db
from handlers.admin_handlers import get_admin_handlers
from handlers.quiz_handlers import get_quiz_handlers
from handlers.user_handlers import help_command, start_command

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

logging.getLogger("httpx").setLevel(logging.WARNING)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Unhandled error: %s", context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ Something went wrong. Please try again in a moment."
        )


def main() -> None:
    init_db()
    logger.info("Starting Daily Quiz Bot...")

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))

    for handler in get_quiz_handlers():
        application.add_handler(handler)

    for handler in get_admin_handlers():
        application.add_handler(handler)

    application.add_error_handler(error_handler)

    logger.info("Handlers registered. Polling...")
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
