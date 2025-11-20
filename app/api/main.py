from __future__ import annotations

from datetime import date, datetime, time, timedelta
from io import StringIO
from typing import Any, Dict, List, Optional

import csv
import os

import pytz
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings, SESSION_WINDOWS_UTC
from app.database import get_db, init_db, SessionLocal
from app.reports.multi_session_report import (
    generate_multi_session_report,
    get_report_metrics,
)
from app.services.astro_core import AstroCore
from app.services.fear_apocalypse_service import FearApocalypseService
from sqlalchemy.orm import Session

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

# ---------------------------------------------------------------
# Global startup time for uptime metrics
# ---------------------------------------------------------------
START_TIME_UTC = datetime.utcnow().replace(tzinfo=pytz.UTC)

# ---------------------------------------------------------------
# CORS
# ---------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------
# Static /web dashboard
# ---------------------------------------------------------------

WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "web")
if os.path.isdir(WEB_DIR):
    app.mount("/web", StaticFiles(directory=WEB_DIR, html=True), name="web")


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/web/")


# ---------------------------------------------------------------
# Utility
# ---------------------------------------------------------------


def _parse_date_or_400(date_str: str) -> date:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format, use YYYY-MM-DD")

# ---------------------------------------------------------------
# Astrological bias & ML feature vector construction
# ---------------------------------------------------------------

# We define a wide, stable feature space derived from the
# "Astrological Influence on Gold" framework:
# - Planets (Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto, Rahu, Ketu)
# - 12 houses
# - Eclipses, full/new moon, major conjunctions
# - Seasonal/quarterly and monthly biases
# - Special nakshatra combinations (Anuradha, Pushya, Jyeshtha, Punarvasu, Bharani)
#
# Each row will expose:
#   row["astro_bias"] (label)
#   row["astro_bias_score"] (numeric)
#   row["ml_features"]["named"] (subset of these features with values)
#   row["ml_features"]["dense"] (fixed-length float[] aligned to ml_feature_index)
#
# At the top level, the report will include:
#   report["ml_feature_index"] = {feature_name: index, ...}

_PLANETS: List[str] = [
    "sun", "moon", "mercury", "venus", "mars",
    "jupiter", "saturn", "uranus", "neptune", "pluto",
    "rahu", "ketu",
]

_HOUSES: List[int] = list(range(1, 13))

_SEASONS: List[str] = ["q1", "q2", "q3", "q4"]

_EVENTS: List[str] = [
    "full_moon",
    "new_moon",
    "solar_eclipse",
    "lunar_eclipse",
    "venus_mars_conjunction",
    "mars_jupiter_conjunction",
    "saturn_pluto_conjunction",
]

_MONTHS: List[str] = [
    "jan", "feb", "mar", "apr", "may", "jun",
    "jul", "aug", "sep", "oct", "nov", "dec",
]

_WEEKDAYS: List[str] = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

# Build the full feature name list
_ML_FEATURE_NAMES: List[str] = []

# Core numeric astro fields already in your rows
_ML_FEATURE_NAMES.extend(
    [
        "nakshatra_bullish_score",
        "hora_effect",
        "retrograde_count",
        "eclipse_influence",
        "contamination_index",
    ]
)

# Planet-level features (bullish / bearish / retrograde intensity)
for _p in _PLANETS:
    _ML_FEATURE_NAMES.append(f"{_p}_bullish_score")
    _ML_FEATURE_NAMES.append(f"{_p}_bearish_score")
    _ML_FEATURE_NAMES.append(f"{_p}_retrograde_intensity")

# House-level features (from 12-house gold framework)
for _h in _HOUSES:
    _ML_FEATURE_NAMES.append(f"house_{_h}_bullish_power")
    _ML_FEATURE_NAMES.append(f"house_{_h}_bearish_power")
    _ML_FEATURE_NAMES.append(f"house_{_h}_activation_score")

# High-impact events (eclipses, conjunctions, full/new moon)
for _ev in _EVENTS:
    _ML_FEATURE_NAMES.append(f"event_{_ev}_impact")

# Seasonal quarters (Q1–Q4 bias)
for _s in _SEASONS:
    _ML_FEATURE_NAMES.append(f"season_{_s}_bias")

# Monthly seasonal effects (Jan–Dec; strong patterns around July/Aug/Sept etc.) 
for _m in _MONTHS:
    _ML_FEATURE_NAMES.append(f"month_{_m}_bias")

# Day-of-week patterns
for _w in _WEEKDAYS:
    _ML_FEATURE_NAMES.append(f"weekday_{_w}_bias")

# Specific nakshatra-based bearish factors mentioned in the research 
_ML_FEATURE_NAMES.extend(
    [
        "sun_anuradha_bearish_factor",
        "mercury_pushya_slump_factor",
        "venus_jyeshtha_slump_factor",
        "venus_punarvasu_slump_factor",
        "jupiter_bharani_bearish_factor",
    ]
)

# Stable mapping: feature_name -> index in the dense vector
ML_FEATURE_INDEX: Dict[str, int] = {
    name: idx for idx, name in enumerate(_ML_FEATURE_NAMES)
}


def _safe_float(row: Dict[str, Any], key: str, default: float = 0.0) -> float:
    """Safely convert row[key] to float, with a sensible default."""
    v = row.get(key, default)
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def compute_astro_bias_for_row(row: Dict[str, Any]) -> None:
    """
    Compute astro_bias (label) and astro_bias_score (numeric) for a row
    using the high-level aggregate astro factors already present:

      - nakshatra_bullish_score
      - hora_effect
      - retrograde_count
      - eclipse_influence
      - contamination_index

    The weights/thresholds are derived from the qualitative logic in
    the "Astrological Influence on Gold" document: houses, retrogrades,
    eclipses, and nakshatra effects on gold price. 
    """
    nakshatra_bullish = _safe_float(row, "nakshatra_bullish_score", 0.0)
    hora_effect = _safe_float(row, "hora_effect", 0.0)
    retrograde_count = _safe_float(row, "retrograde_count", 0.0)
    eclipse_influence = _safe_float(row, "eclipse_influence", 0.0)
    contamination_index = _safe_float(row, "contamination_index", 0.0)

    # Core score formula – you can tweak these weights as you refine
    # the model against real data.
    score = (
        1.5 * nakshatra_bullish +
        1.2 * hora_effect -
        0.8 * retrograde_count -
        1.2 * eclipse_influence -
        0.7 * contamination_index
    )

    # Clamp to a sane range
    score = max(-5.0, min(5.0, score))

    if score >= 3.0:
        label = "STRONG BULLISH"
    elif score >= 1.0:
        label = "BULLISH"
    elif score <= -3.0:
        label = "STRONG BEARISH"
    elif score <= -1.0:
        label = "BEARISH"
    else:
        label = "NEUTRAL"

    row["astro_bias_score"] = round(score, 2)
    row["astro_bias"] = label


def build_ml_features_for_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build the ML-ready feature payload for a single row.

    Returns:
      {
        "named": { feature_name: value, ... },
        "dense": [float, float, ...]  # aligned to ML_FEATURE_INDEX
      }
    """
    named: Dict[str, float] = {}

    # 1) Populate the features we can directly map from current rows.
    for key in [
        "nakshatra_bullish_score",
        "hora_effect",
        "retrograde_count",
        "eclipse_influence",
        "contamination_index",
    ]:
        named[key] = _safe_float(row, key, 0.0)

    # TODO: As you extend your astro pipeline, populate additional
    # planet/house/event features here using real calculations
    # (e.g., full moon flags, Venus-Mars conjunction windows, etc.)

    # 2) Build the dense vector aligned to ML_FEATURE_INDEX
    dense = [0.0] * len(ML_FEATURE_INDEX)
    for feat_name, value in named.items():
        idx = ML_FEATURE_INDEX.get(feat_name)
        if idx is not None:
            dense[idx] = float(value)

    return {"named": named, "dense": dense}


def attach_astro_bias_and_ml_features(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mutates report["sessions"][session] rows to include:
      - astro_bias
      - astro_bias_score
      - ml_features (named + dense)
    Also injects the global ml_feature_index at the top level.
    """
    sessions = report.get("sessions", {})
    for sess_key, sess_rows in sessions.items():
        for row in sess_rows:
            compute_astro_bias_for_row(row)
            row["ml_features"] = build_ml_features_for_row(row)

    # Expose the feature index once per report so the client/ML code
    # can interpret the dense vectors.
    report["ml_feature_index"] = ML_FEATURE_INDEX
    return report



def _safe_float(row: Dict[str, Any], key: str, default: float = 0.0) -> float:
    """Helper: safely convert a row[key] to float."""
    v = row.get(key, default)
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def compute_astro_bias_for_row(row: Dict[str, Any]) -> None:
    """
    Compute astro_bias and astro_bias_score from the astro fields already
    present on the row, and attach them back onto the dict.

    Inputs (from your existing data model):
      - nakshatra_bullish_score
      - hora_effect
      - retrograde_count
      - eclipse_influence
      - contamination_index
    """

    nakshatra_bullish = _safe_float(row, "nakshatra_bullish_score", 0.0)
    hora_effect = _safe_float(row, "hora_effect", 0.0)
    retrograde_count = _safe_float(row, "retrograde_count", 0.0)
    eclipse_influence = _safe_float(row, "eclipse_influence", 0.0)
    contamination_index = _safe_float(row, "contamination_index", 0.0)

    # Core score formula – adjust weights/thresholds as you refine the system
    score = (
        1.5 * nakshatra_bullish +
        1.2 * hora_effect -
        0.8 * retrograde_count -
        1.2 * eclipse_influence -
        0.7 * contamination_index
    )

    # Clamp sanity range
    score = max(-5.0, min(5.0, score))

    # Map score → label
    if score >= 3.0:
        label = "STRONG BULLISH"
    elif score >= 1.0:
        label = "BULLISH"
    elif score <= -3.0:
        label = "STRONG BEARISH"
    elif score <= -1.0:
        label = "BEARISH"
    else:
        label = "NEUTRAL"

    row["astro_bias_score"] = round(score, 2)
    row["astro_bias"] = label


def attach_astro_bias_to_report(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Walks the report['sessions'] dict and attaches astro_bias and
    astro_bias_score to every row in every session.
    """
    sessions = report.get("sessions", {})
    for sess_key, sess_rows in sessions.items():
        # sess_rows is expected to be a list[dict]
        for row in sess_rows:
            compute_astro_bias_for_row(row)
    return report


# ---------------------------------------------------------------
# Lifespan: init DB on startup
# ---------------------------------------------------------------
@app.on_event("startup")
async def on_startup():
    init_db()


# ---------------------------------------------------------------
# Health / Ready / Metrics / System Info / Logs
# ---------------------------------------------------------------


@app.get("/version")
async def version():
    return {"app_name": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/health")
async def health():
    now = datetime.utcnow().isoformat()
    return {"status": "OK", "time": now}


@app.get("/ready")
async def ready(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        return {"status": "READY", "database": "OK"}
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Database not ready: {exc}")


@app.get("/metrics")
async def metrics():
    now = datetime.utcnow().replace(tzinfo=pytz.UTC)
    uptime = (now - START_TIME_UTC).total_seconds()
    rep = get_report_metrics()
    return {
        "uptime_seconds": uptime,
        "system_time": now.isoformat(),
        "last_report_generated": rep["last_report_generated"],
        "last_report_rows": rep["last_report_rows"],
        "last_report_sessions": rep["last_report_sessions"],
    }


@app.get("/system/info")
async def system_info(db: Session = Depends(get_db)):
    now = datetime.utcnow().replace(tzinfo=pytz.UTC)
    uptime = (now - START_TIME_UTC).total_seconds()
    cities = settings.CITIES

    db_ok = True
    db_error = None
    try:
        db.execute("SELECT 1")
    except Exception as exc:  # pragma: no cover
        db_ok = False
        db_error = str(exc)

    return {
        "app": {"name": settings.APP_NAME, "version": settings.APP_VERSION},
        "runtime": {
            "python_version": os.sys.version.split()[0],
            "platform": os.uname().sysname + "-" + os.uname().release,
        },
        "database": {"ok": db_ok, "error": db_error},
        "cities": cities,
        "server_time_utc": now.isoformat(),
        "uptime_seconds": uptime,
    }


@app.get("/logs")
async def logs():
    log_path = settings.APP_LOG_PATH or "app.log"
    exists = os.path.exists(log_path)
    if not exists:
        return {
            "log_path": log_path,
            "exists": False,
            "message": "Log file not found. Configure APP_LOG_PATH or logging to file.",
        }
    # Basic tail of log file
    try:
        with open(log_path, "r") as f:
            content = f.read()[-8000:]
        return PlainTextResponse(content)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Error reading log file: {exc}")


# ---------------------------------------------------------------
# Astro snapshot: /astro/now
# ---------------------------------------------------------------


@app.get("/astro/now")
async def astro_now(
    session: str = Query("sydney", description="Session key: sydney/asia/london/newyork"),
    client_tz: Optional[str] = Query(None),
):
    if session not in settings.CITIES:
        raise HTTPException(status_code=400, detail="Unknown session")

    core = AstroCore()
    fear = FearApocalypseService(core=core)

    dt_utc = datetime.utcnow().replace(tzinfo=pytz.UTC)

    # Basic bundle: positions + fear indices + saturn retro / apocalypse flags
    positions = core.get_sidereal_positions(dt_utc)
    fear_profile = core.get_fear_profile(dt_utc)
    saturn_retro = core.is_saturn_retrograde(dt_utc)
    apoc = fear.is_apocalypse_trigger(dt_utc)

    return {
        "timestamp_utc": dt_utc.isoformat(),
        "ayanamsa_lahiri": core.get_ayanamsa(dt_utc),
        "lunar_phase": core.get_lunar_phase(dt_utc),
        "fear_profile": fear_profile,
        "saturn_retrograde_active": saturn_retro,
        "apocalypse_trigger": apoc,
        "planets": positions,
        # Session projections can still be computed client-side from reports
    }


# ---------------------------------------------------------------
# Multi-session reports
# ---------------------------------------------------------------


@app.get("/api/reports/{date_str}")
async def get_report(
    date_str: str,
    session: str = Query("all", description="Session key or 'all'"),
    client_tz: Optional[str] = Query(None),
):
    d = _parse_date_or_400(date_str)
    report = generate_multi_session_report(d, client_tz=client_tz)

    # Optional: filter to single session
    if session != "all":
        if session not in report["sessions"]:
            raise HTTPException(status_code=400, detail="Unknown session")
        report["sessions"] = {session: report["sessions"][session]}

    # Attach astro_bias and ML vector features
    report = attach_astro_bias_and_ml_features(report)

    return report


@app.get("/api/reports/{date_str}/csv")
async def get_report_csv(
    date_str: str,
    session: str = Query("all", description="Session key or 'all'"),
    client_tz: Optional[str] = Query(None),
):
    d = _parse_date_or_400(date_str)
    report = generate_multi_session_report(d, client_tz=client_tz)

    # Enrich with astro_bias + ml_features so CSV sees the same shape
    report = attach_astro_bias_and_ml_features(report)
    sessions = report["sessions"]

    rows: List[Dict[str, Any]] = []
    for sess_key, sess_rows in sessions.items():
        if session != "all" and sess_key != session:
            continue
        rows.extend(sess_rows)

    if not rows:
        raise HTTPException(status_code=404, detail="No data for this date/session")

    # For CSV, nested objects (ml_features) will be rendered as JSON strings.
    fieldnames = sorted(rows[0].keys())
    buf = StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for r in rows:
        writer.writerow(r)

    return PlainTextResponse(
        buf.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="report_{date_str}_{session}.csv"'
        },
    )


@app.get("/api/reports/latest")
async def get_report_latest(
    client_tz: Optional[str] = Query(None),
    session: str = Query("all"),
):
    today = datetime.utcnow().date()
    # Delegate to get_report so we reuse the same astro_bias logic
    return await get_report(today.isoformat(), session=session, client_tz=client_tz)


# ---------------------------------------------------------------
# Time conversion & session normalisation
# ---------------------------------------------------------------


@app.get("/api/sessions/grid")
async def sessions_grid(
    date_str: str = Query(..., description="Trading date, YYYY-MM-DD"),
    server_tz: str = Query("Etc/GMT-2"),
):
    trading_date = _parse_date_or_400(date_str)
    server_zone = pytz.timezone(server_tz)

    sessions_info: List[Dict[str, Any]] = []

    for key, city in settings.CITIES.items():
        sess_tz = pytz.timezone(city["timezone"])
        win = SESSION_WINDOWS_UTC.get(key)
        if not win:
            continue

        open_t = win["open"]
        close_t = win["close"]

        # for cross-midnight window, open is previous UTC day
        if open_t < close_t:
            utc_start = datetime.combine(trading_date, open_t, tzinfo=pytz.UTC)
            utc_end = datetime.combine(trading_date, close_t, tzinfo=pytz.UTC)
        else:
            utc_start = datetime.combine(trading_date - timedelta(days=1), open_t, tzinfo=pytz.UTC)
            utc_end = datetime.combine(trading_date, close_t, tzinfo=pytz.UTC)

        local_start = utc_start.astimezone(sess_tz)
        local_end = utc_end.astimezone(sess_tz)
        server_start = utc_start.astimezone(server_zone)
        server_end = utc_end.astimezone(server_zone)

        sessions_info.append(
            {
                "session": key.upper(),
                "session_key": key,
                "session_tz": city["timezone"],
                "local_start": local_start.isoformat(),
                "local_end": local_end.isoformat(),
                "utc_start": utc_start.isoformat(),
                "utc_end": utc_end.isoformat(),
                "server_tz": server_tz,
                "server_start": server_start.isoformat(),
                "server_end": server_end.isoformat(),
            }
        )

    return {
        "date": trading_date.isoformat(),
        "server_tz": server_tz,
        "sessions": sessions_info,
    }


@app.get("/api/sessions/normalize")
async def normalize_server_timestamp(
    trading_date: str = Query(..., description="Trading date, YYYY-MM-DD"),
    server_tz: str = Query("Etc/GMT-2"),
    server_time: str = Query(..., description="Server time as YYYY-MM-DD HH:MM"),
):
    d = _parse_date_or_400(trading_date)
    server_zone = pytz.timezone(server_tz)

    try:
        naive = datetime.strptime(server_time, "%Y-%m-%d %H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid server_time format, use YYYY-MM-DD HH:MM")

    server_dt = server_zone.localize(naive)
    utc_dt = server_dt.astimezone(pytz.UTC)

    grid = await sessions_grid(d.isoformat(), server_tz=server_tz)
    sessions: List[Dict[str, Any]] = grid["sessions"]

    in_window = False
    active_session: Optional[Dict[str, Any]] = None

    for sess in sessions:
        utc_start = datetime.fromisoformat(sess["utc_start"])
        utc_end = datetime.fromisoformat(sess["utc_end"])
        if utc_start <= utc_dt < utc_end:
            in_window = True
            active_session = sess
            break

    result: Dict[str, Any] = {
        "trading_date": d.isoformat(),
        "server_tz": server_tz,
        "server_time": server_dt.isoformat(),
        "utc_time": utc_dt.isoformat(),
        "in_trading_window": in_window,
    }

    if active_session:
        sess_tz = pytz.timezone(active_session["session_tz"])
        session_local = utc_dt.astimezone(sess_tz)
        result.update(
            {
                "session": active_session["session_key"],
                "session_tz": active_session["session_tz"],
                "session_local_time": session_local.isoformat(),
                "session_window": {
                    "utc_start": active_session["utc_start"],
                    "utc_end": active_session["utc_end"],
                    "local_start": active_session["local_start"],
                    "local_end": active_session["local_end"],
                },
            }
        )

    return result
