# app/services/ephemeris_service.py

from datetime import datetime, timezone
from typing import Dict, Any, Union

import swisseph as swe

from app.config import settings


class EphemerisService:
    """
    Swiss Ephemeris wrapper for sidereal Lahiri positions.
    Provides planetary positions used by AstroCore, PrecisionCalculationService, etc.
    """

    def __init__(self) -> None:
        # Set ephemeris path and sidereal mode (Lahiri)
        swe.set_ephe_path(settings.EPHE_PATH)
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

        # Planet mapping (Swiss Ephemeris IDs)
        self.planets = {
            "Sun": swe.SUN,
            "Moon": swe.MOON,
            "Mercury": swe.MERCURY,
            "Venus": swe.VENUS,
            "Mars": swe.MARS,
            "Jupiter": swe.JUPITER,
            "Saturn": swe.SATURN,
            "Uranus": swe.URANUS,
            "Neptune": swe.NEPTUNE,
            "Pluto": swe.PLUTO,
            # Nodes
            "Rahu": swe.MEAN_NODE,  # North Node
            # Ketu will be synthesized as opposite of Rahu
        }

    # ------------------------------------------------------------------
    # Core helpers
    # ------------------------------------------------------------------
    def get_julian_day(self, dt: datetime) -> float:
        """
        Convert naive or aware datetime to Julian Day (UT).
        - If dt has tzinfo: convert to UTC.
        - If dt is naive: assume it's already UTC.
        """
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc)
        # else: treat naive dt as UTC

        hour_fraction = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
        return swe.julday(dt.year, dt.month, dt.day, hour_fraction)

    def _calc_body(self, jd_ut: float, body: int):
        """
        Low-level wrapper for swe.calc_ut with sidereal flags.
        Returns (longitude, latitude, speed_long, speed_lat).
        """
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL
        xx, retflag = swe.calc_ut(jd_ut, body, flags)
        # xx: [lon, lat, dist, speed_lon, speed_lat, speed_dist]
        lon, lat, dist, speed_lon, speed_lat, speed_dist = xx
        return lon, lat, speed_lon, speed_lat

    def _is_retrograde(self, speed_long: float) -> bool:
        """Retrograde if longitudinal speed is negative."""
        return speed_long < 0.0

    def _check_combustion(
        self, planet_name: str, planet_long: float, sun_long: float, orb_deg: float = 5.0
    ) -> bool:
        """
        Check simple combustion: within orb_deg degrees of the Sun.
        Distance measured along ecliptic, symmetrical around 0°.
        """
        # Sun itself is never combust
        if planet_name == "Sun":
            return False

        distance = abs(planet_long - sun_long) % 360.0
        if distance > 180.0:
            distance = 360.0 - distance
        return distance <= orb_deg

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_planet_positions(
        self, when: Union[datetime, float, int]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Returns sidereal Lahiri positions for all configured planets.

        `when` can be:
          - datetime  → converted to Julian Day internally
          - float/int → treated as Julian Day (UT)

        Structure:
        {
          "Sun": {
             "longitude": float,      # 0..360 sidereal
             "latitude": float,
             "speed_long": float,
             "speed_lat": float,
             "retrograde": bool,
             "combustion": bool,
          },
          ...
        }

        Notes:
        - Rahu is the mean node from Swiss Ephemeris.
        - Ketu is synthesized as Rahu + 180°.
        """

        # Decide how to get jd_ut
        if isinstance(when, (float, int)):
            jd_ut = float(when)
        else:
            # assume datetime
            jd_ut = self.get_julian_day(when)

        # Compute Sun first for combustion checks
        sun_lon, sun_lat, sun_speed_lon, sun_speed_lat = self._calc_body(
            jd_ut, self.planets["Sun"]
        )

        result: Dict[str, Dict[str, Any]] = {}

        for name, body in self.planets.items():
            if name == "Rahu":
                # Compute Rahu explicitly, then deduce Ketu later
                lon, lat, sp_lon, sp_lat = self._calc_body(jd_ut, body)
                retro = self._is_retrograde(sp_lon)
                combust = self._check_combustion(name, lon, sun_lon, orb_deg=5.0)

                result[name] = {
                    "longitude": lon,
                    "latitude": lat,
                    "speed_long": sp_lon,
                    "speed_lat": sp_lat,
                    "retrograde": retro,
                    "combustion": combust,
                }
                continue

            if name == "Sun":
                lon, lat, sp_lon, sp_lat = (
                    sun_lon,
                    sun_lat,
                    sun_speed_lon,
                    sun_speed_lat,
                )
            else:
                lon, lat, sp_lon, sp_lat = self._calc_body(jd_ut, body)

            retro = self._is_retrograde(sp_lon)
            combust = self._check_combustion(name, lon, sun_lon, orb_deg=5.0)

            result[name] = {
                "longitude": lon,
                "latitude": lat,
                "speed_long": sp_lon,
                "speed_lat": sp_lat,
                "retrograde": retro,
                "combustion": combust,
            }

        # Synthesize Ketu as opposite of Rahu
        if "Rahu" in result:
            rahu = result["Rahu"]
            ketu_long = (rahu["longitude"] + 180.0) % 360.0
            ketu_lat = -rahu["latitude"]
            ketu_retro = True  # in Vedic practice, nodes are "retrograde"
            ketu_combust = self._check_combustion("Ketu", ketu_long, sun_lon, orb_deg=5.0)

            result["Ketu"] = {
                "longitude": ketu_long,
                "latitude": ketu_lat,
                "speed_long": rahu["speed_long"],
                "speed_lat": rahu["speed_lat"],
                "retrograde": ketu_retro,
                "combustion": ketu_combust,
            }

        return result
