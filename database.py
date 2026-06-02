"""SQLite database initialization and connection helpers."""

import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from config import DB_PATH, DATA_DIR

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL UNIQUE,
    username TEXT,
    first_name TEXT,
    joined_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    correct_option INTEGER NOT NULL CHECK (correct_option BETWEEN 1 AND 4),
    is_active INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    selected_option INTEGER NOT NULL CHECK (selected_option BETWEEN 1 AND 4),
    is_correct INTEGER NOT NULL DEFAULT 0,
    answered_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    UNIQUE (user_id, question_id)
);

CREATE TABLE IF NOT EXISTS scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    score INTEGER NOT NULL,
    total INTEGER NOT NULL,
    quiz_date TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE (user_id, quiz_date)
);

CREATE INDEX IF NOT EXISTS idx_questions_active ON questions(is_active);
CREATE INDEX IF NOT EXISTS idx_scores_date ON scores(quiz_date);
CREATE INDEX IF NOT EXISTS idx_answers_user ON answers(user_id);
"""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db() -> None:
    """Create data directory and database tables if they do not exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.executescript(SCHEMA)
        conn.commit()
    logger.info("Database initialized at %s", DB_PATH)


@contextmanager
def get_connection():
    """Yield a SQLite connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()
