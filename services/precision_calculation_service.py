from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import pytz
from sqlalchemy.orm import Session

from app.services.astro_core import AstroCore


# Weekday lords (Python weekday(): Monday=0..Sunday=6)
WEEKDAY_LORD = {
    0: "Moon",     # Monday
    1: "Mars",     # Tuesday
    2: "Mercury",  # Wednesday
    3: "Jupiter",  # Thursday
    4: "Venus",    # Friday
    5: "Saturn",   # Saturday
    6: "Sun",      # Sunday
}

# Standard hora sequence
HORA_SEQUENCE = ["Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars"]

# Hora weights for gold (bullish/bearish)
HORA_WEIGHTS = {
    "Venus": 1.0,
    "Saturn": 0.7,
    "Mars": -0.4,
    "Sun": -0.2,
}

# Base nakshatra bullish scores (0..1); can be refined further
DEFAULT_NAKSHATRA_BULLISH = 0.58
NAKSHATRA_BULLISH_SCORES = {
    "Ashwini": 0.62,
    "Bharani": 0.55,
    "Krittika": 0.52,
    "Rohini": 0.70,
    "Mrigashira": 0.64,
    "Ardra": 0.40,
    "Punarvasu": 0.60,
    "Pushya": 0.72,
    "Ashlesha": 0.48,
    "Magha": 0.58,
    "P. Phalguni": 0.60,
    "U. Phalguni": 0.63,
    "Hasta": 0.58,
    "Chitra": 0.57,
    "Swati": 0.58,
    "Vishakha": 0.56,
    "Anuradha": 0.60,
    "Jyeshta": 0.50,
    "Mula": 0.52,
    "P. Ashadha": 0.56,
    "U. Ashadha": 0.60,
    "Shravana": 0.62,
    "Dhanishta": 0.64,
    "Shatabhisha": 0.46,
    "P. Bhadrapada": 0.50,
    "U. Bhadrapada": 0.54,
    "Revati": 0.68,
}

# Seasonal demand by month (0..1) – festivals, jewelry demand, etc.
SEASONAL_DEMAND = {
    1: 0.62,
    2: 0.58,
    3: 0.54,
    4: 0.50,
    5: 0.48,
    6: 0.50,
    7: 0.55,
    8: 0.60,
    9: 0.65,
    10: 0.70,
    11: 0.72,
    12: 0.68,
}


class PrecisionCalculationService:
    """
    Implements the Gold Signal Score formula, using:
      - Moon nakshatra & pada
      - Retrograde count
      - Lunar phase score
      - Simple aspect score (Sun vs Mars/Jupiter/Saturn)
      - Saturn fear index
      - Seasonal demand
      - Contamination index (Rahu/Gulika/Yamaganda)
      - Hora effect (24h hora calendar)
    """

    def __init__(self, db: Optional[Session] = None) -> None:
        """
        db is optional so that the service can be used in pure-astro contexts
        (like hourly backtests and reports) without wiring a database session.
        """
        self.db: Optional[Session] = db
        self.core = AstroCore()

    # --------------------------------------------------------------
    # Helper methods
    # --------------------------------------------------------------
    def _localize(self, city: Dict[str, Any], local_dt: datetime) -> datetime:
        tz = pytz.timezone(city["timezone"])
        if local_dt.tzinfo is None:
            return tz.localize(local_dt)
        return local_dt.astimezone(tz)

    def _nakshatra_bullish_score(
        self, moon_nakshatra: str, positions: Dict[str, Dict[str, Any]]
    ) -> float:
        """
        Base score from Moon nakshatra, adjusted for special bearish configs
        from your Influence document (Sun in Anuradha, Jupiter in Bharani, etc.).
        """
        base = NAKSHATRA_BULLISH_SCORES.get(moon_nakshatra, DEFAULT_NAKSHATRA_BULLISH)

        # --- Special bearish overrides (from doc) ---
        sun = positions.get("Sun")
        jup = positions.get("Jupiter")
        ven = positions.get("Venus")
        mer = positions.get("Mercury")

        if sun and sun["nakshatra"] == "Anuradha":
            base -= 0.12  # bearish configuration for gold
        if jup and jup["nakshatra"] == "Bharani":
            base -= 0.12
        if ven and ven["nakshatra"] in ("Jyeshta", "Jyeshtha", "Punarvasu"):
            base -= 0.10
        if mer and mer["nakshatra"] == "Pushya":
            base -= 0.08

        # clamp
        return max(0.1, min(base, 0.9))

    def _retrograde_factor(self, positions: Dict[str, Dict[str, Any]]) -> float:
        """
        Count retrograde planets; more retrogrades = more nervousness/volatility.
        We normalize to 0..1 so it can be used inside the Gold formula.
        """
        count = sum(1 for p in positions.values() if p.get("retrograde"))
        # typical range 0..7 – normalize
        factor = min(count / 7.0, 1.0)
        return factor, count

    def _lunar_phase_score(self, lunar_phase: Dict[str, Any]) -> float:
        """
        Score 0..1:
          - New/waxing moderately bullish
          - Waning moderately bearish
          - Full moon significantly bearish (doc: frequent dumps around full moon)
        """
        angle = lunar_phase["phase_angle"]  # 0..360
        waxing = angle < 180.0

        # Base: waxing 0.55, waning 0.45
        base = 0.55 if waxing else 0.45

        # Full moon penalty: within ±18° of 180°
        dist_full = abs(angle - 180.0)
        if dist_full < 18.0:
            penalty = (18.0 - dist_full) / 18.0 * 0.35  # up to -0.35
            base -= penalty

        return max(0.1, min(base, 0.9))

    def _aspect_score(self, positions: Dict[str, Dict[str, Any]]) -> float:
        """
        Simple aspect scoring using a subset of the power ratings
        in your doc. We focus on Sun vs Mars/Jupiter/Saturn for now.
        Returns 0..1 (0 = strongly bearish, 1 = strongly bullish).
        """

        def aspect_delta(a, b):
            d = abs((a - b) % 360.0)
            if d > 180.0:
                d = 360.0 - d
            return d

        def contribution(delta, exact_angle, orb, weight):
            if delta > orb:
                return 0.0
            return weight * (1.0 - delta / orb)

        sun = positions.get("Sun")
        mars = positions.get("Mars")
        jup = positions.get("Jupiter")
        sat = positions.get("Saturn")

        score = 0.0

        if sun and mars:
            d = aspect_delta(sun["longitude"], mars["longitude"])
            # Sun–Mars trine/sextile : strongly bullish
            score += contribution(d, 120.0, 6.0, +0.30)
            score += contribution(d, 60.0, 6.0, +0.20)
            # square/opposition : bearish
            score += contribution(d, 90.0, 6.0, -0.15)
            score += contribution(d, 180.0, 6.0, -0.20)

        if sun and jup:
            d = aspect_delta(sun["longitude"], jup["longitude"])
            score += contribution(d, 120.0, 6.0, +0.20)
            score += contribution(d, 60.0, 6.0, +0.15)
            score += contribution(d, 90.0, 6.0, -0.10)

        if sun and sat:
            d = aspect_delta(sun["longitude"], sat["longitude"])
            # Sun–Saturn trine/conj : bearish for gold (per doc)
            score += contribution(d, 0.0, 6.0, -0.25)
            score += contribution(d, 120.0, 6.0, -0.20)
            score += contribution(d, 180.0, 6.0, -0.10)

        # center around 0.5, clamp 0..1
        score = 0.5 + score
        return max(0.0, min(score, 1.0))

    def _seasonal_demand(self, dt: datetime) -> float:
        return SEASONAL_DEMAND.get(dt.month, 0.55)

    def _hora_ruler_and_effect(self, local_dt: datetime) -> (str, float):
        """
        Simple 24h hora model:
          - Sunrise ~ 06:00 local, day lord = weekday lord
          - 24 horas of 1h length
        """
        sunrise = local_dt.replace(hour=6, minute=0, second=0, microsecond=0)
        if local_dt < sunrise:
            sunrise -= timedelta(days=1)

        diff_hours = int((local_dt - sunrise).total_seconds() // 3600)
        weekday = sunrise.weekday()
        day_lord = WEEKDAY_LORD[weekday]

        start_idx = HORA_SEQUENCE.index(day_lord)
        hora_idx = diff_hours % 24
        ruler = HORA_SEQUENCE[(start_idx + hora_idx) % len(HORA_SEQUENCE)]
        effect = HORA_WEIGHTS.get(ruler, 0.0)
        return ruler, effect

    def _contamination_index(self, local_dt: datetime) -> float:
        """
        Rahu, Gulika, Yamaganda contamination, approximated using
        8 equal daytime segments between 06:00 and 18:00 local.
        """
        sunrise = local_dt.replace(hour=6, minute=0, second=0, microsecond=0)
        sunset = local_dt.replace(hour=18, minute=0, second=0, microsecond=0)
        if local_dt < sunrise:
            sunrise -= timedelta(days=1)
            sunset -= timedelta(days=1)

        day_duration = (sunset - sunrise).total_seconds()
        part = day_duration / 8.0
        weekday = sunrise.weekday()  # 0=Mon..6=Sun

        rahu_seg = {0: 2, 1: 7, 2: 5, 3: 6, 4: 4, 5: 3, 6: 8}[weekday]
        yama_seg = {0: 5, 1: 4, 2: 3, 3: 2, 4: 7, 5: 6, 6: 1}[weekday]
        gulika_seg = {0: 3, 1: 6, 2: 2, 3: 5, 4: 1, 5: 7, 6: 4}[weekday]

        def seg_window(seg_idx: int):
            start = sunrise + timedelta(seconds=(seg_idx - 1) * part)
            end = start + timedelta(seconds=part)
            return start, end

        def in_seg(seg_idx: int) -> float:
            start, end = seg_window(seg_idx)
            if not (start <= local_dt < end):
                return 0.0
            # fraction of the hour that lies in the segment
            hour_start = local_dt.replace(minute=0, second=0, microsecond=0)
            hour_end = hour_start + timedelta(hours=1)
            overlap = max(
                0.0,
                (min(end, hour_end) - max(start, hour_start)).total_seconds(),
            )
            return overlap / 3600.0

        f_rahu = in_seg(rahu_seg)
        f_gulika = in_seg(gulika_seg)
        f_yama = in_seg(yama_seg)

        index = 1.0 * f_rahu + 0.7 * f_gulika + 0.5 * f_yama
        return max(0.0, min(index, 1.0))

    # --------------------------------------------------------------
    # Public: main scoring entrypoint
    # --------------------------------------------------------------
    def calculate_precise_gold_score(
        self, city: Dict[str, Any], local_dt: datetime
    ) -> Dict[str, Any]:
        """
        Compute the Gold Signal Score for a given city+time.
        Returns a dict used by multi_session_report.
        """
        local_dt = self._localize(city, local_dt)

        # Core astro data
        positions = self.core.get_sidereal_positions(local_dt)
        lunar_phase = self.core.get_lunar_phase(local_dt)
        fear_profile = self.core.get_fear_profile(local_dt)
        ayanamsa = self.core.get_ayanamsa(local_dt)  # not used directly in score yet

        # Moon nakshatra / pada
        moon = positions["Moon"]
        moon_nak = moon["nakshatra"]
        moon_pada = moon["pada"]
        nakshatra_pada = f"{moon_nak}-{moon_pada}"

        nakshatra_bullish = self._nakshatra_bullish_score(moon_nak, positions)

        # Retrograde crowding
        retro_factor, retro_count = self._retrograde_factor(positions)

        # Lunar phase score
        lunar_phase_score = self._lunar_phase_score(lunar_phase)

        # Aspect score
        aspect_score = self._aspect_score(positions)

        # Fear metrics
        saturn_fear = fear_profile["saturn_fear_index"]

        # Seasonal demand
        seasonal_demand = self._seasonal_demand(local_dt)

        # Eclipse proximity – for now neutral (0); your existing eclipse logic
        # still feeds eclipse_influence separately into the report.
        eclipse_proximity = 0.0

        # Hora & contamination
        hora_ruler, hora_effect = self._hora_ruler_and_effect(local_dt)
        contamination_index = self._contamination_index(local_dt)

        # Navamsa composite: placeholder neutral 0.5 until full D9 engine is wired
        navamsa_composite = 0.5

        # ----------------------------------------------------------
        # GOLD SIGNAL SCORE (structure based on your formula)
        # ----------------------------------------------------------
        base_components = (
            20.0 * nakshatra_bullish
            + 15.0 * retro_factor
            + 15.0 * navamsa_composite
            + 15.0 * lunar_phase_score
            + 10.0 * aspect_score
            + 10.0 * (eclipse_proximity * 2.0)
            + 10.0 * saturn_fear
            + 5.0 * seasonal_demand
        )

        contamination_penalty = 10.0 * contamination_index
        hora_bonus = 8.0 * hora_effect

        raw_score = base_components - contamination_penalty + hora_bonus

        # ----------------------------------------------------------
        # Re-scaling: center around a neutral astro bias
        #
        # Empirically, raw_score tends to live near ~55.
        # We treat ~57.5 as neutral (→ 50 on 0..100 scale) and
        # stretch deviations so that some hours fall clearly
        # below 45 (SELL) and some above 55 (BUY).
        # ----------------------------------------------------------
        NEUTRAL_PIVOT = 57.5   # raw score near which we consider day "balanced"
        SCALE_FACTOR = 4.0     # controls how wide scores spread around 50

        deviation = raw_score - NEUTRAL_PIVOT
        scaled = 50.0 + deviation * SCALE_FACTOR

        gold_signal_score = max(0.0, min(100.0, scaled))
        gold_signal_score = round(gold_signal_score, 2)

        # for debugging, expose the rescaled score as base_score
        base_score = gold_signal_score

        # ----------------------------------------------------------
        # Map score → trade regime and position size
        #
        # Symmetric bands:
        #   65+       STRONG BUY (Long 300%)
        #   55–65     BUY        (Long 100%)
        #   45–55     NEUTRAL    (Flat)
        #   35–45     SELL       (Short 100%)
        #   <35       STRONG SELL(Short 300%)
        # ----------------------------------------------------------
        if gold_signal_score >= 65:
            trade_reco = "STRONG BUY"
            action = "Long"
            position_pct = 300
        elif gold_signal_score >= 55:
            trade_reco = "BUY"
            action = "Long"
            position_pct = 100
        elif gold_signal_score >= 45:
            trade_reco = "NEUTRAL"
            action = "Flat"
            position_pct = 0
        elif gold_signal_score >= 35:
            trade_reco = "SELL"
            action = "Short"
            position_pct = 100
        else:
            trade_reco = "STRONG SELL"
            action = "Short"
            position_pct = 300

        # Execution levels (same for long/short, interpreted by EA)
        sl_pips = 15
        tp1_pips = 40
        tp2_pips = 120

        return {
            "date": local_dt.date().isoformat(),
            "time": local_dt.strftime("%H:%M"),
            "gold_signal_score": gold_signal_score,
            "base_score": base_score,
            "trade_recommendation": trade_reco,
            "action": action,
            "position_size_percentage": position_pct,
            "stop_loss_pips": sl_pips,
            "take_profit_1_pips": tp1_pips,
            "take_profit_2_pips": tp2_pips,
            "nakshatra_pada": nakshatra_pada,
            "nakshatra_bullish_score": round(nakshatra_bullish, 3),
            "retrograde_count": retro_count,
            "eclipse_influence": 0,  # your existing eclipse logic can override
            "hora_ruler": hora_ruler,
            "hora_effect": hora_effect,
            "contamination_index": round(contamination_index, 3),
        }
