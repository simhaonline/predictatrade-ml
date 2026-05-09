# Predict-A-Trade v2.0 — Core Architecture

> **Document Type:** Architecture Specification
> **Version:** 2.0.0
> **Date:** 2026-05-05
> **Scope:** Greenfield MOIL platform — full system architecture

---

## 1. Overview: The Master-Orchestrated Intelligence Layer (MOIL)

Predict-A-Trade v2.0 introduces the **Master-Orchestrated Intelligence Layer (MOIL)** — a hexagonal architecture where ten independent engine families contribute analysis to a single, authoritative **Master Engine** that adjudicates every verdict. No engine directly issues a trading recommendation; each produces a structured Engine Output Contract consumed exclusively by the Master Engine. The Master Engine normalises, cross-validates, deconflicts, weights, and scores all inputs across 15 independent dimensions before emitting a single Master Verdict Contract.

This architecture eliminates the architectural flaw of v1.x where multiple pillars could issue contradictory directional signals, forcing users to interpret conflicts themselves. In MOIL, the Master Engine is the sole verdict authority.

---

## 2. Six-Layer Architecture

### Layer 1 — Data Foundation

**Responsibility:** Market data ingestion, ephemeris computation, news aggregation, and time-series storage.

- OHLCV ingestion across 6 timeframes (M1, M5, M15, H1, H4, D1) for 187 instruments from TwelveData, Yahoo Finance, and AlphaVantage
- Swiss Ephemeris precomputation (2015-2030 cache) for 17 celestial bodies in both sidereal (Lahiri) and tropical coordinates
- News sentiment aggregation via FinBERT and Zhipu AI GLM-4, stored as scored event streams
- TimescaleDB hypertables with automated retention policies and continuous aggregates

**Service:** `pat-data` (Python 3.12, APScheduler, Celery workers on the `data` queue)

### Layer 2 — Independent Analysis

**Responsibility:** Ten engine families, each operating as an isolated, stateless analysis unit consuming only market data and ephemeris positions. Engines never communicate with each other — all cross-engine correlation is handled by the Master Engine.

The ten engine families:

| # | Engine Family | Domain | Score Range |
|---|---|---|---|
| 1 | AI Engine | GLM-4 reasoning, multi-pillar fusion, narrative generation | [-80, +80] |
| 2 | DI Engine | Vedic Jyotish — Shadbala, Dasha, Hora, Nakshatra, aspects | [-70, +70] |
| 3 | CW Engine | Chinese Wisdom — BaZi, Flying Stars, Five Elements, I-Ching | [-50, +50] |
| 4 | WA Engine | Western Astrology — tropical transits, natal aspects, retrogrades | [-30, +30] |
| 5 | SMC-ICT Engine | Smart Money Concepts — BOS/MSS, Order Blocks, FVG, liquidity sweeps | [0, +120] |
| 6 | Vision Engine | GLM-4V chart recognition — 10-agent parallel pipeline with conflict detection | [-100, +100] |
| 7 | Macro Engine | COT analytics, economic calendar, central bank rates, seasonality | [-60, +60] |
| 8 | Technical Engine | 33 indicators — Ichimoku, RSI, MACD, Bollinger, ADX, VWAP, harmonic patterns, Elliott Wave | [-80, +80] |
| 9 | Sentiment Engine | FinBERT news classification, social media sentiment, options flow | [-40, +40] |
| 10 | Intermarket Engine | Cross-asset correlation, ETF flows, futures basis, pairs signals | [-50, +50] |

Each engine is hosted as a dedicated service (`pat-engine-ai`, `pat-engine-di`, etc.) exposing a uniform `/analyze` endpoint.

**Services:** `pat-engine-{ai,di,cw,wa,smc,vision,macro,technical,sentiment,intermarket}`

### Layer 3 — Master Decision

**Responsibility:** The Master Engine is the sole verdict authority. It ingests up to ten Engine Output Contracts per analysis cycle and produces exactly one Master Verdict Contract.

Core functions:
- **Normalisation:** All engine directional scores are projected onto a common `[-1.0, +1.0]` normalized_direction_score using linear range mapping
- **Weighting:** A dynamic weight vector `W = [w_1, ..., w_10]` is computed per instrument/timeframe based on engine historical accuracy (rolling 90-day Sharpe), regime relevance (trending vs ranging), and temporal alignment
- **Independence Discounting:** When two engines share informational inputs (e.g., DI and WA both use planetary positions), their combined weight is discounted by an overlap coefficient to prevent double-counting
- **Conflict Resolution:** If engines disagree beyond a configurable threshold (`conflict_threshold = 0.4`), the Master Engine flags the verdict as `HEDGE` or `FLAT` rather than forcing a directional call
- **Hard Override Gates:** DI Kala penalty, CW mandatory flat, risk circuit breakers, exchange halts — any gate triggers immediate FLAT verdict regardless of composite score
- **15-Dimension Scoring:** The Master Engine evaluates every analysis cycle across 15 independent dimensions (see `technical-report.md` for the full framework)

**Service:** `pat-master` — the most security-critical component in the system. Runs in an isolated process with no direct internet access; communicates only over the internal service mesh.

### Layer 4 — Delivery

**Responsibility:** Serving verdicts to consumers via REST, WebSocket, and export pipelines.

- **REST API** (`pat-api`): FastAPI with 28 routers, JWT RBAC (5 roles), rate limiting, Prometheus instrumentation
- **WebSocket Hub**: 5 channels (price, signal, system, notification, admin) with JWT-authenticated connections and heartbeat protocol
- **Valkey Pub/Sub Bridge**: Bridges Master Verdict emissions from the internal service mesh to WebSocket subscribers
- **Export Pipeline**: MQL5 `.mqh` include files, JSON, CSV, PDF, Excel — all with cryptographic integrity checksums
- **Notification Dispatcher**: Email (SMTP), Telegram Bot API, Discord webhooks, Twilio SMS

**Services:** `pat-api`, `pat-frontend` (Next.js 15)

### Layer 5 — Execution

**Responsibility:** Translating Master Verdict Contracts into actionable orders at brokers and exchanges.

- **ZeroMQ Bridge** (`pat-execution`): ROUTER/DEALER + PUB/SUB protocol, forwarding verdicts to MQL5 Expert Advisors. The bridge signs each message with HMAC-SHA256 for EA-side verification.
- **Crypto Gateways**: Binance and OKX REST + WebSocket connectors with unified order abstraction
- **Paper Trading Engine**: Simulated execution with latency, slippage, and fill-probability models
- **Portfolio Manager**: CPortfolioManager with position sizing, risk-per-trade limits, and circuit breakers

### Layer 6 — Operations

**Responsibility:** Monitoring, observability, backup, disaster recovery, CI/CD.

- **Prometheus** metrics exported from every service via `prometheus_fastapi_instrumentator` and custom collectors
- **Grafana** dashboards (5 core: System Health, Signal Quality, Engine Performance, Data Pipeline, Business Metrics)
- **Loki** for structured log aggregation with structlog JSON formatting
- **MLflow** model registry and experiment tracking for XGBoost meta-model and GLM-4 fine-tuning runs
- **Wasabi S3** for encrypted offsite backups (WAL archiving, pg_dump, model artifacts)
- **Cloud Build / Gitea Actions** CI/CD with lint, test, security scan, and deploy gates

---

## 3. Service Topology

```
┌────────────────────────────────────────────────────────────────────┐
│                        NGINX (TLS 1.3, HTTP/2)                     │
│                     Reverse Proxy + Rate Limiting                   │
└──────┬─────────────┬──────────────┬──────────────┬─────────────────┘
       │             │              │              │
       ▼             ▼              ▼              ▼
┌──────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐
│pat-api   │  │pat-frontend│  │pat-master │  │prometheus │
│:8000     │  │:3001      │  │:9000      │  │:9090      │
│(internal)│  │(SSR+CSR)  │  │(internal) │  │           │
└────┬─────┘  └───────────┘  └─────┬──────┘  └───────────┘
     │                             │
     │    ┌────────────────────────┼──────────────────────────┐
     │    │          Internal Service Mesh (Valkey)           │
     │    │                                                  │
     │    │  ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │
     │    │  │pat-data  │ │pat-master│ │pat-engine-* (x10)│  │
     │    │  │(ingest)  │ │(verdict) │ │(analysis)        │  │
     └────┼──┤          │ │          │ │                  │  │
          │  └─────┬────┘ └────┬─────┘ └────────┬─────────┘  │
          │        │           │                │             │
          │        ▼           ▼                ▼             │
          │  ┌──────────────────────────────────────────┐     │
          │  │        PostgreSQL 16 + TimescaleDB       │     │
          │  │        13 schemas, 95+ tables            │     │
          │  └──────────────────────────────────────────┘     │
          │                                                   │
          │  ┌──────────┐  ┌──────────┐  ┌──────────────┐    │
          │  │grafana   │  │loki      │  │mlflow        │    │
          │  │:3000     │  │:3100     │  │:5000         │    │
          │  └──────────┘  └──────────┘  └──────────────┘    │
          └───────────────────────────────────────────────────┘
```

---

## 4. Inter-Service Communication Patterns

| Pattern | Transport | Use Case |
|---------|-----------|----------|
| **REST (JSON/ORJSON)** | HTTP/1.1 over internal network | Engine analysis requests, API queries, configuration reads |
| **WebSocket** | WSS via NGINX upgrade | Real-time verdict delivery, price streaming, admin alerts |
| **Valkey Pub/Sub** | TCP (valkey://) | Engine output publication, verdict broadcast, cache invalidation |
| **Valkey Streams** | TCP (valkey://) | Durable event sourcing for analysis pipelines, replay capability |
| **ZeroMQ (ROUTER/DEALER + PUB/SUB)** | TCP (zmq://) | MT4/MT5 bridge — signal delivery to trading terminals |
| **Celery (Valkey broker)** | TCP | Asynchronous task dispatch — OHLCV ingestion, engine compute, ML training |

All internal services authenticate via shared HMAC tokens provisioned at deploy time. The `pat-master` service has an allowlist of permitted callers and rejects all external-origin requests regardless of credentials.

---

## 5. Data Flow: End-to-End Pipeline

```
Market Data APIs ──► pat-data (ingestion) ──► TimescaleDB (ohlcv_data hypertable)
                                                   │
Swiss Ephemeris ────► pat-data (ephemeris cache) ──┘
                                                   │
                          ┌────────────────────────┘
                          ▼
              ┌───────────────────────┐
              │  Valkey Pub/Sub       │  "new_data:{symbol}:{timeframe}"
              │  Data Availability    │
              └──────────┬────────────┘
                         │
          ┌──────────────┼──────────────┬──────────────┐
          ▼              ▼              ▼              ▼
    pat-engine-ai  pat-engine-di  pat-engine-smc  ... (x10)
          │              │              │
          │  Engine Output Contracts (JSON, validated)  │
          │              │              │
          └──────────────┼──────────────┘
                         ▼
              ┌───────────────────────┐
              │    pat-master         │
              │    Master Engine      │
              │                       │
              │  1. Normalise (all)   │
              │  2. Independence check│
              │  3. Weight compute    │
              │  4. Directional fusion│
              │  5. 15-dim scoring    │
              │  6. Override gates    │
              │  7. Verdict emit      │
              └───────────┬───────────┘
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
    ┌─────────────────┐     ┌─────────────────┐
    │ pat-api         │     │ pat-execution   │
    │ REST + WS       │     │ ZMQ + Gateways  │
    │ Verdict delivery│     │ Order routing   │
    └────────┬────────┘     └────────┬────────┘
             ▼                       ▼
    ┌─────────────────┐     ┌─────────────────┐
    │ pat-frontend    │     │ MT5 EA / Crypto │
    │ Verdict Terminal│     │ Exchange        │
    └─────────────────┘     └─────────────────┘
```

---

## 6. Deployment Architecture

Every service runs as a **systemd unit** on AlmaLinux, managed through a unified Makefile:

```bash
# Service lifecycle
make start-all      # systemctl start pat-api pat-master pat-data pat-engine-* pat-frontend
make stop-all       # systemctl stop (reverse order)
make restart-all    # rolling restart with health-check gating
make status         # systemctl status --all pat-*
```

**systemd unit template** (applied to all `pat-*` services):
```
[Unit]
Description=Predict-A-Trade — {service}
After=network.target valkey.service postgresql.service

[Service]
Type=simple
User=pat
Group=pat
WorkingDirectory=/srv/predictatrade.com
ExecStart=/opt/conda/envs/pat-api/bin/uvicorn app.main:app --host 127.0.0.1 --port {port} --workers {workers}
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**NGINX** terminates TLS 1.3, enforces HSTS/CSP headers, applies per-endpoint rate limits (200 req/min global, 30 req/min for signal generation), and proxies to internal services via Unix sockets where possible or localhost TCP.

---

## 7. Technology Stack Rationale

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **API Framework** | FastAPI (Python 3.12) | Native async, Pydantic v2 validation, automatic OpenAPI, superior WebSocket support |
| **Database** | PostgreSQL 16 + TimescaleDB | Time-series optimisation via automatic partitioning, continuous aggregates, 10-100x query improvement on OHLCV scans |
| **Cache/Broker** | Valkey 8.x | Redis-compatible with per-core scaling, IO threads, and dual-channel replication |
| **Frontend** | Next.js 15 | App Router, React Server Components, streaming SSR, ISR for verdict pages |
| **Task Queue** | Celery 5.x (Valkey broker) | Mature Python ecosystem, priority queues, chord/chain/group primitives for engine orchestration |
| **AI/ML** | XGBoost + GLM-4 + FinBERT | XGBoost for SHAP-explainable meta-modelling; GLM-4 for multi-modal reasoning; FinBERT for domain-specific sentiment |
| **Ephemeris** | PySwissEph 2.10 | Deterministic, offline, sub-millisecond planetary position computation to arcsecond precision |
| **Execution Bridge** | ZeroMQ (libzmq) | Sub-millisecond message routing, native PUB/SUB, battle-tested in financial systems |
| **Monitoring** | Prometheus + Grafana + Loki | Industry standard, native FastAPI integration, Loki for structured log querying |
| **Experiment Tracking** | MLflow | Model versioning, parameter logging, artifact management, REST API for automated retraining |
| **Web Server** | NGINX | TLS 1.3 termination, HTTP/2, rate limiting, mod_security WAF integration, battle-tested at scale |

---

## 8. Scaling Strategy

- **Horizontal Engine Scaling:** Each `pat-engine-*` service is stateless and can be replicated behind a round-robin load balancer. Engine instances share no state — they read inputs from TimescaleDB and publish outputs to Valkey.
- **Database Read Replicas:** The `pat-api` and `pat-frontend` read paths (dashboards, historical verdict queries) route to TimescaleDB read replicas. The write path (ingestion, verdict persistence) routes to the primary.
- **Valkey Cluster:** As the broker/cache layer becomes saturated, Valkey can be sharded across nodes with hash-slot distribution, transparent to Celery and Pub/Sub clients.
- **WebSocket Fanout:** The WebSocket hub can be scaled horizontally with a shared Valkey Pub/Sub backplane — each instance subscribes to the same channels and fans out to its connected clients independently.

---

## 9. Security Boundaries and Trust Model

```
┌──────────────────────────────────────────────────────────┐
│  Zone 0 — Public Internet                                │
│  (Untrusted — all inputs validated, rate-limited)        │
└────────────────────┬─────────────────────────────────────┘
                     │ NGINX (TLS termination, WAF, CSP, HSTS)
┌────────────────────▼─────────────────────────────────────┐
│  Zone 1 — DMZ                                           │
│  pat-api, pat-frontend                                    │
│  (Authenticated users, JWT tokens, RBAC enforcement)     │
└────────────────────┬─────────────────────────────────────┘
                     │ Internal API only (127.0.0.1 or Unix socket)
┌────────────────────▼─────────────────────────────────────┐
│  Zone 2 — Application Core                              │
│  pat-master, pat-engine-*, pat-data, pat-execution       │
│  (No direct internet access. Service-to-service auth.)   │
└────────────────────┬─────────────────────────────────────┘
                     │ Local socket / localhost
┌────────────────────▼─────────────────────────────────────┐
│  Zone 3 — Data Layer                                    │
│  PostgreSQL, Valkey, Wasabi S3 (encrypted at rest)      │
│  (No outbound network access except S3 via VPC endpoint)  │
└──────────────────────────────────────────────────────────┘
```

**Trust Model:**
- The Master Engine (`pat-master`) is the highest-trust component — its output is authoritative. It must never be exposed to the public internet.
- Engine services are medium-trust — they produce advisory outputs, never directives.
- The execution layer (`pat-execution`) is high-trust (it moves money) and requires explicit human approval or hard risk limits for live trading.
- All inter-service communication within Zone 2 uses HMAC-signed messages with replay protection (nonce + timestamp validation, 30-second window).

---

*Architecture document — v2.0.0. All specifications target the greenfield MOIL platform rebuild.*
