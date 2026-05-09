# Predict-A-Trade v2.0 — Execution Plan

> **Document Type:** Development Roadmap & Resource Plan
> **Version:** 2.0.0
> **Date:** 2026-05-05
> **Scope:** 10-phase greenfield rebuild — Phase 0 through Phase 9

---

## 1. Overview

This execution plan defines the 10-phase roadmap for rebuilding Predict-A-Trade as a greenfield MOIL platform. The build is scoped as a complete rewrite — no legacy v1.x code is carried forward, though architectural lessons, theoretical frameworks, and domain knowledge (Swiss Ephemeris integration, I-Ching encoding, Shadbala computation) are preserved.

**Estimated total duration:** 16-20 weeks with a 4-person core team plus domain specialists.

---

## 2. Team Structure

| Role | Count | Responsibility |
|------|-------|----------------|
| **Platform Architect / Tech Lead** | 1 | MOIL design, Master Engine, contract definitions, critical path decisions |
| **Backend Engineers** | 2 | API, engine implementations, data pipeline, Celery workers |
| **Frontend Engineer** | 1 | Verdict Terminal (Next.js 15), real-time visualisations, admin panel |
| **Domain Specialists (part-time)** | 3 | Vedic astrology, Chinese metaphysics, quantitative validation |

---

## 3. Phase Roadmap

### Phase 0 — Product Definition & SOW Approval (Week 1)

**Objective:** Lock scope, contracts, and acceptance criteria before a single line of code is written.

**Milestones:**
- Finalise the Engine Output Contract JSON schema with all required/optional fields, enumerated values, and validation rules
- Finalise the Master Verdict Contract JSON schema with all 15 scoring dimensions
- Define API surface: endpoint paths, request/response shapes, error codes, pagination standard
- Document the 15-dimension scoring framework with exact formulae and thresholds
- Produce and approve the Statement of Work (SOW) with phase-gate criteria for each subsequent phase
- Establish the monorepo structure, linting rules (ruff, mypy strict, eslint), pre-commit hooks, and branch protection policies

**Gate:** SOW signed by all stakeholders. Contracts published as versioned JSON Schema documents in `/contracts/`.

---

### Phase 1 — Infrastructure (Weeks 2-3)

**Objective:** Provision every service and system that code will run on.

**Milestones:**
- Provision AlmaLinux VPS/dedicated server with firewall (iptables/nftables), SELinux enforcing, and SSH key-only access
- Install and configure PostgreSQL 16 with TimescaleDB extension, tuned for OLAP workloads (`shared_buffers`, `work_mem`, `effective_cache_size`)
- Install Valkey 8.x with persistence (AOF + RDB), configure as Celery broker and cache
- Deploy NGINX with TLS 1.3 certificates (Let's Encrypt via certbot), HTTP/2, CSP/HSTS headers
- Set up Prometheus node exporters on all hosts, deploy Grafana with initial dashboards, configure Loki with structlog JSON pipeline
- Create systemd unit files for all `pat-*` services with resource limits (MemoryMax, CPUQuota)
- Establish Wasabi S3 bucket with lifecycle policies for backup rotation and IAM access keys
- Configure CI/CD pipeline (Cloud Build or Gitea Actions) with build caching, multi-stage Dockerfiles, and automated DB migration execution

**Gate:** All infrastructure services respond to health checks. PostgreSQL accepts connections. Valkey ping returns PONG. NGINX serves HTTPS.

---

### Phase 2 — Contracts (Weeks 2-3, parallel with Phase 1)

**Objective:** Define every interface before any implementation begins.

**Milestones:**
- Publish `engine-output-contract-v2.0.json` — JSON Schema for all ten engine families with shared envelope (`engine_id`, `timestamp`, `instrument`, `timeframe`, `normalized_direction_score`, `calibrated_confidence`, `evidence_quality`, `raw_factors`, `sha256_checksum`)
- Publish `master-verdict-contract-v2.0.json` — JSON Schema for the Master Engine output with all 15 dimensions, recommendation band, and immutability hash
- Publish `api-contract-v2.0.yaml` — OpenAPI 3.1 specification covering all v2 endpoints (`/v2/master/verdicts`, `/v2/engines/`, `/v2/instruments/`, `/v2/backtest/`)
- Define database schema via Alembic migration skeleton — all tables, hypertables, ENUMs, indexes, and foreign keys declared before Phase 3 data platform work
- Define inter-service authentication protocol (HMAC token format, nonce structure, replay window)
- Publish WebSocket channel specification (5 channels, message formats, heartbeat interval, reconnection strategy)

**Gate:** All contracts version-tagged in `/contracts/v2.0/`. Schema validators run in CI. No implementation deviates from contracts.

---

### Phase 3 — Data Platform (Weeks 3-5)

**Objective:** Build the data foundation that all engines read from.

**Milestones:**
- **Ingestion Pipeline:** TwelveData/Yahoo/AlphaVantage provider abstraction, OHLCV fetch with exponential backoff retry, upsert to TimescaleDB hypertable `market.ohlcv_data`
- **Instrument Registry:** 187-instrument seed script with asset class, pip size, lot size, trading hours, and session metadata
- **Ephemeris Cache (2015-2030):** Precompute all 17 celestial body positions at 1-hour granularity in both sidereal (Lahiri) and tropical coordinates. Store in TimescaleDB hypertable `astro.ephemeris_cache` with composite index on `(timestamp, body_id, coordinate_system)`
- **News Feed:** RSS/API aggregation pipeline feeding into `macro.news_feed` hypertable with FinBERT sentiment scoring as a Celery task on ingestion
- **Data Validation Layer:** Schema validation on every ingested bar (OHLC ordering, volume non-negative, timestamp monotonicity). Quarantine table for rejected data with alerting.
- **Retention Policies:** TimescaleDB automated drop_chunks policies — ticks 7 days, M1 bars 90 days, D1 bars 10 years

**Gate:** 187 instruments seeded. 6 timeframes ingest successfully. Ephemeris cache queryable for any timestamp in range.

---

### Phase 4 — Independent Engines (Weeks 4-9)

**Objective:** Build all ten engine families in isolation, each as a dedicated `pat-engine-*` service with uniform interface.

**Build Order (critical path — longest first):**
1. **AI Engine** (Week 4-6) — GLM-4 Flash/Long integration, prompt templates, structured output parsing, response caching
2. **DI Engine** (Week 4-6) — PySwissEph wrappers, Shadbala 4-component, Vimshottari Dasha L1/L2/L3, Hora, Nakshatra, major+minor aspects with Gaussian orb model, Kala penalty gates
3. **SMC-ICT Engine** (Week 5-7) — BOS/MSS detection, Order Block identification, FVG mapping, liquidity sweep detection, OTE zone computation, confluence scoring
4. **Vision Engine** (Week 5-7) — Chart rendering (matplotlib/plotly), GLM-4V image submission, 10-agent pipeline with conflict detection and fusion scoring
5. **Technical Engine** (Week 6-7) — 33 indicators (Ichimoku 5-line, RSI, MACD, Bollinger, ADX, VWAP, Stochastic, CCI, OBV, Williams %R, etc.), harmonic patterns (6 types with Fibonacci validation), Elliott Wave (5-impulse + ABC corrective)
6. **CW Engine** (Week 6-8) — Chinese lunisolar calendar, BaZi 4 Pillars/12 Day Officers, Feng Shui 9 Flying Stars (annual/monthly/daily), Five Elements generative/control cycles, I-Ching 64-hexagram encoding (3 methods)
7. **WA Engine** (Week 7-8) — Tropical ephemeris, Gold natal chart (Nixon Shock 1971-08-15), transit aspects, retrograde flags, synodic cycles
8. **Macro Engine** (Week 7-8) — COT report parsing and analytics, economic calendar integration, central bank rate tracker, seasonality patterns
9. **Sentiment Engine** (Week 8-9) — FinBERT inference pipeline, social media aggregation, options flow analysis
10. **Intermarket Engine** (Week 8-9) — Cross-asset correlation matrix, ETF flow ingestion, futures basis computation, pairs divergence detection

**Each engine must:**
- Accept identical request shape: `{ instrument_id, timeframe, bar_count, ephemeris_position? }`
- Return a validated Engine Output Contract
- Pass contract schema validation in its test suite
- Include a deterministic test case with known inputs producing known output (reproducibility gate)
- Be deployable as an independent systemd service

**Gate:** All ten engine services start, accept `/analyze` requests, and return schema-valid Engine Output Contracts. Each engine has at least one deterministic reproducibility test.

---

### Phase 5 — Master Engine (Weeks 8-11, overlapping with late Phase 4 engines)

**Objective:** Build the adjudication layer that consumes engine outputs and produces authoritative verdicts.

**Milestones:**
- **Normalisation Engine:** Linear range mapping — project every engine's native score range onto `[-1.0, +1.0]` with configurable clipping
- **Weight Computation:** Dynamic weight vector per instrument/timeframe using rolling 90-day engine Sharpe ratio, regime classifier output (trending vs ranging vs breakout), and temporal alignment scoring
- **Independence Discounting:** Overlap detection matrix between engine pairs (DI↔WA via shared ephemeris inputs, AI↔Sentiment via shared GLM-4 API). Discount combined weight by `1 - overlap_coefficient` where coefficient is the Jaccard similarity of input feature sets
- **Directional Fusion:** `weighted_direction = Σ(w_i * normalized_direction_i)` with conflict detection — if standard deviation of engine directions exceeds `conflict_threshold`, flag as HEDGE
- **15-Dimension Scoring:** Full implementation of all 15 scoring dimensions (see `technical-report.md`)
- **Hard Override Pipeline:** Ordered evaluation of DI Kala penalty gates, CW mandatory flat threshold, risk circuit breakers, exchange halts, session boundaries
- **Verdict Emission:** Publish Master Verdict Contract to Valkey Pub/Sub channel `verdicts:{instrument}:{timeframe}` and persist to TimescaleDB `signals.master_verdicts` hypertable
- **SHA-256 Immutability:** Every verdict includes a content-hash covering all inputs and the computed output. Replay verification computes the same hash and compares.

**Gate:** Master Engine correctly adjudicates 100+ precomputed test scenarios with known expected outputs. All override gates fire correctly. SHA-256 immutability verified on replay.

---

### Phase 6 — Research & Validation (Weeks 10-13)

**Objective:** Statistically validate that MOIL produces measurable alpha.

**Milestones:**
- **Walk-Forward Analysis:** Expanding-window validation across 2020-2026, training on 90-day rolling windows, testing on subsequent 30-day windows. Metrics: Sharpe ratio, Calmar ratio, win rate, profit factor, max drawdown.
- **Historical Replay:** Replay 2024-2025 market data through the full MOIL pipeline. Compare emitted verdicts against actual subsequent price movement. Measure directional accuracy, average favourable excursion, average adverse excursion.
- **Baseline Comparisons:** Run three system configurations: B1 (technical indicators only), B2 (all quantitative engines), B3 (full MOIL with all ten engines including metaphysical). Compare via Diebold-Mariano test on squared forecast errors.
- **SHAP Decomposition:** For XGBoost meta-model, compute SHAP values to quantify each engine family's marginal contribution. Primary hypothesis test: metaphysical engine SHAP values must be non-zero and directionally stable across test windows.
- **Stress Testing:** Flash crash replay (2010, 2015, 2020), correlation breakdown scenarios, data feed interruption, engine failure modes.

**Gate:** Full MOIL (B3) demonstrates statistically significant improvement over technical-only baseline (B1) at p < 0.05 on Diebold-Mariano. Walk-forward Sharpe ratio > 1.0. Max drawdown < 25%.

---

### Phase 7 — Frontend & Delivery (Weeks 11-14)

**Objective:** Build the Verdict Terminal and all delivery channels.

**Milestones:**
- **Verdict Terminal** (Next.js 15 App Router): Dashboard with real-time Master Verdict display, instrument selector with search, timeframe switcher (M1-D1), 6-pillar radar hexagon visualisation (Recharts/D3), engine output drill-down per engine family
- **Verdict History:** Paginated table with sort/filter by instrument, timeframe, recommendation band, date range. Export to PDF (jsPDF), Excel (SheetJS), CSV, JSON.
- **WebSocket Real-Time:** 5-channel subscription with JWT authentication, automatic reconnection with exponential backoff, heartbeat keepalive. Verdict updates push to subscribed clients within 100ms of Master Engine emission.
- **Alert Configuration:** User-defined alert thresholds — direction change, conviction threshold crossing, override gate triggering, engine health degradation
- **Notification Delivery:** Email (SMTP + MJML templates), Telegram Bot, Discord webhook, SMS (Twilio) — all templated with verdict summary formatting
- **Mobile-Responsive Layout:** Verdict Terminal usable on tablet and phone viewports for trader mobility

**Gate:** `/qa` Playwright test suite passes on all core user journeys (view verdict, switch instrument, export report, configure alert). Lighthouse score > 90 on Performance.

---

### Phase 8 — Execution Integration (Weeks 13-16)

**Objective:** Verdicts become trades.

**Milestones:**
- **ZeroMQ Bridge v2:** Rewrite the MT4/MT5 bridge with proper framing protocol, HMAC-SHA256 message signing, sequence numbering for EA-side deduplication, and bidirectional health-check pings
- **MQL5 EA v2:** PredictATradeEA v2 consuming Master Verdict Contracts (not raw engine outputs). Strategy factory updated for MOIL recommendation bands. Circuit breakers with per-instrument max exposure limits.
- **Crypto Gateways:** Binance + OKX unified REST/WS connectors. Order abstraction layer supporting market, limit, stop-loss, and take-profit orders. Position tracking with realised/unrealised PnL.
- **Paper Trading Engine:** Realistic simulation with configurable latency distribution (log-normal), slippage model (proportional to spread + volatility), fill-probability function (decays with distance from mid-price). Generates execution reports comparable to live trading logs.
- **Portfolio Risk Manager:** CPortfolioManager v2 with Kelly criterion position sizing, per-instrument max allocation, total exposure cap, correlation-adjusted VaR, and hard stop-loss circuit breakers.

**Gate:** Paper trading executes a full week of verdicts with realistic fills. ZeroMQ bridge delivers signed messages verified by the EA stub.

---

### Phase 9 — Ops Hardening & Launch (Weeks 16-20)

**Objective:** Production readiness and launch.

**Milestones:**
- Run full security audit against OWASP Top 10 — SQL injection, XSS, CSRF, JWT manipulation, rate-limit bypass, dependency vulnerabilities
- Load testing with `locust` — sustain 200 concurrent WebSocket connections, 50 req/s REST throughput, engine compute within SLA (< 5s per instrument/timeframe)
- Backup and disaster recovery drill — simulate primary DB loss, restore from WAL archive to read replica, promote, verify no data loss
- Runbook completion — every alertable condition has a documented response procedure
- Monitoring dashboard review — Grafana dashboards cover all SLIs (latency, error rate, throughput, data freshness)
- Launch checklist execution — DNS cutover, TLS cert validation, health-check gating, rollback plan tested
- Go-live with 24-hour on-call rotation for first week

---

*Execution plan — v2.0.0. All phase dates are estimates subject to sprint planning refinement.*
