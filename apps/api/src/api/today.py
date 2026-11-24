import time
from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.auth import get_current_user_id
from api.config import USER_TIMEZONE
from api.gmail import fetch_recent_emails
from api.google_oauth import fetch_today_events
from api.llm import model

# ---------------------------------------------------------------------------
# The SHAPE of the "Today" dashboard data.
#
# Gemini receives these classes as a JSON schema and must answer in exactly this
# shape, so we get Python objects back instead of a paragraph we'd have to parse.
# Every Field(description=...) is also sent to Gemini: it's an instruction per field.
# ---------------------------------------------------------------------------


class Priority(BaseModel):
    title: str = Field(description="Short headline, max ~8 words, e.g. 'Card blocked by bank'")
    why: str = Field(description="One sentence: why this needs attention")
    action: str = Field(description="The concrete next step for the user, e.g. 'Call the bank to unblock the card'")
    urgency: Literal["high", "medium", "low"]
    email_id: str = Field(description="The id of the email this came from, copied exactly")


class MeetingPrep(BaseModel):
    title: str = Field(description="What to prepare for, e.g. 'Technical interview'")
    when: str | None = Field(default=None, description="Date/time if known, else null")
    context: str = Field(description="Key facts from the email: role, company, people, format")
    checklist: list[str] = Field(description="3-6 concrete preparation steps tailored to the context")
    email_id: str | None = None


class TodayBrief(BaseModel):
    summary: str = Field(description="2-3 sentences: today's meetings with times, then the most important email items")
    priorities: list[Priority] = Field(description="ONLY emails that need the user's attention or action. Empty if none.")
    prep: list[MeetingPrep] = Field(description="Upcoming events that need preparation: interviews, exams, presentations. Empty if none.")


# ---------------------------------------------------------------------------
# Step D: turn the facts into compact text, then ask Gemini to fill TodayBrief.
# ---------------------------------------------------------------------------


def format_events(events: list[dict]) -> str:
    if not events:
        return "(no events today)"
    lines = []
    for e in events:
        start = e["start"].get("dateTime", e["start"].get("date"))  # all-day events only have "date"
        lines.append(f"- {start} | {e.get('summary', '(no title)')}")
    return "\n".join(lines)


def format_emails(emails: list[dict]) -> str:
    # One line per email with only the useful fields: fewer tokens = faster, cheaper, less distraction.
    if not emails:
        return "(no emails)"
    return "\n".join(
        f"- id={m['id']} | from: {m['from']} | date: {m['date']} | subject: {m['subject']} | snippet: {m['snippet']}"
        for m in emails
    )


BRIEF_INSTRUCTIONS = """You are a personal chief of staff preparing the user's daily dashboard.
Right now it is {now} ({tz}).

TODAY'S CALENDAR:
{events}

EMAILS FROM THE LAST 48 HOURS:
{emails}

Rules:
- priorities: include ONLY emails that need the user to act or decide (payments, deadlines,
  security/bank alerts, replies people are waiting for, interviews, official/visa matters).
  Skip newsletters, marketing, job-board suggestions and FYI notifications. Merge duplicates
  about the same thing into one priority. Order by urgency.
- prep: for interviews, exams, presentations or important meetings mentioned in the emails or
  calendar, give context (role, company, who, format) and a practical checklist tailored to it.
  E.g. a technical interview for a Junior Software Engineer -> data structures, a short project
  walkthrough, questions to ask them.
- summary: start with today's meetings and their times ("No meetings today" if none), then the
  1-2 most important email items. Plain language, no markdown.
- Never invent facts, times or ids that are not in the data above."""


def fetch_or_none(fetch, user_id: str):
    """Runs a fetch function; returns None if that Google account isn't connected.

    A user may have connected Gmail but not Calendar (or neither). The dashboard
    should still work with whatever is connected instead of failing completely.
    """
    try:
        return fetch(user_id)
    except HTTPException as error:
        if error.status_code == 401:
            return None
        raise


def gather_facts(user_id: str) -> tuple[list[dict] | None, list[dict] | None]:
    """The DATA layer: plain code, no AI. None = that account isn't connected."""
    events = fetch_or_none(fetch_today_events, user_id)
    emails = fetch_or_none(fetch_recent_emails, user_id)
    return events, emails


def build_today_brief(events: list[dict] | None, emails: list[dict] | None) -> TodayBrief:
    """The THINKING layer: one Gemini call that turns the facts into a TodayBrief."""
    now = datetime.now(ZoneInfo(USER_TIMEZONE))
    prompt = BRIEF_INSTRUCTIONS.format(
        now=f"{now:%A %d %B %Y, %H:%M}",
        tz=USER_TIMEZONE,
        events=format_events(events) if events is not None else "(Google Calendar not connected)",
        emails=format_emails(emails) if emails is not None else "(Gmail not connected)",
    )

    # The key line: the model MUST answer as a TodayBrief (JSON schema enforced),
    # and LangChain hands us back a Python object.
    structured_model = model.with_structured_output(TodayBrief)
    return structured_model.invoke(prompt)


def ai_error_message(error: Exception) -> str:
    text = str(error)
    if "RESOURCE_EXHAUSTED" in text or "429" in text:
        return "The AI's daily free quota is used up, so priorities and prep aren't available until it resets."
    return "The AI service is busy right now, so priorities and prep aren't available. Try Refresh in a minute."


def fallback_summary(events: list[dict] | None) -> str:
    """A plain summary written by code, for when the AI can't run."""
    if events is None:
        return "Google Calendar isn't connected."
    if not events:
        return "No meetings today."
    times = ", ".join(row["time"] for row in format_schedule(events))
    return f"{len(events)} event(s) today: {times}."


# ---------------------------------------------------------------------------
# Step E: the endpoint, with a cache.
#
# Building a brief takes ~40s (one Gmail request per email + a Gemini call) and
# uses one of the limited free Gemini requests. So we keep each user's last brief
# for CACHE_SECONDS and return it instantly. ?refresh=true skips the cache.
#
# The cache is a plain dict in memory: losing it on restart only costs one
# rebuild. (With several servers it would move to Postgres/Redis.)
# ---------------------------------------------------------------------------

router = APIRouter()

CACHE_SECONDS = 30 * 60
_cache: dict[str, tuple[float, dict]] = {}  # user_id -> (time built, response)


def format_schedule(events: list[dict]) -> list[dict]:
    """Calendar events -> simple rows for the dashboard. Pure code, no AI."""
    schedule = []
    for e in events:
        start = e["start"]
        if "dateTime" in start:
            time = datetime.fromisoformat(start["dateTime"]).astimezone(ZoneInfo(USER_TIMEZONE))
            label = f"{time:%H:%M}"
        else:
            label = "All day"
        schedule.append({"time": label, "title": e.get("summary", "(no title)")})
    return schedule


@router.get("")
def get_today(refresh: bool = False, user_id: str = Depends(get_current_user_id)):
    cached = _cache.get(user_id)
    if cached and not refresh and time.time() - cached[0] < CACHE_SECONDS:
        return cached[1]

    try:
        events, emails = gather_facts(user_id)
    except Exception as error:
        print(f"gather_facts failed: {error!r}")
        raise HTTPException(status_code=503, detail="Couldn't reach Google right now. Try again in a minute.")

    ai_error = None
    if events is None and emails is None:
        # Nothing connected: nothing for the AI to read, so don't spend a Gemini call.
        brief = TodayBrief(summary="Connect Gmail and Google Calendar to see your day here.", priorities=[], prep=[])
    else:
        try:
            brief = build_today_brief(events, emails)
        except Exception as error:
            # Gemini busy (503/504) or out of quota (429). Degrade instead of failing:
            # the code-computed parts (date, meetings, schedule) still work without AI.
            print(f"build_today_brief failed: {error!r}")
            ai_error = ai_error_message(error)
            brief = TodayBrief(summary=fallback_summary(events), priorities=[], prep=[])

    now = datetime.now(ZoneInfo(USER_TIMEZONE))
    response = {
        "generated_at": now.isoformat(),
        "date": f"{now:%A, %d %B %Y}",
        "connected": {"gmail": emails is not None, "calendar": events is not None},
        # Counting is code's job, not the AI's: exact and free.
        "meeting_count": len(events or []),
        "schedule": format_schedule(events or []),
        "ai_error": ai_error,  # None when the AI part worked
        **brief.model_dump(),  # summary, priorities, prep
    }
    # Only cache complete results; after an AI failure the next visit tries again.
    if ai_error is None:
        _cache[user_id] = (time.time(), response)
    return response
