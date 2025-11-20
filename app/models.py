# app/models.py

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    JSON,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


# ============================================================
#  CITY
# ============================================================
class City(Base):
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    timezone = Column(String(100), nullable=False)

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    sunrise_offset = Column(Float, default=6.5)
    sunset_offset = Column(Float, default=18.0)

    # relationships
    signal_scores = relationship("SignalScore", back_populates="city")
    planetary_positions = relationship("PlanetaryPosition", back_populates="city")


# ============================================================
#  SIGNAL SCORE (Main Gold Influence Output)
# ============================================================
class SignalScore(Base):
    __tablename__ = "signal_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, index=True, nullable=False)

    # Foreign key -> City
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)
    city = relationship("City", back_populates="signal_scores")

    base_score = Column(Float, nullable=False)
    planetary_intensity = Column(Float, nullable=False)
    aspectual_score = Column(Float, nullable=False)

    cosmic_pressure = Column(String(50))
    gold_signal_score = Column(Float, nullable=False)
    trade_recommendation = Column(String(20), nullable=False)

    retrograde_count = Column(Integer, default=0)
    eclipse_influence = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_signal_timestamp_city", "timestamp", "city_id"),
    )


# ============================================================
#  PLANETARY POSITIONS
# ============================================================
class PlanetaryPosition(Base):
    __tablename__ = "planetary_positions"

    id = Column(Integer, primary_key=True, autoincrement=True)

    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)

    planet = Column(String(20), index=True, nullable=False)

    longitude = Column(Float, nullable=False)
    latitude = Column(Float, nullable=True)
    speed_long = Column(Float, nullable=True)
    speed_lat = Column(Float, nullable=True)

    retrograde = Column(Boolean, default=False)
    combustion = Column(Boolean, default=False)
    exalted = Column(Boolean, default=False)
    debilitated = Column(Boolean, default=False)

    nakshatra = Column(String(30))
    pada = Column(Integer)

    city = relationship("City", back_populates="planetary_positions")

    __table_args__ = (
        Index("idx_pos_timestamp_planet", "timestamp", "planet"),
    )


# ============================================================
#  RETROGRADE CYCLES
# ============================================================
class RetrogradeCycle(Base):
    __tablename__ = "retrograde_cycles"

    id = Column(Integer, primary_key=True, autoincrement=True)

    planet = Column(String(20), index=True, nullable=False)
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, nullable=False, index=True)

    sign = Column(String(20))
    duration_days = Column(Integer)
    shadow_period_weeks = Column(Integer)

    obsession_gap_type = Column(String(50))
    is_active = Column(Boolean, default=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================
#  ECLIPSE EVENTS (Black Hole Windows)
# ============================================================
class EclipseEvent(Base):
    __tablename__ = "eclipse_events"

    id = Column(Integer, primary_key=True, autoincrement=True)

    date_utc = Column(DateTime, index=True, nullable=False)
    eclipse_type = Column(String(20), nullable=False)  # Solar / Lunar
    degree_sign = Column(String(20))
    gamma = Column(Float)
    saros_series = Column(String(20))
    path_visibility = Column(String(200))
    black_hole_duration_days = Column(Integer)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_eclipse_date", "date_utc"),
    )


# ============================================================
#  OBSESSION GAPS (market anomalies)
# ============================================================
class ObsessionGap(Base):
    __tablename__ = "obsession_gaps"

    id = Column(Integer, primary_key=True, autoincrement=True)

    trigger_date = Column(DateTime, index=True, nullable=False)
    planet = Column(String(20), index=True, nullable=False)
    gap_type = Column(String(50))

    sequence_steps = Column(Text)
    expected_pips = Column(Integer)
    size_percentage = Column(Integer)

    win_rate_long = Column(Float)
    win_rate_short = Column(Float)

    god_tier = Column(Boolean, default=False, index=True)
    is_active = Column(Boolean, default=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================
#  EXTRA: NAKSHATRA TRANSIT STORAGE
# ============================================================
class NakshatraTransit(Base):
    __tablename__ = "nakshatra_transits"

    id = Column(Integer, primary_key=True, autoincrement=True)

    timestamp = Column(DateTime, index=True, nullable=False)
    planet = Column(String(20))
    nakshatra = Column(String(30))
    pada = Column(Integer)

    special_flag = Column(String(50))  # retro entry / exit / exaltation zone etc.
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================
#  OPTIONAL HISTORICAL DATA: UltraDetailed Matrix
# ============================================================
class UltraDetailedExecutionMatrix(Base):
    __tablename__ = "ultra_detailed_execution_matrix"

    id = Column(Integer, primary_key=True)
    data = Column(JSON)  # entire row stored as JSON as per your old file


# ============================================================
#  OPTIONAL HISTORICAL Astro Bias Table
# ============================================================
class AstrologicalBiasAndTradeRecommendation(Base):
    __tablename__ = "astrological_bias_and_trade_recommendation"

    id = Column(Integer, primary_key=True)
    date = Column(String(25))
    planetary_positions = Column(JSON)
    signals = Column(JSON)
    performance_notes = Column(JSON)


# ============================================================
#  OPTIONAL Historical Nakshatra changes
# ============================================================
class NakshatraTransitionsAndMicroRationale(Base):
    __tablename__ = "nakshatra_transitions_micro_rationale"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    moon_nakshatra = Column(String(30))
    moon_pada = Column(Integer)
    analysis_data = Column(JSON)

