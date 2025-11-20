# app/services/astro_core.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Tuple

import swisseph as swe

from app.services.ephemeris_service import EphemerisService
from app.config import settings


# ---------------------------------------------------------------------
# Zodiac & Nakshatra definitions (sidereal)
# ---------------------------------------------------------------------

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

# 27 Nakshatras, each 13°20' = 13.333... degrees
NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "P. Phalguni", "U. Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshta",
    "Mula", "P. Ashadha", "U. Ashadha", "Shravana", "Dhanishta",
    "Shatabhisha", "P. Bhadrapada", "U. Bhadrapada", "Revati",
]

NAKSHATRA_SPAN = 360.0 / 27.0      # 13.333...°
PADA_SPAN = NAKSHATRA_SPAN / 4.0   # 3.333...°


@dataclass
class PlanetPosition:
    name: str
    longitude: float
    latitude: float
    speed_long: float
    speed_lat: float
    retrograde: bool
    combustion: bool
    sign: str
    nakshatra: str
    pada: int


class AstroCore:
    """
    Higher-level astro engine on top of EphemerisService:
      - Sidereal Lahiri planetary positions
      - Rāśi (sign), Nakshatra, Pada
      - Lunar phase & tithi
      - Ayanāṃśa
      - Fear profile (for FearApocalypseService)
    """

    def __init__(self) -> None:
        swe.set_ephe_path(settings.EPHE_PATH)
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
        self.ephemeris = EphemerisService()

    # ----------------------------------------------------------
    # Internal helpers
    # ----------------------------------------------------------
    def _sidereal_sign(self, lon: float) -> str:
        norm = lon % 360.0
        idx = int(norm // 30.0)  # 0..11
        return ZODIAC_SIGNS[idx]

    def _nakshatra_pada(self, lon: float) -> Tuple[str, int]:
        norm = lon % 360.0
        n_index = int(norm // NAKSHATRA_SPAN)  # 0..26
        nak = NAKSHATRAS[n_index]

        within_nak = norm - n_index * NAKSHATRA_SPAN
        pada_index = int(within_nak // PADA_SPAN)  # 0..3
        pada = pada_index + 1                      # 1..4
        return nak, pada

    # ----------------------------------------------------------
    # Public: positions, lunar phase, ayanamsa
    # ----------------------------------------------------------
    def get_sidereal_positions(self, dt: datetime) -> Dict[str, Dict[str, Any]]:
        """
        Returns:
        {
          "Sun": {
            "longitude": float,
            "latitude": float,
            "speed_long": float,
            "speed_lat": float,
            "retrograde": bool,
            "combustion": bool,
            "sign": "Scorpio",
            "nakshatra": "Anuradha",
            "pada": 3,
          },
          ...
        }
        """
        base_positions = self.ephemeris.get_planet_positions(dt)
        result: Dict[str, Dict[str, Any]] = {}

        for name, pdata in base_positions.items():
            lon = pdata["longitude"]
            sign = self._sidereal_sign(lon)
            nak, pada = self._nakshatra_pada(lon)

            result[name] = {
                "longitude": lon,
                "latitude": pdata.get("latitude", 0.0),
                "speed_long": pdata.get("speed_long", 0.0),
                "speed_lat": pdata.get("speed_lat", 0.0),
                "retrograde": bool(pdata.get("retrograde", False)),
                "combustion": bool(pdata.get("combustion", False)),
                "sign": sign,
                "nakshatra": nak,
                "pada": pada,
            }

        return result

    def get_lunar_phase(self, dt: datetime) -> Dict[str, Any]:
        """
        Compute simple lunar phase and tithi using Sun/Moon sidereal longitude.
        """
        positions = self.get_sidereal_positions(dt)
        sun_long = positions["Sun"]["longitude"]
        moon_long = positions["Moon"]["longitude"]

        phase_angle = (moon_long - sun_long) % 360.0

        # Rough tithi: 12° per tithi
        tithi = int(phase_angle // 12.0) + 1
        if tithi > 30:
            tithi = 30

        # Simple phase naming
        if 0 <= phase_angle < 90:
            phase_name = "Waxing Crescent"
        elif 90 <= phase_angle < 180:
            phase_name = "Waxing Gibbous"
        elif 180 <= phase_angle < 270:
            phase_name = "Waning Gibbous"
        else:
            phase_name = "Waning Crescent"

        return {
            "phase_angle": round(phase_angle, 2),
            "phase_name": phase_name,
            "tithi": tithi,
        }

    def get_ayanamsa(self, dt: datetime) -> float:
        """
        Returns Lahiri ayanamsa for the given datetime.
        """
        jd_ut = self.ephemeris.get_julian_day(dt)
        return swe.get_ayanamsa(jd_ut)

    # ----------------------------------------------------------
    # Fear profile (for FearApocalypseService)
    # ----------------------------------------------------------
    def get_fear_profile(self, dt: datetime) -> Dict[str, Any]:
        """
        Compute a composite "fear profile" based on planetary positions,
        retrogrades, and combustion. This is intentionally simplified but
        structurally compatible with what FearApocalypseService expects:

        {
          "per_planet": { "Sun": 0.8, "Moon": 0.9, ... },
          "average_fear_index": float,
          "saturn_fear_index": float,
          "emotional_tension_index": float,
        }
        """
        positions = self.get_sidereal_positions(dt)
        per_planet: Dict[str, float] = {}

        # Base weight by nature (malefics > benefics)
        base_weights = {
            "Sun": 0.7,
            "Moon": 0.7,
            "Mercury": 0.6,
            "Venus": 0.6,
            "Mars": 0.85,
            "Jupiter": 0.5,
            "Saturn": 1.0,
            "Rahu": 1.0,
            "Ketu": 0.95,
            "Uranus": 0.8,
            "Neptune": 0.7,
            "Pluto": 0.8,
        }

        for name, p in positions.items():
            base = base_weights.get(name, 0.6)

            # Retrograde tends to increase psychological tension
            if p.get("retrograde"):
                base += 0.1

            # Combustion (except Moon) adds pressure
            if p.get("combustion") and name != "Moon":
                base += 0.05

            # Clamp 0..1
            score = max(0.0, min(base, 1.0))
            per_planet[name] = round(score, 3)

        if per_planet:
            average = round(sum(per_planet.values()) / len(per_planet), 3)
        else:
            average = 0.0

        saturn_fear = per_planet.get("Saturn", average)

        # Emotional tension: Moon + Mars + Saturn blend
        moon_fear = per_planet.get("Moon", average)
        mars_fear = per_planet.get("Mars", average)
        emotional_tension = round((moon_fear + mars_fear + saturn_fear) / 3.0, 3)

        return {
            "per_planet": per_planet,
            "average_fear_index": average,
            "saturn_fear_index": saturn_fear,
            "emotional_tension_index": emotional_tension,
        }
