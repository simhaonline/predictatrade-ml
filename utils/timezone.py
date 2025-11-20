# app/utils/timezone.py
from datetime import datetime
from zoneinfo import ZoneInfo

def convert_utc_to_tz(dt_utc: datetime, tz: str) -> datetime:
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=ZoneInfo("UTC"))
    return dt_utc.astimezone(ZoneInfo(tz))


def convert_session_to_client(session_local_dt: datetime, session_tz: str, client_tz: str) -> datetime:
    """
    session_local_dt: datetime in session local timezone (e.g. Sydney)
    session_tz:      IANA name of session tz, e.g. 'Australia/Sydney'
    client_tz:       MT5 client timezone, e.g. 'Europe/Zurich'
    """
    local = session_local_dt.replace(tzinfo=ZoneInfo(session_tz))
    return local.astimezone(ZoneInfo(client_tz))
