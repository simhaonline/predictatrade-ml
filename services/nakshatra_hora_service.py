# app/services/nakshatra_hora_service.py
from datetime import datetime, timedelta, date
from typing import Dict, List, Any
import pytz

from sqlalchemy.orm import Session

from app.services.astro_core import AstroCore
from app.services.precision_calculation_service import PrecisionCalculationService
from app.config import settings

class NakshatraHoraService:
    def __init__(self, db: Session):
        self.db = db
        self.core = AstroCore()
        self.precision = PrecisionCalculationService(db)

    def build_hora_calendar(self, city: Dict[str, Any], target_date: date) -> List[Dict[str, Any]]:
        tz = pytz.timezone(city["timezone"])
        rows: List[Dict[str, Any]] = []

        for hour in range(24):
            local_dt = tz.localize(
                datetime.combine(target_date, datetime.min.time()) + timedelta(hours=hour)
            )
            signal = self.precision.calculate_precise_gold_score(city, local_dt.replace(tzinfo=None))

            rows.append({
                "hour": hour,
                "timestamp_local": local_dt.isoformat(),
                "hora_ruler": signal["hora_ruler"],
                "hora_effect": signal["hora_effect"],
                "contamination_index": signal["contamination_index"],
                "nakshatra": signal["nakshatra_pada"].split("-")[0],
                "pada": int(signal["nakshatra_pada"].split("-")[1]),
                "gold_signal_score": signal["gold_signal_score"],
                "trade_recommendation": signal["trade_recommendation"],
            })
        return rows

    def get_moon_nakshatra_pada(self, dt: datetime) -> Dict[str, Any]:
        positions = self.core.get_sidereal_positions(dt)
        moon = positions["Moon"]
        return {
            "nakshatra": moon["nakshatra"],
            "pada": moon["pada"],
            "longitude": moon["longitude"],
            "sign": moon["sign"],
        }
