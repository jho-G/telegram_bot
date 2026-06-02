"""User registration and lookup."""

from database import get_connection, utc_now_iso


def register_user(telegram_id: int, username: str | None, first_name: str | None) -> dict:
    """Insert or update a user; return the user row as a dict."""
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchone()

        if existing:
            conn.execute(
                """
                UPDATE users
                SET username = ?, first_name = ?
                WHERE telegram_id = ?
                """,
                (username, first_name, telegram_id),
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM users WHERE telegram_id = ?",
                (telegram_id,),
            ).fetchone()
            return dict(row)

        conn.execute(
            """
            INSERT INTO users (telegram_id, username, first_name, joined_at)
            VALUES (?, ?, ?, ?)
            """,
            (telegram_id, username, first_name, utc_now_iso()),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchone()
        return dict(row)


def get_user_by_telegram_id(telegram_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchone()
        return dict(row) if row else None


def list_all_users() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM users ORDER BY joined_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]
