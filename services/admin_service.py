"""Admin-facing formatting and aggregates."""

from services.quiz_service import get_all_results, get_results_for_date, list_questions
from services.user_service import list_all_users
from utils.helpers import md, today_str


def format_users_list(users: list[dict]) -> str:
    if not users:
        return "👥 No users registered yet."

    lines = ["👥 *Registered Users*\n"]
    for i, u in enumerate(users, 1):
        name = md(u.get("first_name") or "Unknown")
        if u.get("username"):
            username = f"@{md(u['username'])}"
        else:
            username = "no username"
        lines.append(f"{i}. {name} ({username}) — ID `{u['telegram_id']}`")
    lines.append(f"\nTotal: *{len(users)}* users")
    return "\n".join(lines)


def format_questions_list(questions: list[dict]) -> str:
    if not questions:
        return "📋 No quiz questions yet.\n\nUse *Add Quiz* to create one."

    lines = ["📋 *Quiz Questions*\n"]
    for q in questions:
        status = "🟢" if q["is_active"] else "⚪"
        raw = q["question"][:60] + ("…" if len(q["question"]) > 60 else "")
        lines.append(f"{status} #{q['id']}: {md(raw)}")
    lines.append(f"\nTotal: *{len(questions)}* questions")
    active = sum(1 for q in questions if q["is_active"])
    lines.append(f"Active now: *{active}*")
    return "\n".join(lines)


def format_results(results: list[dict], title: str = "Today's Results") -> str:
    if not results:
        return f"📊 *{title}*\n\nNo scores recorded yet."

    lines = [f"📊 *{title}*\n"]
    for i, r in enumerate(results, 1):
        name = md(r.get("first_name") or "User")
        if r.get("username"):
            display = f"{name} @{md(r['username'])}"
        else:
            display = name
        lines.append(
            f"{i}. {display} — *{r['score']}/{r['total']}* ({r['quiz_date']})"
        )
    return "\n".join(lines)


def get_today_results_text() -> str:
    return format_results(get_results_for_date(today_str()), title=f"Results — {today_str()}")


def get_recent_results_text() -> str:
    return format_results(get_all_results(30), title="Recent Results (latest 30)")
