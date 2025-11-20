# app/services/planetary_events_service.py

from datetime import datetime, timedelta, date
from typing import List, Dict, Any

import pytz

from app.services.astro_core import AstroCore


class PlanetaryEventsService:
    """
    Scan a given date for time-stamped changes in planetary states:
      - sign change
      - nakshatra change
      - pada change
      - retrograde ↔ direct
      - combustion on/off
    """

    def __init__(self, step_minutes: int = 5):
        self.core = AstroCore()
        self.step_minutes = step_minutes

    def scan_day(
        self, target_date: date, timezone_str: str = "UTC"
    ) -> List[Dict[str, Any]]:
        tz = pytz.timezone(timezone_str)
        start_local = tz.localize(datetime.combine(target_date, datetime.min.time()))
        end_local = start_local + timedelta(days=1)

        prev_state: Dict[str, Dict[str, Any]] = {}
        events: List[Dict[str, Any]] = []

        t = start_local
        while t < end_local:
            positions = self.core.get_sidereal_positions(t)

            for name, p in positions.items():
                state = {
                    "sign": p["sign"],
                    "nakshatra": p["nakshatra"],
                    "pada": p["pada"],
                    "retrograde": bool(p.get("retrograde", False)),
                    "combustion": bool(p.get("combustion", False)),
                }

                if name in prev_state:
                    prev = prev_state[name]
                    changed_keys = [k for k in state if state[k] != prev[k]]
                    if changed_keys:
                        events.append(
                            {
                                "timestamp_local": t.isoformat(),
                                "planet": name,
                                "changed": changed_keys,
                                "from": prev,
                                "to": state,
                            }
                        )

                prev_state[name] = state

            t += timedelta(minutes=self.step_minutes)

        return events
