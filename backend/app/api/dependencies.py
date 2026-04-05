from fastapi import Header
from zoneinfo import ZoneInfo

from app.core.timezone import resolve_timezone


def request_timezone(timezone_name: str | None = Header(default=None, alias="X-Timezone")) -> ZoneInfo:
    return resolve_timezone(timezone_name)
