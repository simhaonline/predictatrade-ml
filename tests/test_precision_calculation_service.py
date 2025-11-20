# tests/test_precision_calculation_service.py

from datetime import datetime

import pytz
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.services.precision_calculation_service import PrecisionCalculationService


def _get_db() -> Session:
    return SessionLocal()


def test_precision_service_basic():
    db = _get_db()
    svc = PrecisionCalculationService(db)

    # Use Sydney as a reference session
    city_cfg = settings.CITIES["sydney"]
    city = {
        "name": city_cfg.name,
        "timezone": city_cfg.timezone,
        "latitude": city_cfg.latitude,
        "longitude": city_cfg.longitude,
    }

    # Pick an arbitrary UTC date/time
    dt_local = datetime(2025, 11, 18, 10, 0, 0)

    result = svc.calculate_precise_gold_score(city, dt_local)

    # Basic shape checks
    assert "gold_signal_score" in result
    assert "trade_recommendation" in result
    assert "action" in result
    assert "nakshatra_pada" in result
    assert "hora_ruler" in result

    # Range checks
    assert 0.0 <= result["gold_signal_score"] <= 100.0
    assert 0.0 <= result["nakshatra_bullish_score"] <= 1.0
    assert 0.0 <= result["contamination_index"] <= 1.0

    # Trade mapping consistency
    reco = result["trade_recommendation"]
    action = result["action"]
    assert reco in {"STRONG BUY", "BUY", "NEUTRAL", "SELL", "STRONG SELL"}
    if reco in {"STRONG BUY", "BUY"}:
        assert action == "Long"
    elif reco in {"SELL", "STRONG SELL"}:
        assert action == "Short"
    else:
        assert action in {"Flat", "Long", "Short"}
