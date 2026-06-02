"""Admin commands, menus, and ConversationHandler for adding quizzes."""

import logging

from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from services.admin_service import (
    format_questions_list,
    format_users_list,
    get_recent_results_text,
    get_today_results_text,
)
from services.quiz_service import (
    create_question,
    delete_question,
    get_question,
    list_questions,
    publish_quiz,
    stop_quiz,
)
from services.user_service import list_all_users
from utils.helpers import format_question_preview, require_admin
from utils.keyboards import (
    ADMIN_MENU,
    BACK_TO_ADMIN,
    confirm_delete_keyboard,
    correct_option_keyboard,
    delete_question_keyboard,
)

logger = logging.getLogger(__name__)

# Conversation states for /addquiz
(
    STATE_QUESTION,
    STATE_OPTION_A,
    STATE_OPTION_B,
    STATE_OPTION_C,
    STATE_OPTION_D,
    STATE_CORRECT,
) = range(6)

ADMIN_MENU_TEXT = (
    "🛠 *Admin Panel*\n\n"
    "Manage quizzes from your phone — no coding needed.\n"
    "Choose an option below:"
)


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_admin(update, context):
        return
    if update.message:
        await update.message.reply_text(
            ADMIN_MENU_TEXT,
            reply_markup=ADMIN_MENU,
            parse_mode="Markdown",
        )


async def admin_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()

    if not await require_admin(update, context):
        return

    data = query.data or ""

    if data == "admin:menu":
        await query.edit_message_text(
            ADMIN_MENU_TEXT,
            reply_markup=ADMIN_MENU,
            parse_mode="Markdown",
        )
        return

    if data == "admin:list":
        questions = list_questions()
        text = format_questions_list(questions)
        await query.edit_message_text(
            text, parse_mode="Markdown", reply_markup=BACK_TO_ADMIN
        )
        return

    if data == "admin:delete_menu":
        questions = list_questions()
        if not questions:
            await query.edit_message_text(
                "No questions to delete.",
                reply_markup=BACK_TO_ADMIN,
            )
            return
        await query.edit_message_text(
            "🗑 *Delete Quiz*\n\nSelect a question to delete:",
            parse_mode="Markdown",
            reply_markup=delete_question_keyboard(questions),
        )
        return

    if data.startswith("admin:del:") and not data.startswith("admin:del_confirm"):
        try:
            qid = int(data.split(":")[2])
        except (IndexError, ValueError):
            await query.answer("Invalid selection.", show_alert=True)
            return
        q = get_question(qid)
        if not q:
            await query.answer("Question not found.", show_alert=True)
            return
        await query.edit_message_text(
            format_question_preview(q) + "\n\n⚠️ Delete this question?",
            parse_mode="Markdown",
            reply_markup=confirm_delete_keyboard(qid),
        )
        return

    if data.startswith("admin:del_confirm:"):
        try:
            qid = int(data.split(":")[2])
        except (IndexError, ValueError):
            await query.answer("Invalid selection.", show_alert=True)
            return
        if delete_question(qid):
            await query.edit_message_text(
                f"✅ Question #{qid} deleted.",
                reply_markup=BACK_TO_ADMIN,
            )
        else:
            await query.answer("Could not delete.", show_alert=True)
        return

    if data == "admin:results":
        await query.edit_message_text(
            get_recent_results_text(),
            parse_mode="Markdown",
            reply_markup=BACK_TO_ADMIN,
        )
        return

    if data == "admin:users":
        users = list_all_users()
        await query.edit_message_text(
            format_users_list(users),
            parse_mode="Markdown",
            reply_markup=BACK_TO_ADMIN,
        )
        return

    if data == "admin:publish":
        count = publish_quiz()
        await query.edit_message_text(
            f"📢 *Quiz Published*\n\n{count} question(s) are now active for users.",
            parse_mode="Markdown",
            reply_markup=BACK_TO_ADMIN,
        )
        logger.info("Admin published quiz: %s questions activated", count)
        return

    if data == "admin:stop":
        count = stop_quiz()
        await query.edit_message_text(
            f"🛑 *Quiz Stopped*\n\n{count} question(s) deactivated.",
            parse_mode="Markdown",
            reply_markup=BACK_TO_ADMIN,
        )
        logger.info("Admin stopped quiz: %s questions deactivated", count)
        return


async def results_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_admin(update, context):
        return
    if update.message:
        await update.message.reply_text(
            get_today_results_text(),
            parse_mode="Markdown",
        )


# --- Add quiz conversation ---

async def addquiz_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await require_admin(update, context):
        return ConversationHandler.END

    context.user_data["new_quiz"] = {}
    prompt = "➕ *Add Quiz — Step 1/6*\n\nSend the *question text*:"

    if update.message:
        await update.message.reply_text(prompt, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(prompt, parse_mode="Markdown")
    return STATE_QUESTION


async def addquiz_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (update.message.text or "").strip() if update.message else ""
    if len(text) < 3:
        await update.message.reply_text("Please send a longer question (at least 3 characters).")
        return STATE_QUESTION

    context.user_data["new_quiz"]["question"] = text
    await update.message.reply_text(
        "➕ *Step 2/6*\n\nSend *option A*:",
        parse_mode="Markdown",
    )
    return STATE_OPTION_A


async def addquiz_option_a(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (update.message.text or "").strip() if update.message else ""
    if not text:
        await update.message.reply_text("Option cannot be empty. Send option A:")
        return STATE_OPTION_A

    context.user_data["new_quiz"]["option_a"] = text
    await update.message.reply_text("➕ *Step 3/6*\n\nSend *option B*:", parse_mode="Markdown")
    return STATE_OPTION_B


async def addquiz_option_b(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (update.message.text or "").strip() if update.message else ""
    if not text:
        await update.message.reply_text("Option cannot be empty. Send option B:")
        return STATE_OPTION_B

    context.user_data["new_quiz"]["option_b"] = text
    await update.message.reply_text("➕ *Step 4/6*\n\nSend *option C*:", parse_mode="Markdown")
    return STATE_OPTION_C


async def addquiz_option_c(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (update.message.text or "").strip() if update.message else ""
    if not text:
        await update.message.reply_text("Option cannot be empty. Send option C:")
        return STATE_OPTION_C

    context.user_data["new_quiz"]["option_c"] = text
    await update.message.reply_text("➕ *Step 5/6*\n\nSend *option D*:", parse_mode="Markdown")
    return STATE_OPTION_D


async def addquiz_option_d(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (update.message.text or "").strip() if update.message else ""
    if not text:
        await update.message.reply_text("Option cannot be empty. Send option D:")
        return STATE_OPTION_D

    context.user_data["new_quiz"]["option_d"] = text
    await update.message.reply_text(
        "➕ *Step 6/6*\n\n*Which option is correct?*\nTap a button:",
        parse_mode="Markdown",
        reply_markup=correct_option_keyboard(),
    )
    return STATE_CORRECT


async def addquiz_correct_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not query:
        return STATE_CORRECT

    await query.answer()

    if not await require_admin(update, context):
        return ConversationHandler.END

    data = query.data or ""

    if data == "addquiz:cancel":
        context.user_data.pop("new_quiz", None)
        await query.edit_message_text("❌ Add quiz cancelled.")
        return ConversationHandler.END

    if not data.startswith("addquiz:correct:"):
        return STATE_CORRECT

    try:
        correct = int(data.split(":")[2])
    except (IndexError, ValueError):
        await query.answer("Invalid choice.", show_alert=True)
        return STATE_CORRECT

    if correct not in (1, 2, 3, 4):
        await query.answer("Pick 1, 2, 3, or 4.", show_alert=True)
        return STATE_CORRECT

    quiz_data = context.user_data.get("new_quiz", {})
    required = ("question", "option_a", "option_b", "option_c", "option_d")
    if not all(quiz_data.get(k) for k in required):
        await query.edit_message_text("⚠️ Session expired. Start again with /addquiz")
        context.user_data.pop("new_quiz", None)
        return ConversationHandler.END

    row = create_question(
        question=quiz_data["question"],
        option_a=quiz_data["option_a"],
        option_b=quiz_data["option_b"],
        option_c=quiz_data["option_c"],
        option_d=quiz_data["option_d"],
        correct_option=correct,
    )
    context.user_data.pop("new_quiz", None)

    await query.edit_message_text(
        f"✅ *Question saved!* (#{row['id']})\n\n"
        f"{format_question_preview(row)}\n\n"
        "Use *Publish Quiz* in /admin when ready for users.",
        parse_mode="Markdown",
    )
    logger.info("Admin created question #%s", row["id"])
    return ConversationHandler.END


async def addquiz_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("new_quiz", None)
    if update.message:
        await update.message.reply_text("❌ Add quiz cancelled.")
    return ConversationHandler.END


def build_addquiz_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("addquiz", addquiz_start),
            CallbackQueryHandler(addquiz_start, pattern=r"^admin:addquiz_start$"),
        ],
        states={
            STATE_QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, addquiz_question)
            ],
            STATE_OPTION_A: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, addquiz_option_a)
            ],
            STATE_OPTION_B: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, addquiz_option_b)
            ],
            STATE_OPTION_C: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, addquiz_option_c)
            ],
            STATE_OPTION_D: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, addquiz_option_d)
            ],
            STATE_CORRECT: [
                CallbackQueryHandler(
                    addquiz_correct_callback,
                    pattern=r"^addquiz:(correct:\d|cancel)$",
                )
            ],
        },
        fallbacks=[CommandHandler("cancel", addquiz_cancel)],
        allow_reentry=True,
        name="add_quiz_conversation",
    )


def get_admin_handlers():
    """Return handlers to register in the application."""
    return [
        CommandHandler("admin", admin_command),
        CommandHandler("results", results_command),
        CallbackQueryHandler(
            admin_menu_callback,
            pattern=r"^admin:(?!addquiz_start)",
        ),
        build_addquiz_conversation(),
    ]
