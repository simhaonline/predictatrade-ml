# Astro Gold Multi-Session Trading Engine

High-precision sidereal astro-trading engine for XAUUSD / gold, built on **Swiss Ephemeris**, with:

- 12-planet high-precision ephemeris (Sun…Pluto, Rahu, Ketu)
- 27 Nakshatras × 4 Pada (108 entry points)
- Hora & 24-hour trading calendar
- Fear index, obsession gaps, black-hole windows (eclipses), “apocalypse triggers”
- Saturn transit & retrograde analysis
- Vimshottari Dasha framework (extendable to Shodshottari, Ashtottari, Shashti-Hayani)
- **Multi-session signals** for: Sydney, Asia (Tokyo), London, New York
- CSV + JSON report generator
- FastAPI API + small Web UI to browse reports in tabular form

Everything is **sidereal** using **Lahiri ayanāṃśa** by default.

---

## Project Layout

```text
your_project/
├─ app/
│  ├─ __init__.py
│  ├─ config.py                          # pydantic Settings, city config, EPHE_PATH, API keys
│  ├─ database.py                        # SQLAlchemy engine, SessionLocal, Base, get_db(), init_db()
│  ├─ models.py                          # ORM models (City, SignalScore, RetrogradeCycle, EclipseEvent, ObsessionGap, etc.)
│  ├─ services/
│  │  ├─ __init__.py
│  │  ├─ ephemeris_service.py            # low-level Swiss Ephemeris wrapper
│  │  ├─ precision_calculation_service.py# "Gold Influence Formula" core
│  │  ├─ gold_price_service.py           # Finnhub / Alpha Vantage price data (optional)
│  │  ├─ astro_core.py                   # sidereal core, signs, nakshatras, lunar phases, ayanāṃśa, fear index
│  │  ├─ nakshatra_hora_service.py       # 27×4 padas + 24-hour Hora calendar
│  │  ├─ fear_apocalypse_service.py      # fear profile, obsession gaps, black holes, apocalypse triggers, Saturn transit
│  │  ├─ dasha_service.py                # Vimshottari dasha scaffold (extend for others)
│  ├─ reports/
│  │  ├─ __init__.py
│  │  ├─ multi_session_report.py         # CSV + JSON generator (multi-session engine)
│  └─ api/
│     ├─ __init__.py
│     ├─ main.py                         # FastAPI app (JSON + CSV endpoints, serves Web UI)
├─ web/
│  ├─ index.html                         # Web UI – simple table viewer for reports
│  ├─ app.js                             # calls FastAPI, renders JSON into HTML table
│  └─ styles.css                         # dark, trading-style theme
├─ .env                                  # environment config (DB URL, EPHE_PATH, API keys, timezones)
├─ requirements.txt
└─ README.md

# Installation
## 1. Create & activate virtualenv (recommended)

```
# Create env
conda create -n predictatrade-ml python=3.11 -y
conda activate predictatrade-ml
mkdir -p /srv/predictatrade-ml
cd /srv/predictatrade-ml
```

## 2. Install dependencies

```
pip install -r requirements.txt
pip install pydantic-settings
pip install pytest
pip freeze
```

## 3. Configure .env

```
cp .env.example .env   # if you keep an example file
```

* Then edit .env and set:
- DATABASE_URL to your MySQL instance
- EPHE_PATH to the directory where Swiss Ephemeris files reside
- FINNHUB_API_KEY, ALPHA_VANTAGE_API_KEY (optional; for price data)
- TIMEZONE_* and LATITUDE_*, LONGITUDE_* if you want custom city definitions
- The code uses app.config.Settings (pydantic) to load env values.

## 



curl "https://finnhub.io/api/v1/quote?symbol=OANDA:XAU_USD&token=d4e2su9r01qmhtc6sel0d4e2su9r01qmhtc6selg"

python init_db_runner.py
uvicorn app.api.main:app --reload

sudo useradd -r -s /bin/false fastapi

cat >/etc/systemd/system/fastapi.service<<'EOF'
[Unit]
Description=FastAPI Uvicorn App (predictatrade-ml env)
After=network.target

[Service]
# Project working directory
WorkingDirectory=/srv/predictatrade-ml

# Start uvicorn using conda env binary
ExecStart=/opt/miniconda3/envs/predictatrade-ml/bin/uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --log-config logging.ini

# Restart policy
Restart=always
RestartSec=3

# Environment variables (optional)
Environment="PATH=/opt/miniconda3/envs/predictatrade-ml/bin"

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload && sudo systemctl enable fastapi.service && sudo systemctl start fastapi.service

sudo systemctl status fastapi.service && journalctl -u fastapi.service -f
sudo systemctl stop fastapi.service && sudo systemctl status fastapi.service && journalctl -u fastapi.service -f

sudo chown fastapi:fastapi /srv/predictatrade-ml/
sudo chmod 755 /srv/predictatrade-ml




How this maps to your URLs

With your domain https://api.predictatrade.com pointing at this app:

https://api.predictatrade.com/health

https://api.predictatrade.com/ready

https://api.predictatrade.com/metrics

https://api.predictatrade.com/version

https://api.predictatrade.com/system/info

https://api.predictatrade.com/logs

https://api.predictatrade.com/astro/now

https://api.predictatrade.com/api/reports/latest

https://api.predictatrade.com/api/reports/2025-11-18

https://api.predictatrade.com/api/reports/2025-11-18/csv

https://api.predictatrade.com/web/



python -m pytest -q


Use the same structures that were working earlier for /astro/now and /api/reports/...

Keep /health, /ready, /metrics, /version, /system/info, /logs, /astro/now, /api/reports/{date}, /api/reports/{date}/csv, /dashboard

Handle "latest" in /api/reports/latest


https://api.predictatrade.com/api/reports/2025-11-19?client_tz=Europe/London


https://api.predictatrade.com/time/convert?session=asia&dt=2025-11-19%2010:00&target_tz=Etc/GMT-2

https://api.predictatrade.com/api/reports/2025-11-19/csv?client_tz=Etc/GMT-2


curl "https://api.predictatrade.com/api/reports/2025-11-19?client_tz=Etc/GMT-3" | jq .





https://api.predictatrade.com/web/execution_matrix.html

https://api.predictatrade.com/web/astro_bias.html

https://api.predictatrade.com/web/nakshatra_rationale.html

https://api.predictatrade.com/web/time_conversion.html