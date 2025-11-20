from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any, Dict, List, Optional

import pytz

from app.config import settings, SESSION_WINDOWS_UTC
from app.services.precision_calculation_service import PrecisionCalculationService

# ---------------------------------------------------------------------------
# In-memory metrics for health / metrics endpoints
# ---------------------------------------------------------------------------

_REPORT_METRICS: Dict[str, Any] = {
    "last_report_generated": None,  # ISO string in UTC
    "last_report_rows": 0,
    "last_report_sessions": 0,
}


def get_report_metrics() -> Dict[str, Any]:
    """
    Return a shallow copy of the last report metrics for diagnostics.
    """
    return dict(_REPORT_METRICS)


# ---------------------------------------------------------------------------
# Helper: is an hour inside the session UTC window?
# ---------------------------------------------------------------------------


def _in_session_window(session_key: str, dt_utc: datetime) -> bool:
    """
    Return True if dt_utc falls inside the configured UTC session window
    for the given session_key (e.g. 'sydney', 'asia', 'london', 'newyork').

    Handles windows that cross midnight (open > close).
    If no window exists, returns True (include everything).
    """
    win = SESSION_WINDOWS_UTC.get(session_key)
    if not win:
        return True

    open_t: time = win["open"]
    close_t: time = win["close"]
    current_t: time = dt_utc.time()

    if open_t < close_t:
        # Simple same-day window
        return open_t <= current_t < close_t
    else:
        # Cross-midnight window: [open, 24h) ∪ [0, close)
        return current_t >= open_t or current_t < close_t


# ---------------------------------------------------------------------------
# Core report generator
# ---------------------------------------------------------------------------


def generate_multi_session_report(
    target_date: date,
    client_tz: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate hourly multi-session report for a given trading date.

    - We iterate 24 local hours for each session's city timezone.
    - Convert each hour to UTC and check if it lies in that session's
      UTC trading window.
    - For each included hour, we call PrecisionCalculationService once.
    """
    # Precision engine (DB is optional for this pure-astro use case)
    precision = PrecisionCalculationService()

    cities = settings.CITIES

    sessions_out: Dict[str, List[Dict[str, Any]]] = {k: [] for k in cities.keys()}
    total_rows = 0

    for session_key, city_cfg in cities.items():
        tz = pytz.timezone(city_cfg["timezone"])
        rows: List[Dict[str, Any]] = []

        for hour in range(24):
            # Naive local datetime for this session hour
            naive_local_dt = datetime.combine(target_date, time(hour, 0))

            # Localize for window filtering and display
            local_dt = tz.localize(naive_local_dt)
            dt_utc = local_dt.astimezone(pytz.UTC)

            # Filter by UTC window
            if not _in_session_window(session_key, dt_utc):
                continue

            # ---- PRECISION ENGINE CALL ----
            # Match the service signature: (city, local_dt)
            signal: Dict[str, Any] = precision.calculate_precise_gold_score(
                city=city_cfg,
                local_dt=naive_local_dt,
            )

            # Base row: session & timestamp meta
            row: Dict[str, Any] = {
                "session": session_key,
                "city": city_cfg["name"],
                "timezone": city_cfg["timezone"],
                "timestamp_local": local_dt.isoformat(),
                # date/time will be overwritten by signal's values if present,
                # which keeps everything consistent with the scoring engine.
                "date": local_dt.date().isoformat(),
                "time": local_dt.strftime("%H:%M"),
                # Explicit fields for the table
                "time_client": local_dt.strftime("%H:%M"),
                "time_utc": dt_utc.strftime("%H:%M"),
            }
            row.update(signal)

            rows.append(row)

        sessions_out[session_key] = rows
        total_rows += len(rows)

    _REPORT_METRICS["last_report_generated"] = datetime.utcnow().isoformat()
    _REPORT_METRICS["last_report_rows"] = int(total_rows)
    _REPORT_METRICS["last_report_sessions"] = int(len(sessions_out))

    return {"date": target_date.isoformat(), "sessions": sessions_out}
