# app/services/fear_apocalypse_service.py
from datetime import datetime, timedelta
from typing import Dict, Any, List

from sqlalchemy.orm import Session

from app.services.astro_core import AstroCore
from app.models import RetrogradeCycle, EclipseEvent, ObsessionGap

class FearApocalypseService:
    def __init__(self, db: Session):
        self.db = db
        self.core = AstroCore()

    def get_fear_and_transit(self, dt: datetime) -> Dict[str, Any]:
        fear_profile = self.core.get_fear_profile(dt)
        saturn_rx = self._get_active_saturn_retrograde(dt)
        eclipses = self._get_active_eclipse_window(dt)
        gaps = self._get_active_obsession_gaps(dt)

        apocalypse_trigger = any(g.god_tier for g in gaps) and bool(eclipses)

        return {
            "fear_profile": fear_profile,
            "saturn_retrograde_active": saturn_rx is not None,
            "saturn_retrograde_window": self._retrograde_to_dict(saturn_rx),
            "eclipse_window": [self._eclipse_to_dict(e) for e in eclipses],
            "active_obsession_gaps": [self._gap_to_dict(g) for g in gaps],
            "apocalypse_trigger": apocalypse_trigger,
        }

    def _get_active_saturn_retrograde(self, dt: datetime):
        return self.db.query(RetrogradeCycle).filter(
            RetrogradeCycle.planet == "Saturn",
            RetrogradeCycle.is_active == True,
            RetrogradeCycle.start_date <= dt,
            RetrogradeCycle.end_date >= dt,
        ).first()

    def _get_active_eclipse_window(self, dt: datetime) -> List[EclipseEvent]:
        window_start = dt - timedelta(days=14)
        window_end = dt + timedelta(days=14)
        return self.db.query(EclipseEvent).filter(
            EclipseEvent.is_active == True,
            EclipseEvent.date_utc.between(window_start, window_end),
        ).all()

    def _get_active_obsession_gaps(self, dt: datetime) -> List[ObsessionGap]:
        window_start = dt - timedelta(hours=4)
        window_end = dt + timedelta(hours=4)
        return self.db.query(ObsessionGap).filter(
            ObsessionGap.is_active == True,
            ObsessionGap.trigger_date.between(window_start, window_end),
        ).all()

    @staticmethod
    def _retrograde_to_dict(rx: RetrogradeCycle):
        if not rx:
            return None
        return {
            "planet": rx.planet,
            "start": rx.start_date.isoformat(),
            "end": rx.end_date.isoformat(),
            "sign": rx.sign,
            "duration_days": rx.duration_days,
            "shadow_period_weeks": rx.shadow_period_weeks,
            "obsession_gap_type": rx.obsession_gap_type,
        }

    @staticmethod
    def _eclipse_to_dict(e: EclipseEvent):
        return {
            "date_utc": e.date_utc.isoformat(),
            "eclipse_type": e.eclipse_type,
            "degree_sign": e.degree_sign,
            "gamma": e.gamma,
            "saros_series": e.saros_series,
            "path_visibility": e.path_visibility,
            "black_hole_duration_days": e.black_hole_duration_days,
            "is_active": e.is_active,
        }

    @staticmethod
    def _gap_to_dict(g: ObsessionGap):
        return {
            "trigger_date": g.trigger_date.isoformat(),
            "planet": g.planet,
            "gap_type": g.gap_type,
            "sequence_steps": g.sequence_steps,
            "expected_pips": g.expected_pips,
            "size_percentage": g.size_percentage,
            "win_rate_long": g.win_rate_long,
            "win_rate_short": g.win_rate_short,
            "god_tier": g.god_tier,
            "is_active": g.is_active,
        }
