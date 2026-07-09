"""Date/time utilities: utc_now() for naive UTC timestamps, DatetimeUTCStr for API serialization."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Annotated

from pydantic import PlainSerializer


# Project-wide standard for getting current timestamp: naive UTC, truncated to seconds
# (matches the YYYY-MM-DD HH:MM:SS serialization + Postgres TIMESTAMP(precision=0); keeps
# raw SQLite storage second-precise too, since SQLite ignores the precision variant).
def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


# Project-wide standard for getting current date (no time component).
def utc_today() -> date:
    return datetime.now(timezone.utc).date()


AGENT_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'


def datetime_to_agent(value: datetime) -> str:
    """Boundary out (DB → agent / API): datetime → "YYYY-MM-DD HH:MM:SS" (naive UTC, no offset).

    An aware value is first converted to UTC and stripped of tzinfo, so neither the agent
    nor Luxon on the frontend misreads a bare timestamp as local time.
    """
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value.strftime(AGENT_DATETIME_FORMAT)


def datetime_from_agent(value: str) -> datetime:
    """Boundary in (agent → DB): "YYYY-MM-DD HH:MM:SS" → naive UTC datetime (second precision)."""
    return datetime.strptime(value, AGENT_DATETIME_FORMAT)


# Pydantic field type: serializes datetime → "YYYY-MM-DD HH:MM:SS" (naive UTC, no offset).
# Prevents Luxon from misreading bare timestamps as local time on the frontend.
DatetimeUTCStr = Annotated[datetime, PlainSerializer(datetime_to_agent, return_type=str)]


__all__ = [
    "utc_now",
    "utc_today",
    "AGENT_DATETIME_FORMAT",
    "datetime_to_agent",
    "datetime_from_agent",
    "DatetimeUTCStr",
]
