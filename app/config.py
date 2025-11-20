from __future__ import annotations

import os
from datetime import time
from typing import Dict, Any

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Global application configuration.

    NOTE:
    - Unknown environment variables are ignored (extra="ignore"), so
      older keys in your .env will not break the app.
    """

    # ------------------------------------------------------------------
    # App identity
    # ------------------------------------------------------------------
    APP_NAME: str = "astro-trading-engine"
    APP_VERSION: str = "1.0.0"

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:password@localhost:3306/astro?charset=utf8mb4",
    )
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))

    # ------------------------------------------------------------------
    # Ephemeris & logging
    # ------------------------------------------------------------------
    EPHE_PATH: str = os.getenv("EPHE_PATH", "/usr/share/ephe")
    APP_LOG_PATH: str | None = os.getenv("APP_LOG_PATH") or None

    # Keep everything sidereal with Lahiri by default
    AYANAMSA: str = os.getenv("AYANAMSA", "lahiri")

    # ------------------------------------------------------------------
    # External APIs (optional – used by ML/gold-price modules)
    # ------------------------------------------------------------------
    FINNHUB_API_KEY: str | None = os.getenv("FINNHUB_API_KEY") or os.getenv(
        "finnhub_api_key"
    )
    ALPHA_VANTAGE_API_KEY: str | None = os.getenv("ALPHA_VANTAGE_API_KEY") or os.getenv(
        "alpha_vantage_api_key"
    )

    # ------------------------------------------------------------------
    # City / session configuration
    # ------------------------------------------------------------------
    # Keys must match the session keys used everywhere else
    # (sydney, asia, london, newyork).
    CITIES: Dict[str, Dict[str, Any]] = {
        "sydney": {
            "name": "sydney",
            "timezone": os.getenv("TIMEZONE_SYDNEY", "Australia/Sydney"),
            "latitude": float(os.getenv("LATITUDE_SYDNEY", "-33.8688")),
            "longitude": float(os.getenv("LONGITUDE_SYDNEY", "151.2093")),
        },
        "asia": {
            "name": "tokyo",
            "timezone": os.getenv("TIMEZONE_ASIA", "Asia/Tokyo"),
            "latitude": float(os.getenv("LATITUDE_ASIA", "35.6895")),
            "longitude": float(os.getenv("LONGITUDE_ASIA", "139.6917")),
        },
        "london": {
            "name": "london",
            "timezone": os.getenv("TIMEZONE_LONDON", "Europe/London"),
            "latitude": float(os.getenv("LATITUDE_LONDON", "51.5074")),
            "longitude": float(os.getenv("LONGITUDE_LONDON", "-0.1278")),
        },
        "newyork": {
            "name": "newyork",
            "timezone": os.getenv("TIMEZONE_NEWYORK", "America/New_York"),
            "latitude": float(os.getenv("LATITUDE_NEWYORK", "40.7128")),
            "longitude": float(os.getenv("LONGITUDE_NEWYORK", "-74.006")),
        },
    }

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Important: ignore unknown env keys like timezone_sydney, etc.
        extra = "ignore"


settings = Settings()

# ----------------------------------------------------------------------
# Session trading windows in UTC (from your Excel screenshot)
# ----------------------------------------------------------------------
# We expose this as a plain dict, so it can be used anywhere.
# For cross-midnight windows, "open" is on the previous UTC day,
# "close" is on the trading date.
# ----------------------------------------------------------------------

SESSION_WINDOWS_UTC: Dict[str, Dict[str, time]] = {
    # keys here must match settings.CITIES keys
    "sydney": {"open": time(22, 0), "close": time(7, 0)},   # 22:00 → 07:00
    "asia": {"open": time(23, 0), "close": time(8, 0)},     # 23:00 → 08:00
    "london": {"open": time(7, 0), "close": time(16, 0)},   # 07:00 → 16:00
    "newyork": {"open": time(12, 0), "close": time(21, 0)}, # 12:00 → 21:00
    # Optional for future:
    # "shanghai": {"open": time(1, 30), "close": time(7, 0)},
    # "europe": {"open": time(7, 0), "close": time(16, 0)},
}
