# app/services/dasha_service.py
from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.services.astro_core import AstroCore

VIM_LORDS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
VIM_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]

class DashaService:
    """Framework for Vimshottari / Shodshottari / Ashtottari / Shashti-Hayani."""
    def __init__(self):
        self.core = AstroCore()

    def current_vimshottari(self, birth_dt: datetime, natal_moon_long: float, now: datetime) -> Dict[str, Any]:
        timeline = self._vimshottari_timeline(birth_dt, natal_moon_long, years=120)
        for block in timeline:
            if block["start"] <= now <= block["end"]:
                return block
        return {}

    def _vimshottari_timeline(self, birth_dt: datetime, natal_moon_long: float, years: int = 120) -> List[Dict[str, Any]]:
        nak = self.core._nakshatra_from_long(natal_moon_long)
        lord_index = nak["index"] % 9

        length = 360.0 / 27.0
        offset_in_nak = natal_moon_long % length
        remaining_fraction = (length - offset_in_nak) / length

        lords = VIM_LORDS[lord_index:] + VIM_LORDS[:lord_index]
        years_seq = VIM_YEARS[lord_index:] + VIM_YEARS[:lord_index]

        timeline: List[Dict[str, Any]] = []
        cursor = birth_dt

        first_years = years_seq[0] * remaining_fraction
        first_end = cursor + timedelta(days=first_years * 365.25)
        timeline.append({"lord": lords[0], "start": cursor, "end": first_end, "system": "Vimshottari"})
        cursor = first_end

        for lord, yrs in zip(lords[1:], years_seq[1:]):
            d_end = cursor + timedelta(days=yrs * 365.25)
            timeline.append({"lord": lord, "start": cursor, "end": d_end, "system": "Vimshottari"})
            cursor = d_end
            if (cursor - birth_dt).days / 365.25 > years:
                break

        return timeline
