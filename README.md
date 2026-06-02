# Telegram Daily Quiz Bot

A production-style Telegram quiz bot for a **non-technical admin**. Everything is managed from Telegram on a mobile phone — no JSON files, no code editing.

## Features

- **Admin** (`/admin`): Add, list, delete, publish, and stop quizzes; view users and results
- **Users** (`/start`, `/quiz`): Register, take today's quiz one question at a time, get automatic grading
- **SQLite** storage for users, questions, answers, and daily scores
- **One attempt per day** per user

## Project structure

```
quiz_bot/
├── bot.py
├── config.py
├── database.py
├── requirements.txt
├── .env.example
├── handlers/
├── services/
├── utils/
└── data/
    └── quizzes.db   (created on first run)
```

## Setup

### 1. Prerequisites

- Python 3.10 or newer
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- Your Telegram user ID (message [@userinfobot](https://t.me/userinfobot))

### 2. Install dependencies

```bash
cd quiz_bot
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure environment

```bash
copy .env.example .env
```

Edit `.env` and set:

- `BOT_TOKEN` — from BotFather
- `ADMIN_ID` — your numeric Telegram user ID

### 4. Run the bot

```bash
python bot.py
```

You should see `Starting Daily Quiz Bot...` and `Handlers registered. Polling...`

## Admin guide (mobile)

| Command / action | What it does |
|------------------|--------------|
| `/admin` | Open admin menu (inline buttons) |
| `/addquiz` | Add a question step-by-step |
| `/results` | Today's scores (highest first) |
| `/cancel` | Cancel add-quiz flow |

**Typical workflow**

1. `/addquiz` — enter question, options A–D, tap correct answer
2. Repeat for more questions
3. `/admin` → **Publish Quiz** — makes questions live for users
4. Users use `/quiz`
5. `/admin` → **View Results** or `/results`
6. **Stop Quiz** when the day is over

## User commands

| Command | Description |
|---------|-------------|
| `/start` | Register and welcome message |
| `/quiz` | Start today's active quiz |
| `/help` | Help text |

## Security

- Secrets live only in `.env` (never commit `.env`)
- Only `ADMIN_ID` can use admin commands and callbacks
- Callback data is validated before processing

## Troubleshooting

- **Bot doesn't respond**: Check `BOT_TOKEN` and that `python bot.py` is running
- **Admin commands blocked**: Verify `ADMIN_ID` matches your Telegram ID exactly
- **No quiz for users**: Add questions with `/addquiz`, then **Publish Quiz** from `/admin`

## License

MIT — use freely for learning and client projects.
