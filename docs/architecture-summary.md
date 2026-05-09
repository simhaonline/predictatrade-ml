# Architecture Summary

## One-Page Blueprint

Predict-A-Trade v2.0 implements the Master-Orchestrated Intelligence Layer (MOIL) -- a 6-layer architecture where the Master Engine is the sole verdict authority, coordinating 10 specialized engine families and computing a 15-dimension score for every trading decision.

## ASCII Layer Diagram

```
+============================================================================+
| LAYER 6: PRESENTATION                                                     |
|  +------------------+  +--------------------+  +------------------------+ |
|  | pat-frontend     |  | WebSocket Clients   |  | Mobile (React Native) | |
|  | Next.js 15 + TS  |  | Real-time stream    |  | Future                | |
|  +--------+---------+  +---------+----------+  +------------------------+ |
|           |                      |                                         |
+===========|======================|=========================================+
            |     HTTPS/WSS        |
+===========|======================|=========================================+
| LAYER 5: API GATEWAY             |                                        |
|  +-------------------------------|---------------------------------------+ |
|  | pat-api (FastAPI + NGINX)     |                                       | |
|  | JWT + API Key Auth            |  Rate Limiting  |  Request Validation  | |
|  +-------------------------------+---------------------------------------+ |
+=====================================|=====================================+
                                      | Internal gRPC/REST
+=====================================|=====================================+
| LAYER 4: ORCHESTRATION (THE BRAIN)  |                                    |
|  +----------------------------------|----------------------------------+  |
|  | pat-master (Master Engine)       |                                   |  |
|  | +----------------------------+   |   +----------------------------+  |  |
|  | | Engine Orchestrator        |   |   | Verdict Aggregator         |  |  |
|  | | - Parallel fan-out to all  |   |   | - Weighted signal fusion   |  |  |
|  | |   10 engines               |   |   | - 15-dimension scoring     |  |  |
|  | | - Timeout + retry logic    |   |   | - Confidence calibration   |  |  |
|  | +----------------------------+   |   +----------------------------+  |  |
|  | SOLE VERDICT AUTHORITY -- No engine issues verdicts independently    |  |
|  +--------------------------------------------------------------------+  |
+=====================================|=====================================+
                                       | Async Task Queue (Valkey)
+=====================================|=====================================+
| LAYER 3: ENGINE FLEET (10 FAMILIES) |                                    |
|  +-------+ +-------+ +-------+ +-------+ +-------+ +-------+ +-------+  |
|  | CV    | | AI    | | DI    | | CW    | |Western| | COT   | |Season |  |
|  | 8010  | | 8011  | | 8012  | | 8013  | | 8014  | | 8015  | | 8016  |  |
|  +-------+ +-------+ +-------+ +-------+ +-------+ +-------+ +-------+  |
|  +-------+ +-------+ +-------+                                         |
|  | Macro | | Tech  | | Exec  |                                         |
|  | 8017  | | 8018  | | 8019  |                                         |
|  +-------+ +-------+ +-------+                                         |
+=====================================|=====================================+
                                       |
+=====================================|=====================================+
| LAYER 2: DATA & STATE               |                                    |
|  +------------------+  +------------|--------+  +---------------------+  |
|  | pat-data         |  | PostgreSQL 16 +    |  | Valkey (Cache +     |  |
|  | Market ingestion  |  | TimescaleDB        |  | Message Queue)      |  |
|  | ETL pipeline     |  | Hypertables +      |  | Session state       |  |
|  | Data validation  |  | Compression        |  | Engine queue        |  |
|  +------------------+  +---------------------+  +---------------------+  |
+============================================================================+
| LAYER 1: INFRASTRUCTURE & EXECUTION                                       |
|  +------------------+  +------------------+  +------------------------+  |
|  | pat-execution    |  | pat-mlflow       |  | Monitoring Triad       |  |
|  | Broker API layer |  | Model registry   |  | Prometheus + Grafana   |  |
|  | Order routing    |  | Experiment track |  | + Loki                 |  |
|  +------------------+  +------------------+  +------------------------+  |
|  +------------------+  +------------------+                            |
|  | Vault (Secrets)  |  | Swiss Ephemeris  |                            |
|  +------------------+  +------------------+                            |
+============================================================================+
```

## Key Architectural Decisions with Rationale

### 1. Master Engine as Sole Verdict Authority

**Decision:** Only the Master Engine produces trading verdicts. Engines produce signals, not decisions.

**Rationale:** A single authority prevents conflicting signals from reaching execution. In multi-engine architectures without a master, contradictory signals create confusion or require complex reconciliation. The Master Engine owns the 15-dimension scoring framework and the final confidence calibration, providing a single coherent output to the execution layer.

### 2. 15-Dimension Scoring

**Decision:** Every verdict is scored across 15 independent dimensions rather than a single composite metric.

**Rationale:** A single score obscures the driver of a signal. A 15-dimension breakdown lets the Master Engine weight each dimension independently, lets users understand why a verdict was produced, and enables dimension-level ablation studies during backtesting. The dimensions capture trend, momentum, volatility, volume, support/resistance, pattern recognition, sentiment, inter-market correlation, seasonality, macro-economic context, order flow, market structure, cycle analysis, statistical properties, and risk.

### 3. 10 Engine Families (Not Micro-Engines)

**Decision:** Group related analysis into 10 engine families rather than dozens of micro-engines.

**Rationale:** Engine families provide enough granularity for specialization without the combinatorial explosion of managing many small engines. Each family encapsulates a coherent analytical domain (e.g., "Western technical analysis" rather than separate RSI, MACD, and Bollinger engines). This reduces inter-engine communication overhead and simplifies the Master Engine's aggregation logic.

### 4. Async Engine Execution with Deadlines

**Decision:** Engines are invoked in parallel with individual timeouts (default 30 seconds), and the Master Engine produces a verdict even if some engines time out.

**Rationale:** Real-time trading cannot wait for the slowest engine. The Master Engine degrades gracefully, down-weighting or excluding timed-out engines from the current verdict while logging the failure for post-hoc analysis and engine health monitoring.

### 5. PostgreSQL + TimescaleDB (Not Separate TSDB)

**Decision:** Use PostgreSQL 16 with TimescaleDB extension rather than a separate time-series database.

**Rationale:** TimescaleDB provides time-series optimization (hypertables, automatic partitioning, compression) within a full relational database. This gives us SQL joins, foreign keys, transactions, and the entire PostgreSQL ecosystem while handling billions of OHLCV bars efficiently. A separate TSDB would add operational complexity without commensurate benefit.

### 6. Valkey over Redis

**Decision:** Use Valkey (the Linux Foundation fork) instead of Redis.

**Rationale:** Valkey maintains full API compatibility with Redis OSS but operates under an open governance model without the licensing uncertainty introduced by Redis Ltd.'s license changes. It provides the cache and message queue capability the platform needs without vendor lock-in risk.

### 7. gRPC for Internal Service Communication

**Decision:** Inter-service communication between the Master Engine and engine fleet uses gRPC. External API is REST + WebSocket.

**Rationale:** gRPC provides strongly-typed contracts, binary serialization (lower latency and bandwidth), bidirectional streaming, and built-in deadline propagation. This is critical for the low-latency communication between the Master Engine and its engines. External APIs use REST for broad client compatibility.

## Service Topology

```
                              Internet
                                 |
                           [Cloudflare CDN]
                                 |
                    [NGINX Ingress/Load Balancer]
                     /                        \
            [pat-frontend:3000]        [pat-api:8001]
                                            |
                                      [pat-master:8002]
                                     /       |        \
                          gRPC fan-out to all 10 engines
                          |       |       ...      |
                    [cv:8010] [ai:8011]   ...   [exec:8019]
                          \       |       ...      /
                           [Valkey:6379]  [PG:5432]
                                  |
                          [pat-data:8000]
                                  |
                          Market Data Feeds
```

## Data Flow

1. **Ingestion:** `pat-data` fetches market data from providers (Polygon, IBKR, Yahoo Finance) and stores OHLCV bars in TimescaleDB hypertables.
2. **Verdict Request:** User or automated trigger requests a verdict for a symbol/timeframe via `pat-api`.
3. **Orchestration:** `pat-master` receives the request, looks up relevant engine families from the registry, and fans out requests to all 10 engines in parallel via gRPC.
4. **Engine Execution:** Each engine queries PostgreSQL for historical data, applies its analytical model, and returns a signal (direction + confidence) to the Master Engine.
5. **Aggregation:** The Master Engine collects all engine signals, applies the 15-dimension scoring framework with per-engine weights, calibrates confidence, and produces a final verdict.
6. **Delivery:** The verdict is stored in PostgreSQL, pushed to WebSocket subscribers, and returned to the API caller.
7. **Execution:** If the verdict meets execution thresholds, `pat-execution` translates it into broker orders with position sizing and risk checks.

## Technology Choices with Justification

| Technology           | Role                        | Justification                                         |
|---------------------|-----------------------------|-------------------------------------------------------|
| **Python 3.12**     | Backend language            | Rich ML/data ecosystem (numpy, pandas, PyTorch, FastAPI). Strong async support. Team expertise. |
| **FastAPI**         | API framework               | Native async, automatic OpenAPI, Pydantic validation, WebSocket support. Best-in-class performance for Python. |
| **Next.js 15**      | Frontend framework          | React Server Components, App Router, streaming SSR. Mature ecosystem for dashboards. |
| **PostgreSQL 16**   | Primary database            | ACID compliance, TimescaleDB extension, mature replication, JSONB for flexible schema. |
| **TimescaleDB 2.16** | Time-series optimization   | Hypertables, automatic partitioning, 90%+ compression on financial data. Native PostgreSQL extension. |
| **Valkey 8.0**      | Cache & Message Queue       | API-compatible with Redis OSS. Open governance. Proven for pub/sub and caching. |
| **NGINX 1.27**      | Reverse proxy & TLS         | Industry standard. HTTP/2, TLS 1.3, WebSocket proxying. Low resource footprint. |
| **HashiCorp Vault** | Secrets management          | Dynamic secrets, AppRole auth, audit logging. Enterprise-grade secret lifecycle. |
| **Prometheus**      | Metrics & alerting          | Pull-based, dimensional data model, powerful query language (PromQL). |
| **Grafana**         | Visualization               | Rich dashboarding, alerting integration, multi-data-source. |
| **Loki**            | Log aggregation             | Index-free design, low cost, native Grafana integration. |
| **MLflow**          | ML experiment tracking      | Model registry, experiment tracking, artifact storage. Mature, open-source. |
| **Swiss Ephemeris** | Planetary calculations      | JPL DE431-based. Standard for astrological and financial astrology applications. |
| **Wasabi S3**       | Backup storage              | S3-compatible API at 80% lower cost than AWS S3. No egress fees. |

## Scaling Characteristics

- **Read-heavy:** Engine queries are predominantly reads (historical data lookup). Add read replicas as engine count scales.
- **CPU-bound engines:** CV and AI engines require GPU or high-CPU nodes. Isolate these on dedicated hardware.
- **Write volume:** OHLCV bar writes are predictable (~10K bars/minute for monitored symbols). TimescaleDB handles this with headroom.
- **API scaling:** Stateless API layer scales horizontally behind NGINX load balancer.
- **Master Engine bottleneck:** The Master Engine is a singleton for verdict authority. Scale vertically or implement leader election for HA.
