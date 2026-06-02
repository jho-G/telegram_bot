"""Quiz questions, answers, scores, and daily quiz logic."""

from database import get_connection, utc_now_iso
from utils.helpers import today_str


def create_question(
    question: str,
    option_a: str,
    option_b: str,
    option_c: str,
    option_d: str,
    correct_option: int,
) -> dict:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO questions (
                question, option_a, option_b, option_c, option_d,
                correct_option, is_active, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, 0, ?)
            """,
            (
                question.strip(),
                option_a.strip(),
                option_b.strip(),
                option_c.strip(),
                option_d.strip(),
                correct_option,
                utc_now_iso(),
            ),
        )
        conn.commit()
        qid = cursor.lastrowid
        row = conn.execute("SELECT * FROM questions WHERE id = ?", (qid,)).fetchone()
        return dict(row)


def list_questions(active_only: bool = False) -> list[dict]:
    with get_connection() as conn:
        if active_only:
            rows = conn.execute(
                "SELECT * FROM questions WHERE is_active = 1 ORDER BY id ASC"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM questions ORDER BY id DESC"
            ).fetchall()
        return [dict(r) for r in rows]


def get_question(question_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM questions WHERE id = ?", (question_id,)
        ).fetchone()
        return dict(row) if row else None


def delete_question(question_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM questions WHERE id = ?", (question_id,))
        conn.commit()
        return cursor.rowcount > 0


def publish_quiz() -> int:
    """Activate all draft questions. Returns count activated."""
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE questions SET is_active = 1 WHERE is_active = 0"
        )
        conn.commit()
        return cursor.rowcount


def stop_quiz() -> int:
    """Deactivate all active questions. Returns count deactivated."""
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE questions SET is_active = 0 WHERE is_active = 1"
        )
        conn.commit()
        return cursor.rowcount


def get_active_questions() -> list[dict]:
    return list_questions(active_only=True)


def user_completed_quiz_today(user_id: int, quiz_date: str | None = None) -> bool:
    quiz_date = quiz_date or today_str()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM scores WHERE user_id = ? AND quiz_date = ?",
            (user_id, quiz_date),
        ).fetchone()
        return row is not None


def get_user_score_today(user_id: int, quiz_date: str | None = None) -> dict | None:
    quiz_date = quiz_date or today_str()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM scores WHERE user_id = ? AND quiz_date = ?",
            (user_id, quiz_date),
        ).fetchone()
        return dict(row) if row else None


def save_answer(
    user_id: int,
    question_id: int,
    selected_option: int,
    is_correct: bool,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO answers (user_id, question_id, selected_option, is_correct, answered_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, question_id) DO UPDATE SET
                selected_option = excluded.selected_option,
                is_correct = excluded.is_correct,
                answered_at = excluded.answered_at
            """,
            (user_id, question_id, selected_option, int(is_correct), utc_now_iso()),
        )
        conn.commit()


def was_answer_correct(user_id: int, question_id: int) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT is_correct FROM answers WHERE user_id = ? AND question_id = ?",
            (user_id, question_id),
        ).fetchone()
    return bool(row and row["is_correct"])


def user_answered_question(user_id: int, question_id: int) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM answers WHERE user_id = ? AND question_id = ?",
            (user_id, question_id),
        ).fetchone()
        return row is not None


def save_final_score(user_id: int, score: int, total: int, quiz_date: str | None = None) -> None:
    quiz_date = quiz_date or today_str()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO scores (user_id, score, total, quiz_date)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, quiz_date) DO UPDATE SET
                score = excluded.score,
                total = excluded.total
            """,
            (user_id, score, total, quiz_date),
        )
        conn.commit()


def get_results_for_date(quiz_date: str | None = None) -> list[dict]:
    """Return scores joined with user info, highest score first."""
    quiz_date = quiz_date or today_str()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT s.score, s.total, s.quiz_date,
                   u.username, u.first_name, u.telegram_id
            FROM scores s
            JOIN users u ON u.id = s.user_id
            WHERE s.quiz_date = ?
            ORDER BY s.score DESC, s.total DESC
            """,
            (quiz_date,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_all_results(limit: int = 50) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT s.score, s.total, s.quiz_date,
                   u.username, u.first_name, u.telegram_id
            FROM scores s
            JOIN users u ON u.id = s.user_id
            ORDER BY s.quiz_date DESC, s.score DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
