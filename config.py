"""Application configuration loaded from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "quizzes.db"

load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0") or "0")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set. Copy .env.example to .env and add your token.")

if not ADMIN_ID:
    raise ValueError("ADMIN_ID is not set. Add your Telegram user ID to .env.")
