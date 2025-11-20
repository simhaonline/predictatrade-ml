# app/services/time_conversion_service.py

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, date, time, timedelta
from typing import List, Dict, Any, Optional

import pytz

from app.config import settings


@dataclass
class SessionWindow:
    """Represents one session's trading window for a given calendar date."""
    session_key: str
    session_name: str
    session_timezone: str

    local_start: datetime   # session-local start
    local_end: datetime     # session-local end (exclusive)

    utc_start: datetime     # same window in UTC
    utc_end: datetime

    server_timezone: str
    server_start: datetime  # same window in server tz
    server_end: datetime

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # Serialize datetimes to ISO strings for JSON
        for key, value in list(d.items()):
            if isinstance(value, datetime):
                d[key] = value.isoformat()
        return d


class TimeConversionService:
    """
    Helper to normalize session windows and MT5 server timestamps:

    - Normalize everything to UTC
    - Define each session's start/end in UTC for a given calendar date
    - Convert server timestamps -> UTC
    - Filter to "current day's" trading window (no spillover)
    """

    def __init__(self, server_tz: str = "Etc/GMT-2"):
        """
        :param server_tz: MT5 server timezone (IANA style, e.g. 'Etc/GMT-2' or 'Europe/London')
                          NOTE: 'Etc/GMT-2' means UTC+2 (IANA "Etc" zones are inverted).
        """
        self.server_tz_name = server_tz
        try:
            self.server_tz = pytz.timezone(server_tz)
        except Exception:
            raise ValueError(f"Invalid server timezone '{server_tz}'")

    # ------------------------------------------------------------------
    # Core: session windows for a given date
    # ------------------------------------------------------------------
    def build_session_windows(self, target_date: date) -> List[SessionWindow]:
        """
        Build 00:00–24:00 local trading windows for each configured session (Sydney/Tokyo/London/NewYork),
        then project them to UTC and server time.

        :param target_date: calendar date to consider in each session's LOCAL time
        """
        windows: List[SessionWindow] = []

        for key, city_cfg in settings.CITIES.items():
            session_tz = pytz.timezone(city_cfg.timezone)

            # 00:00 local session time for that calendar date
            local_start_naive = datetime.combine(target_date, time(0, 0))
            local_start = session_tz.localize(local_start_naive)
            local_end = local_start + timedelta(days=1)  # exclusive end

            # Convert to UTC
            utc_start = local_start.astimezone(pytz.UTC)
            utc_end = local_end.astimezone(pytz.UTC)

            # Convert to server timezone
            server_start = utc_start.astimezone(self.server_tz)
            server_end = utc_end.astimezone(self.server_tz)

            windows.append(
                SessionWindow(
                    session_key=key,
                    session_name=city_cfg.name,
                    session_timezone=city_cfg.timezone,
                    local_start=local_start,
                    local_end=local_end,
                    utc_start=utc_start,
                    utc_end=utc_end,
                    server_timezone=self.server_tz_name,
                    server_start=server_start,
                    server_end=server_end,
                )
            )

        # Sort by UTC start so you see the real chronological rhythm
        windows.sort(key=lambda w: w.utc_start)
        return windows

    # ------------------------------------------------------------------
    # Normalize a server timestamp -> UTC + session
    # ------------------------------------------------------------------
    def normalize_server_timestamp(
        self,
        ts_server: datetime,
        target_date: date,
    ) -> Optional[Dict[str, Any]]:
        """
        Normalize a MT5 server timestamp:

        - interpret ts_server in server timezone if tz-naive
        - convert to UTC
        - find which session's UTC window it falls into for target_date
        - ignore records that fall outside ANY session window for that date
          (avoid spillover to yesterday/tomorrow)

        :return: dict with utc_time + session info, or None if out-of-range
        """
        # Ensure server-aware datetime
        if ts_server.tzinfo is None:
            ts_server_local = self.server_tz.localize(ts_server)
        else:
            ts_server_local = ts_server.astimezone(self.server_tz)

        ts_utc = ts_server_local.astimezone(pytz.UTC)

        # Build windows once
        windows = self.build_session_windows(target_date)

        for w in windows:
            if w.utc_start <= ts_utc < w.utc_end:
                return {
                    "server_time": ts_server_local.isoformat(),
                    "utc_time": ts_utc.isoformat(),
                    "session_key": w.session_key,
                    "session_name": w.session_name,
                    "session_timezone": w.session_timezone,
                    "session_local_start": w.local_start.isoformat(),
                    "session_local_end": w.local_end.isoformat(),
                    "session_utc_start": w.utc_start.isoformat(),
                    "session_utc_end": w.utc_end.isoformat(),
                }

        # Out-of-range for this day's trading window
        return None

    # ------------------------------------------------------------------
    # Helper for bulk conversion (e.g. OHLC series)
    # ------------------------------------------------------------------
    def map_server_series(
        self,
        timestamps_server: List[datetime],
        target_date: date,
    ) -> List[Dict[str, Any]]:
        """
        Bulk wrapper over normalize_server_timestamp() for an array of timestamps.
        Only entries that fall inside the date's trading windows are returned.
        """
        mapped: List[Dict[str, Any]] = []
        for ts in timestamps_server:
            entry = self.normalize_server_timestamp(ts, target_date)
            if entry is not None:
                mapped.append(entry)
        return mapped
