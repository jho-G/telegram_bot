"""User quiz flow: /quiz command and answer callbacks."""

import logging

from telegram import Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from services.quiz_service import (
    get_active_questions,
    get_user_score_today,
    save_answer,
    save_final_score,
    user_answered_question,
    user_completed_quiz_today,
    was_answer_correct,
)
from services.user_service import get_user_by_telegram_id, register_user
from utils.helpers import format_option, md, today_str
from utils.keyboards import quiz_answer_keyboard

logger = logging.getLogger(__name__)

QUIZ_KEY = "quiz_session"


def _build_session(questions: list[dict]) -> dict:
    return {
        "question_ids": [q["id"] for q in questions],
        "index": 0,
        "score": 0,
        "total": len(questions),
        "date": today_str(),
    }


async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or not update.message:
        return

    db_user = get_user_by_telegram_id(user.id)
    if not db_user:
        db_user = register_user(user.id, user.username, user.first_name)

    if user_completed_quiz_today(db_user["id"]):
        existing = get_user_score_today(db_user["id"])
        score = existing["score"] if existing else 0
        total = existing["total"] if existing else 0
        await update.message.reply_text(
            f"✅ You already completed today's quiz.\n\n"
            f"Your score: *{score}/{total}*",
            parse_mode="Markdown",
        )
        return

    questions = get_active_questions()
    if not questions:
        await update.message.reply_text(
            "📭 No active quiz right now.\n\n"
            "Check back later when the admin publishes a quiz."
        )
        return

    # Resume if user already answered some questions today (e.g. after bot restart)
    remaining = [q for q in questions if not user_answered_question(db_user["id"], q["id"])]
    if not remaining:
        score = sum(
            1
            for q in questions
            if was_answer_correct(db_user["id"], q["id"])
        )
        total = len(questions)
        save_final_score(db_user["id"], score, total, today_str())
        await update.message.reply_text(
            f"✅ Quiz already completed.\n\nYour score: *{score}/{total}*",
            parse_mode="Markdown",
        )
        return

    answered_count = len(questions) - len(remaining)
    session = _build_session(questions)
    session["index"] = answered_count
    session["score"] = sum(
        1
        for q in questions
        if user_answered_question(db_user["id"], q["id"])
        and was_answer_correct(db_user["id"], q["id"])
    )
    context.user_data[QUIZ_KEY] = session
    await _send_current_question(update, context, db_user["id"])


async def _send_current_question(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
) -> None:
    session = context.user_data.get(QUIZ_KEY)
    if not session:
        return

    qids = session["question_ids"]
    idx = session["index"]

    if idx >= len(qids):
        await _finish_quiz(update, context, user_id)
        return

    from services.quiz_service import get_question

    question = get_question(qids[idx])
    if not question:
        session["index"] += 1
        await _send_current_question(update, context, user_id)
        return

    total = session["total"]
    num = idx + 1
    text = (
        f"❓ *Question {num} of {total}*\n\n"
        f"{md(question['question'])}\n\n"
        f"{format_option(1, question['option_a'])}\n"
        f"{format_option(2, question['option_b'])}\n"
        f"{format_option(3, question['option_c'])}\n"
        f"{format_option(4, question['option_d'])}\n\n"
        "_Tap your answer below._"
    )

    chat_id = update.effective_chat.id if update.effective_chat else None
    message = update.effective_message

    if message:
        await message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=quiz_answer_keyboard(question["id"]),
        )
    elif update.callback_query and chat_id:
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=quiz_answer_keyboard(question["id"]),
        )


async def quiz_answer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return

    user = update.effective_user
    if not user:
        return

    data = query.data or ""
    if not data.startswith("quiz:ans:"):
        return

    parts = data.split(":")
    if len(parts) != 4:
        await query.answer("Invalid answer.", show_alert=True)
        return

    try:
        question_id = int(parts[2])
        selected = int(parts[3])
    except ValueError:
        await query.answer("Invalid answer.", show_alert=True)
        return

    if selected not in (1, 2, 3, 4):
        await query.answer("Invalid option.", show_alert=True)
        return

    await query.answer()

    db_user = get_user_by_telegram_id(user.id)
    if not db_user:
        db_user = register_user(user.id, user.username, user.first_name)

    if user_completed_quiz_today(db_user["id"]):
        await query.edit_message_text("You already finished today's quiz.")
        context.user_data.pop(QUIZ_KEY, None)
        return

    session = context.user_data.get(QUIZ_KEY)
    if not session:
        await query.edit_message_text(
            "Session expired. Send /quiz to start again."
        )
        return

    qids = session["question_ids"]
    idx = session["index"]

    if idx >= len(qids) or qids[idx] != question_id:
        await query.edit_message_text("This question is no longer active. Send /quiz.")
        return

    if user_answered_question(db_user["id"], question_id):
        await query.edit_message_text("You already answered this question.")
        return

    from services.quiz_service import get_question

    question = get_question(question_id)
    if not question:
        await query.edit_message_text("Question not found.")
        return

    is_correct = selected == question["correct_option"]
    save_answer(db_user["id"], question_id, selected, is_correct)

    if is_correct:
        session["score"] += 1

    feedback = "✅ Correct!" if is_correct else "❌ Wrong."
    await query.edit_message_text(
        f"{query.message.text}\n\n{feedback}",
        parse_mode="Markdown",
    )

    session["index"] += 1
    context.user_data[QUIZ_KEY] = session

    # Send next question or finish
    if session["index"] < session["total"]:
        await _send_current_question(update, context, db_user["id"])
    else:
        await _finish_quiz(update, context, db_user["id"])


async def _finish_quiz(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
) -> None:
    session = context.user_data.pop(QUIZ_KEY, None)
    if not session:
        return

    score = session["score"]
    total = session["total"]
    quiz_date = session["date"]

    save_final_score(user_id, score, total, quiz_date)

    pct = int((score / total) * 100) if total else 0
    emoji = "🏆" if pct >= 80 else "👍" if pct >= 50 else "📚"

    text = (
        f"{emoji} *Quiz Complete!*\n\n"
        f"Your score: *{score} / {total}* ({pct}%)\n\n"
        "Come back tomorrow for a new quiz!"
    )

    chat_id = update.effective_chat.id if update.effective_chat else None
    if update.callback_query and chat_id:
        await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
    elif update.message:
        await update.message.reply_text(text, parse_mode="Markdown")

    logger.info("User %s finished quiz: %s/%s", user_id, score, total)


def get_quiz_handlers():
    return [
        CommandHandler("quiz", quiz_command),
        CallbackQueryHandler(quiz_answer_callback, pattern=r"^quiz:ans:"),
    ]
