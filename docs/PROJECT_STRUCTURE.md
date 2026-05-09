# Predict-A-Trade vNext Project Structure

This document outlines the proposed project structure based on the analysis of requirements documentation (REPOSITORY_UNDERSTANDING.md, DETAILED_SOW.md, GAP_ANALYSIS.md, ARCHITECTURE_PLAN.md, EXECUTION_ROADMAP.md) and project conventions.

## 1. Folder Structure

The project follows a monorepo layout with clear separation of concerns.

```
/ (root)
├── src/                 # Backend Python services (FastAPI)
│   ├── pat-data/        # Data Foundation Layer service
│   │   ├── main.py              # Application entrypoint
│   │   ├── api.py               # FastAPI routes and dependency injection
│   │   ├── ingestor.py          # Market data ingestion from providers
│   │   ├── validator.py         # OHLCV data validation
│   │   ├── ephemeris.py         # Swiss Ephemeris precomputation
│   │   ├── news_processor.py    # FinBERT/GLM-4 sentiment pipeline
│   │   ├── storage.py           # TimescaleDB upsert and queries
│   │   └── ...
│   ├── pat-master/      # Master Decision Layer service
│   │   ├── main.py
│   │   ├── api.py
│   │   ├── normalization.py     # Linear range mapping
│   │   ├── weighting.py         # Dynamic weight computation (Sharpe, regime, temporal)
│   │   ├── independence.py      # Jaccard similarity overlap detection
│   │   ├── fusion.py            # Directional fusion with conflict detection
│   │   ├── scoring.py           # 15-dimension scoring framework
│   │   ├── override.py          # Hard override pipeline (DI Kala, CW mandatory flat, risk breakers)
│   │   ├── storage.py           # Persistence to TimescaleDB and Valkey
│   │   └── ...
│   ├── pat-api/         # Delivery Layer API Gateway
│   │   ├── main.py
│   │   ├── api.py               # REST API routers
│   │   ├── auth.py              # JWT and API key authentication
│   │   ├── websocket.py         # WebSocket hub implementation
│   │   ├── client.py            # Service clients for inter-service communication
│   │   ├── middleware.py        # Rate limiting, request logging, correlation IDs
│   │   └── ...
│   ├── pat-engine-ai/   # AI Signal Engine (Independent Analysis Layer)
│   │   ├── main.py
│   │   ├── api.py               # /analyze endpoint
│   │   ├── glm4_client.py       # GLM-4 Flash/Long integration
│   │   ├── prompt_templates.py  # Prompt template system
│   │   ├── caching.py           # Valkey-based response caching
│   │   └── ...
│   ├── pat-engine-di/   # Discretionary Intelligence Engine
│   │   ├── main.py
│   │   ├── api.py
│   │   ├── swisseph.py          # PySwissEph wrappers
│   │   ├── shadbala.py          # Shadbala 4-component analysis
│   │   ├── dasha.py             # Vimshottari Dasha calculations
│   │   ├── aspects.py           # Planetary aspects with Gaussian orb model
│   │   └── ...
│   ├── pat-engine-cw/   # Chinese Wisdom Engine
│   │   ├── main.py
│   │   ├── api.py
│   │   ├── calendar.py          # Chinese lunisolar calendar
│   │   ├── bazi.py              # BaZi 4 Pillars/12 Day Officers
│   │   ├── flying_stars.py      # Feng Shui 9 Flying Stars
│   │   ├── five_elements.py     # Five Elements generative/control cycles
│   │   └── ...
│   ├── pat-engine-wa/   # Western Astrology Engine
│   │   ├── main.py
│   │   ├── api.py
│   │   ├── tropical.py          # Tropical ephemeris calculations
│   │   ├── natal_chart.py       # Gold natal chart (Nixon Shock)
│   │   ├── transits.py          # Transit aspects and retrograde flags
│   │   └── ...
│   ├── pat-engine-smc-ict/ # SMC-ICT Engine
│   │   ├── main.py
│   │   ├── api.py
│   │   ├── bos_mss.py           # Break of Structure / Market Structure Shift
│   │   ├── order_block.py       # Order Block identification
│   │   ├── fvg.py               # Fair Value Gap mapping
│   │   ├── liquidity_sweep.py   # Liquidity sweep detection
│   │   └── ...
│   ├── pat-engine-vision/ # Vision Engine
│   │   ├── main.py
│   │   ├── api.py
│   │   ├── chart_renderer.py    # Matplotlib/Plotly chart rendering
│   │   ├── glm4v_client.py      # GLM-4V image submission pipeline
│   │   ├── parallel_analysis.py # 10-agent parallel analysis
│   │   └── ...
│   ├── pat-engine-macro/  # Macro Engine
│   │   ├── main.py
│   │   ├── api.py
│   │   ├── cot_parser.py        # COT report parsing
│   │   ├── economic_calendar.py # Economic calendar integration
│   │   ├── central_bank.py      # Central bank rate tracker
│   │   └── ...
│   ├── pat-engine-technical/ # Technical Structure Engine
│   │   ├── main.py
│   │   ├── api.py
│   │   ├── indicators.py        # 33 technical indicators
│   │   ├── harmonics.py         # Harmonic pattern detection
│   │   ├── elliott_wave.py      # Elliott Wave analysis
│   │   ├── support_resistance.py # Support/resistance level identification
│   │   └── ...
│   ├── pat-engine-sentiment/ # Sentiment Engine
│   │   ├── main.py
│   │   ├── api.py
│   │   ├── finbert.py           # FinBERT inference pipeline
│   │   ├── social_media.py      # Social media sentiment aggregation
│   │   ├── options_flow.py      # Options flow analysis
│   │   └── ...
│   ├── pat-engine-intermarket/ # Intermarket Engine
│   │   ├── main.py
│   │   ├── api.py
│   │   ├── correlation.py       # Cross-asset correlation matrix
│   │   ├── etf_flow.py          # ETF flow ingestion and analysis
│   │   ├── futures_basis.py     # Futures basis calculation
│   │   └── ...
│   ├── pat-execution/     # Execution Layer service
│   │   ├── main.py
│   │   ├── api.py               # Health check and config endpoints
│   │   ├── zeromq_bridge.py     # ZeroMQ Bridge v2 (ROUTER/DEALER + PUB/SUB)
│   │   ├── hmac_signer.py       # HMAC-SHA256 message signing with key rotation
│   │   ├── mql5_adapter.py      # MQL5 Expert Advisor v2 protocol translation
│   │   ├── crypto_gateway.py    # Unified Binance/OKX REST/WebSocket abstraction
│   │   ├── paper_trading.py     # Paper trading engine with latency/slippage/fill models
│   │   ├── risk_manager.py      # Kelly criterion, correlation-adjusted VaR, circuit breakers
│   │   └── ...
│   └── shared/          # Shared libraries and cross-cutting concerns
│       ├── contracts/         # JSON Schema definitions (engine output, master verdict)
│       ├── db/                # Database connection, session management, base models
│       ├── auth/              # Authentication utilities (JWT, HMAC tokens)
│       ├── utils/             # Common utilities (logging, configuration, helpers)
│       └── ...
├── frontend/            # Next.js 15 Application (Delivery Layer)
│   ├── pages/           # App Router pages
│   ├── components/      # Reusable React components
│   ├── lib/             # Utility functions, API clients, WebSocket hooks
│   ├── styles/          # TailwindCSS configuration and custom styles
│   ├── public/          # Static assets
│   └── ...
├── config/              # Configuration files (YAML, environment)
│   ├── .env             # Environment variables template
│   ├── pat-data.yaml
│   ├── pat-master.yaml
│   ├── pat-api.yaml
│   ├── pat-frontend.yaml
│   ├── pat-engine-*.yaml (one per engine)
│   └── pat-execution.yaml
├── scripts/             # Utility and automation scripts
│   ├── backup.sh        # Backup and restore procedures
│   ├── migrate.sh       # Database migration runner
│   ├── setup.sh         # Development environment setup
│   ├── test.sh          # Test runner
│   └── ...
├── tests/               # Test suite
│   ├── unit/            # Unit tests for individual modules
│   ├── integration/     # Integration tests for service interactions
│   └── e2e/             # End-to-end tests (Playwright for frontend, pytest for backend)
├── docker/              # Dockerfiles and Compose files
│   ├── production/      # Production Dockerfiles (multi-stage builds)
│   │   ├── api.Dockerfile
│   │   ├── engine.Dockerfile
│   │   ├── frontend.Dockerfile
│   │   └── ...
│   └── compose/         # Docker Compose environments
│       ├── dev.yml      # Local development
│       └── prod.yml     # Production-like deployment
├── systemd/             # Systemd unit files for production deployment
│   ├── pat-data.service
│   ├── pat-master.service
│   ├── pat-api.service
│   ├── pat-frontend.service
│   ├── pat-engine-*.service
│   └── pat-execution.service
├── docs/                # Documentation (as provided in the repository)
├── contracts/           # Versioned JSON Schema and OpenAPI specifications
│   ├── engine-output-contract-v2.0.json
│   ├── master-verdict-contract-v2.0.json
│   └── api-contract-v2.0.yaml
├── migrations/          # Alembic database migrations
│   ├── versions/
│   │   └── <timestamp>_<description>.py
│   ├── alembic.ini
│   └── env.py
└── README.md
```

## 2. Module Interfaces

Each backend service follows a clean, modular architecture with well-defined interfaces:

- **API Layer (`api.py`)**: FastAPI application setup, route definitions, dependency injection, request/response validation.
- **Business Logic Layer**: Domain-specific implementations (e.g., scoring algorithms, data ingestion pipelines, analysis engines) encapsulated in dedicated modules.
- **Data Access Layer (`storage.py`)**: Abstracts database interactions (TimescaleDB upserts, queries) and cache/bus interactions (Valkey Pub/Sub, Streams).
- **External Integrations**: Clients for third-party APIs (TwelveData, GLM-4, Binance, etc.) with retry/backoff and circuit breaker patterns.
- **Cross-Cutting Concerns (shared modules)**: Logging, authentication, configuration loading, error handling, metrics collection.

Services communicate via:
- **Synchronous**: HTTP REST/JSON (engine analysis, API gateway requests).
- **Asynchronous**: Valkey Streams (engine outputs → master verdicts, master verdicts → execution) and Valkey Pub/Sub (market data availability, alerts, system events).
- **Database**: Direct TimescaleDB connections (read‑only for most services, write‑only for data‑owning services).

## 3. Data Schemas

### 3.1 Engine Output Contract
All independent analysis engines emit a validated JSON contract conforming to the following schema (simplified; full JSON Schema in `contracts/engine-output-contract-v2.0.json`):

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Engine Output Contract",
  "type": "object",
  "required": ["instrument_id", "timeframe", "timestamp", "engine_name", "score"],
  "properties": {
    "instrument_id": {
      "type": "string",
      "description": "Standardized instrument identifier (e.g., ESZ24, BTCUSD)"
    },
    "timeframe": {
      "type": "string",
      "enum": ["M1", "M5", "M15", "H1", "H4", "D1"],
      "description": "Candlestick timeframe"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "UTC timestamp of the analysis completion"
    },
    "engine_name": {
      "type": "string",
      "enum": [
        "ai", "di", "cw", "wa", "smc-ict", "vision",
        "macro", "technical", "sentiment", "intermarket"
      ],
      "description": "Identifier of the emitting engine"
    },
    "score": {
      "type": "number",
      "description": "Raw engine score within engine‑specific range (see DETAILED_SOW.md)",
      "minimum": -120,
      "maximum": 120
    },
    "confidence": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0,
      "default": 1.0,
      "description": "Confidence in the engine output (optional)"
    },
    "metadata": {
      "type": "object",
      "description": "Engine‑specific additional data (optional)",
      "additionalProperties": true
    }
  },
  "additionalProperties": false
}
```

### 3.2 Master Verdict Contract
The Master Engine emits a validated JSON contract representing the canonical tradable score and eligibility:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Master Verdict Contract",
  "type": "object",
  "required": [
    "instrument_id", "timeframe", "timestamp",
    "verdict_score", "verdict_direction",
    "dimension_scores", "hash"
  ],
  "properties": {
    "instrument_id": {
      "type": "string",
      "description": "Instrument identifier"
    },
    "timeframe": {
      "type": "string",
      "enum": ["M1", "M5", "M15", "H1", "H4", "D1"],
      "description": "Candlestick timeframe"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "UTC timestamp of verdict generation"
    },
    "verdict_score": {
      "type": "number",
      "description": "Aggregated score after weighting, normally‑scaled to [-100, +100]",
      "minimum": -100,
      "maximum": 100
    },
    "verdict_direction": {
      "type": "string",
      "enum": ["bullish", "bearish", "neutral", "hedge", "flat"],
      "description": "Directional recommendation derived from verdict_score"
    },
    "dimension_scores": {
      "type": "object",
      "description": "Scores for each of the 15 MOIL dimensions",
      "additionalProperties": {
        "type": "number",
        "minimum": -1.0,
        "maximum": 1.0
      },
      "minProperties": 15,
      "maxProperties": 15
    },
    "override_applied": {
      "oneOf": [
        { "type": "string" },
        { "type": "null" }
      ],
      "description": "Name of the override gate that forced a FLAT verdict, if any"
    },
    "conflicts": {
      "type": "array",
      "description": "List of detected engine conflicts (if directional fusion flagged HEDGE)",
      "items": {
        "type": "object",
        "properties": {
          "engine_a": { "type": "string" },
          "engine_b": { "type": "string" },
          "conflict_metric": { "type": "number" }
        },
        "required": ["engine_a", "engine_b", "conflict_metric"],
        "additionalProperties": false
      }
    },
    "hash": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$",
      "description": "SHA‑256 immutability hash covering the verdict and all inputs"
    },
    "version": {
      "type": "string",
      "default": "2.0",
      "description": "Contract schema version"
    }
  },
  "additionalProperties": false
}
```

### 3.3 Key Database Tables (TimescaleDB Hypertables)

| Table | Description | Key Columns |
|-------|-------------|-------------|
| `market.ohlcv_data` | Raw market data | `time`, `instrument_id`, `timeframe`, `open`, `high`, `low`, `close`, `volume` |
| `astro.ephemeris_cache` | Precomputed planetary positions | `time`, `body_id`, `coordinate_system`, `right_ascension`, `declination` |
| `macro.news_feed` | Sentiment‑scored news events | `time`, `source`, `headline`, `sentiment_score`, `relevance_score` |
| `signals.engine_outputs` | Immutable engine outputs | `time`, `instrument_id`, `timeframe`, `engine_name`, `score`, `confidence`, `metadata_json` |
| `signals.master_verdicts` | Master verdicts with SHA‑256 hashes | `time`, `instrument_id`, `timeframe`, `verdict_score`, `verdict_direction`, `dimension_scores_json`, `override_applied`, `hash` |
| `signals.master_conflicts` | Detected conflicts between engines | `time`, `instrument_id`, `timeframe`, `engine_a`, `engine_b`, `conflict_metric` |
| `signals.master_overrides` | Applied override gates | `time`, `instrument_id`, `timeframe`, `override_name`, `trigger_condition` |
| `audit.events` | Security and operations audit trail | `time`, `event_type`, `actor`, `outcome`, `details_json` |
| `execution.orders` | Order lifecycle tracking | `time`, `instrument_id`, `order_id`, `side`, `type`, `price`, `quantity`, `status` |
| `execution.positions` | Position and PnL tracking | `time`, `instrument_id`, `position_size`, `average_price`, `unrealized_pnl`, `realized_pnl` |

## 4. Command Hierarchy

The platform provides a modular CLI (`pat` command) for operational tasks, service management, and data inspection. Each command is a self‑contained file under `src/pat-cli/` (conceptual; actual implementation follows the `feat(cli):` convention).

```
pat
├── service
│   ├── list          # List all services and their status
│   ├── start <name>  # Start a service
│   ├── stop <name>   # Stop a service
│   ├── restart <name># Restart a service
│   └── status <name> # Detailed status of a service
├── verdict
│   ├── get <instrument> <timeframe>   # Latest Master Verdict
│   └── history <instrument> <timeframe> [--limit N] [--offset N] # Paginated history
├── engine
│   ├── list                              # List all engine services
│   ├── output <engine> <instrument> <timeframe>   # Engine Output Contract
│   └── test <engine>                     # Run deterministic reproducibility test
├── config
│   ├── show [service]                    # Show configuration (masking secrets)
│   └── set <service> <key> <value>       # Update configuration value
├── alert
│   ├── list                              # List configured alerts
│   ├── create                            # Create a new alert (interactive)
│   ├── delete <id>                       # Delete an alert by ID
│   └── test <id>                         # Send a test notification
├── db
│   ├── migrate                           # Run pending Alembic migrations
│   ├── backup                            # Trigger a backup to Wasabi S3
│   └── restore <timestamp>               # Restore from WAL archive or backup
├── user
│   ├── list                              # List users (admin only)
│   ├── create                            # Create a new user
│   ├── password <username>               # Reset user password
│   └── role <username> <role>            # Assign role (Admin, Trader, Analyst, Viewer, Guest)
├── api-key
│   ├── list                              # List API keys (masked)
│   ├── create                            # Create a new API key
│   ├── revoke <id>                       # Revoke an API key
│   └── rotate <id>                       # Rotate an API key
├── export
│   ├── verdicts <instrument> [--format csv|json|pdf]   # Export verdict history
│   └── engines <engine> [--format csv|json]            # Export engine output history
├── version                              # Show version information
└── health                               # Overall system health endpoint aggregator
```

**Notes**:
- All commands output JSON by default (`--yaml` or `--table` flags may be available).
- Authentication‑requiring commands (e.g., `user`, `api-key`, `config set`) check for a valid JWT or API key in the environment (`PAT_API_TOKEN`) or prompt for credentials.
- Service management commands interact with systemd units via `sudo systemctl` (configured via sudoers for the `pat` user).
- The CLI is designed to be extensible; new subcommands are added as independent files.

## 5. Service Boundaries

| Service | Layer | Responsibility | Interfaces (in/out) |
|---------|-------|----------------|---------------------|
| **pat-data** | Data Foundation | Market data ingestion, validation, ephemeris precomputation, news sentiment processing, historical data storage | **In**: Market data provider APIs (TwelveData, Yahoo Finance, AlphaVantage), news/RSS feeds<br>**Out**: Valkey Pub/Sub `new_data:{symbol}:{timeframe}`, OHLCV/ephemeris/news writes to TimescaleDB |
| **pat-engine-*** (10 engines) | Independent Analysis | Isolated analysis producing immutable Engine Output Contracts | **In**: HTTP POST `/analyze` (instrument_id, timeframe, bar_count, ephemeris_position?), Valkey Pub/Sub `new_data:{symbol}:{timeframe}` (indirect via pat‑data)<br>**Out**: Valkey Streams `engine_outputs:{engine_name}` (consumer groups), HTTP `/analyze` response (Engine Output Contract) |
| **pat-master** | Master Decision | Normalizes, weights, deconflicts, scores, applies overrides, emits Master Verdict Contract | **In**: Valkey Streams `engine_outputs:*` (all engines), Valkey Pub/Sub `new_data:*` (for ephemeris/market context), HTTP health/config<br>**Out**: Valkey Streams `master_verdicts`, Valkey Pub/Sub `verdicts:{instrument}:{timeframe}`, TimescaleDB `signals.master_verdicts` |
| **pat-api** | Delivery Layer | REST API gateway, authentication, rate limiting, WebSocket hub, service client for inter‑service communication | **In**: External HTTPS requests (clients, frontend), Valkey Pub/Sub `verdicts:*` (for WebSocket fanout), service‑to‑service HMAC tokens<br>**Out**: JSON REST responses, WebSocket messages to authenticated clients, service‑to‑service requests (via internal clients) |
| **pat-frontend** | Delivery Layer | Next.js 15 Verdict Terminal UI: real‑time dashboard, instrument selector, dimension visualization, engine drill‑down, history table with export, alert configuration, authentication | **In**: pat‑api REST/WebSocket endpoints, config files<br>**Out**: User‑initiated actions (alert creation, config changes) sent to pat‑api |
| **pat-execution** | Execution Layer | Translates Master Verdict Contracts into actionable orders via ZeroMQ bridge, crypto gateways, paper trading, risk management | **In**: Valkey Streams `master_verdicts`, ZeroMQ EA connections, crypto exchange APIs<br>**Out**: ZeroMQ messages to EAs, order submissions to Binance/OKX, paper trade simulations, position/PnL updates to TimescaleDB |

## 6. API Endpoints

All API endpoints are served by the `pat-api` service (unless otherwise noted) and follow REST conventions. Base path: `/v2`.

### 6.1 REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/master/verdicts/{instrument}/{timeframe}` | Latest Master Verdict Contract |
| `GET` | `/master/verdicts/{instrument}/{timeframe}/history` | Paginated history of Master Verdict Contracts (query: `limit`, `offset`) |
| `GET` | `/engines/{engine}/outputs/{instrument}/{timeframe}` | Engine Output Contract for a specific engine |
| `GET` | `/instruments` | Instrument registry with metadata (asset class, pip size, lot size, trading hours) |
| `POST` | `/backtest` | Historical backtesting interface (payload: instrument, timeframe, start, end, parameters) |
| `GET` | `/health` | Service health status (liveness/readiness) |
| `POST` | `/auth/login` | JWT authentication (returns access & refresh tokens) |
| `POST` | `/api-keys` | Create a new API key (returns key ID and secret; secret shown only once) |

### 6.2 WebSocket Channels

All WebSocket connections are authenticated via JWT (query param `token` or Authorization header). Base URL: `wss://<host>/ws`.

| Channel | Description |
|---------|-------------|
| `verdicts` | Real‑time Master Verdict Contract updates (message: Master Verdict Contract) |
| `engines` | Individual engine output streams (message: Engine Output Contract) |
| `instruments` | Instrument metadata updates (e.g., trading session changes) |
| `alerts` | Triggered alert notifications (message: alert payload) |
| `system` | System status and health updates (e.g., service downtime, backup completion) |

### 6.3 Authentication & Security

- **JWT**: HS256/RS256 tokens with refresh mechanism; short‑lived access token (15 min), long‑lived refresh token (7 days).
- **API Keys**: For service‑to‑service and trusted client access; HMAC‑SHA256 signing of requests.
- **Rate Limiting**: Token‑bucket algorithm; configurable per‑endpoint and per‑IP/API‑key limits.
- **Input Validation**: Pydantic v2 (FastAPI) for request bodies; query parameter validation.
- **Output Encoding**: Automatic JSON encoding; frontend uses React escaping to prevent XSS.
- **CORS**: Configured for trusted origins only.

## 7. Configuration Structure

Configuration follows a layered hierarchy: defaults in code → environment‑specific YAML files → environment variables → secrets (HashiCorp Vault). Secrets are never stored in files or environment variables; they are fetched at runtime from Vault via AppRole authentication.

### 7.1 Configuration Files

Each service has a corresponding YAML file in `config/` (e.g., `pat-master.yaml`). These files contain non‑secret configuration such as:

- Service host and port
- Database connection parameters (host, port, database name – **excluding** password)
- Valkey connection parameters (host, port – **excluding** password)
- External API endpoint URLs (without API keys)
- Feature flags and tuning parameters
- Logging levels
- Worker counts and timeouts

### 7.2 Environment Variables

Environment variables override YAML values and are used for:

- `ENVIRONMENT` (development, staging, production)
- `LOG_LEVEL` (override default)
- `PORT` (override service port)
- Secrets are **not** passed via environment variables; they are retrieved from Vault.

### 7.3 Secrets Management (HashiCorp Vault)

- **Authentication**: AppRole per service (role‑ID and secret‑ID stored securely in the host’s filesystem, readable only by the service user).
- **Dynamic Secrets**: Where possible (e.g., database passwords, API keys) Vault generates short‑lived credentials.
- **Static Secrets**: API keys for TwelveData, Binance, OKX, GLM‑4, etc. stored in Vault KV v2.
- **Secrets Rotation**: Configured via Vault policies and automated renewal (consul‑template or sidecar).
- **Audit Logging**: All Vault access is logged to `audit.events` via service‑side integration.

### 7.4 Example Configuration Snippet (`config/pat-master.yaml`)

```yaml
service:
  host: "0.0.0.0"
  port: 8005
  workers: 4
  timeout_keepalive: 5

database:
  host: "predictatrade_db"
  port: 5432
  database: "predictatrade"
  # username/password from Vault

valkey:
  host: "predictatrade_valkey"
  port: 6379
  # password from Vault

external:
  ephemeris_cache_hours: 1
  # URLs for external APIs (keys from Vault)

features:
  enable_override_logging: true
  scoring_cache_size: 1000

logging:
  level: "info"
  format: "json"
```

## 8. Cross‑Cutting Concerns

### 8.1 Logging
- Structured JSON with fields: `timestamp`, `level`, `message`, `service`, `trace_id`, `span_id`.
- Levels: TRACE (dev), DEBUG, INFO, WARN, ERROR, FATAL.
- Application logs retained 30 days; audit logs retained 7 years.
- No PII or secrets logged; automatic redaction patterns for tokens, keys, passwords.

### 8.2 Monitoring
- **Four Golden Signals**: latency, traffic, errors, saturation.
- **Business Metrics**: engine output volume and latency, master verdict distribution (bullish/bearish/neutral/hedge/flat), override gate trigger frequency, alert rates and MTTR, system uptime.
- Implemented via Prometheus client libraries in each service; Grafana dashboards per concern.

### 8.3 Observability
- Distributed tracing via trace/span IDs propagated in headers.
- Custom instrumentation for engine latency, verdict computation time, override evaluations.
- Health check endpoints (`/health`) for liveness and readiness.
- Runbook links embedded in alert notifications.

### 8.4 Security Architecture
- **Zero‑Trust Zones**:
  - Zone 0 (Public Internet) ↔ NGINX (TLS termination, WAF, rate limiting)
  - Zone 1 (DMZ) ↔ pat‑api (API gateway) ↔ pat‑frontend (SSR/CSR)
  - Zone 2 (Application Core, no direct internet) ↔ pat‑master ↔ pat‑engine‑* (HMAC token auth) ↔ pat‑data ↔ pat‑execution
  - Zone 3 (Data Layer) ↔ PostgreSQL + TimescaleDB (primary + replicas), Valkey (clustered, AOF+RDB), Wasabi S3 (encrypted backups, VPC‑endpoint only)
- **Authentication Hierarchy**:
  - Public: JWT or API key (Zone 1)
  - Service‑to‑Service: HMAC‑SHA256 tokens with nonce + timestamp (30‑second replay window) (Zone 2)
  - Database: Certificate or password authentication (Zone 3)
- **Encryption**:
  - At rest: PostgreSQL TDE or filesystem encryption, Valkey RDB/AOF encryption, Wasabi S3 server‑side encryption.
  - In transit: TLS 1.3 everywhere (NGINX termination; service‑to‑service where applicable); mutual TLS planned for high‑trust service communication.
- **Threat Mitigation**: parameterized queries, CSP headers, SameSite cookies, rate limiting, outbound traffic monitoring, privileged access logging, container image scanning, read‑only root filesystem where feasible.

### 8.5 Reliability & Resilience
- Retry logic with exponential backoff and jitter for external dependencies.
- Circuit breakers (Netflix Hystrix style) for unstable dependencies.
- Bulkheads (thread‑pool isolation) to prevent cascade failures.
- Idempotent external API calls.
- Explicit transaction boundaries for related DB operations.
- Health checks (liveness/readiness) and automatic restart on failure.
- Graceful degradation (e.g., continue with reduced engine set if non‑critical engines fail).

### 8.6 Scalability
- Horizontal scaling of stateless engine services behind round‑robin load balancing (NGINX or Valkey Pub/Sub fanout).
- API layer scaled with shared Valkey for rate‑limiting state.
- Frontend scaled via CDN‑cached static assets and SSR nodes behind load balancer.
- WebSocket hub scaled via shared Valkey Pub/Sub backplane.
- Database read replicas for API/frontend workloads.
- Automatic partitioning by time (TimescaleDB chunks) and partition‑by‑instrument/timeframe where beneficial.

### 8.7 Maintenance & Deployment
- **Development**: Docker Compose for local development with volume mounts for hot reloading.
- **Production**: Systemd service units (one per service) with resource limits (`MemoryMax`, `CPUQuota`), log forwarding to journald, automatic restart with exponential backoff.
- **CI/CD**: Multi‑stage Docker builds (build/test/production), automated schema migrations, security scanning (SAST/DAST/dependency), performance benchmarking, blue‑green deployment capability.
- **Backup & DR**: WAL archiving for point‑in‑time recovery, regular base backups with compression, encrypted offsite storage to Wasabi S3, MLflow artifact backup, regular restore testing, documented RTO/RPO.
- **Secrets Rotation**: Automated via Vault lease renewal and application‑side secret caching with background refresh.

This project structure provides a solid foundation for implementing the Predict‑A‑Trade vNext platform in accordance with the Master‑Orchestrated Intelligence Layer (MOIL) architecture, ensuring separation of concerns, scalability, security, and operational excellence.