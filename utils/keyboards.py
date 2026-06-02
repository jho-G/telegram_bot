"""Inline and reply keyboard builders."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from utils.helpers import OPTION_LABELS

# Admin menu
ADMIN_MENU = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("➕ Add Quiz", callback_data="admin:addquiz_start"),
            InlineKeyboardButton("📋 List Quizzes", callback_data="admin:list"),
        ],
        [
            InlineKeyboardButton("🗑 Delete Quiz", callback_data="admin:delete_menu"),
            InlineKeyboardButton("📊 View Results", callback_data="admin:results"),
        ],
        [
            InlineKeyboardButton("👥 View Users", callback_data="admin:users"),
            InlineKeyboardButton("📢 Publish Quiz", callback_data="admin:publish"),
        ],
        [InlineKeyboardButton("🛑 Stop Quiz", callback_data="admin:stop")],
    ]
)

BACK_TO_ADMIN = InlineKeyboardMarkup(
    [[InlineKeyboardButton("◀️ Admin Menu", callback_data="admin:menu")]]
)


def correct_option_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for admin to pick the correct answer (1–4)."""
    buttons = [
        [
            InlineKeyboardButton("1 — A", callback_data="addquiz:correct:1"),
            InlineKeyboardButton("2 — B", callback_data="addquiz:correct:2"),
        ],
        [
            InlineKeyboardButton("3 — C", callback_data="addquiz:correct:3"),
            InlineKeyboardButton("4 — D", callback_data="addquiz:correct:4"),
        ],
        [InlineKeyboardButton("❌ Cancel", callback_data="addquiz:cancel")],
    ]
    return InlineKeyboardMarkup(buttons)


def quiz_answer_keyboard(question_id: int) -> InlineKeyboardMarkup:
    """Inline options A–D for a quiz question."""
    buttons = [
        [
            InlineKeyboardButton("A", callback_data=f"quiz:ans:{question_id}:1"),
            InlineKeyboardButton("B", callback_data=f"quiz:ans:{question_id}:2"),
        ],
        [
            InlineKeyboardButton("C", callback_data=f"quiz:ans:{question_id}:3"),
            InlineKeyboardButton("D", callback_data=f"quiz:ans:{question_id}:4"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def delete_question_keyboard(questions: list[dict]) -> InlineKeyboardMarkup:
    """One button per question for deletion."""
    rows = []
    for q in questions[:20]:
        label = f"#{q['id']} {q['question'][:40]}{'…' if len(q['question']) > 40 else ''}"
        rows.append(
            [InlineKeyboardButton(label, callback_data=f"admin:del:{q['id']}")]
        )
    rows.append([InlineKeyboardButton("◀️ Back", callback_data="admin:menu")])
    return InlineKeyboardMarkup(rows)


def confirm_delete_keyboard(question_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Yes, delete", callback_data=f"admin:del_confirm:{question_id}"),
                InlineKeyboardButton("❌ Cancel", callback_data="admin:delete_menu"),
            ]
        ]
    )
