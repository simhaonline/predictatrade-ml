# Execution Roadmap for Predict-A-Trade vNext

## Overview
This roadmap outlines the phased implementation of the Predict-A-Trade vNext platform following the Master-Orchestrated Intelligence Layer (MOIL) architecture. The plan consists of 9 phases over approximately 16-20 weeks with a 4-person core team plus domain specialists.

Each phase includes specific tasks, dependencies, parallelizable work, risks, estimated complexity, and deliverables.

---

## Phase 0: Product Definition & SOW Approval (Week 1)

**Objective**: Lock scope, contracts, and acceptance criteria before writing any code.

### Tasks
- Finalize Engine Output Contract JSON schema with all required/optional fields
- Finalize Master Verdict Contract JSON schema with all 15 scoring dimensions
- Define API surface: endpoint paths, request/response shapes, error codes, pagination standard
- Document the 15-dimension scoring framework with exact formulae and thresholds
- Produce and approve Statement of Work (SOW) with phase-gate criteria
- Establish monorepo structure, linting rules (ruff, mypy strict, eslint), pre-commit hooks, branch protection
- Set up initial project repository with README, .gitignore, licensing

### Dependencies
- None (foundational phase)

### Parallelizable Work
- Contract definition can proceed in parallel with project setup
- Technical writers can work on SOW while engineers set up repos

### Risks
- Scope creep during contract finalization
- Stakeholder misalignment on architectural decisions
- Underestimation of engine complexity

### Estimated Complexity
Low-Medium (primarily documentation and planning)

### Deliverables
- Engine Output Contract v2.0 (JSON Schema)
- Master Verdict Contract v2.0 (JSON Schema)
- API Contract v2.0 (OpenAPI 3.1 YAML)
- 15-Dimension Scoring Framework Document
- Approved Statement of Work (SOW)
- Repository initialization with basic structure
- Linting/formatting configuration (ruff, mypy, eslint, prettier)
- Pre-commit hooks setup

---

## Phase 1: Infrastructure (Weeks 2-3)

**Objective**: Provision every service and system that code will run on.

### Tasks
#### Week 2
- Provision AlmaLinux VPS/dedicated server with firewall (iptables/nftables), SELinux enforcing, SSH key-only access
- Install and configure PostgreSQL 16 with TimescaleDB extension, tuned for OLAP workloads
- Install Valkey 8.x with persistence (AOF + RDB), configure as broker/cache
- Deploy NGINX with TLS 1.3 certificates (Let's Encrypt via certbot), HTTP/2, CSP/HSTS headers

#### Week 3
- Set up Prometheus node exporters on all hosts, deploy Grafana with initial dashboards
- Configure Loki with structlog JSON pipeline for log aggregation
- Create systemd unit file templates for all `pat-*` services with resource limits
- Establish Wasabi S3 bucket with lifecycle policies for backup rotation and IAM access keys
- Set up initial CI/CD pipeline (Cloud Build or Gitea Actions) with build caching
- Configure automated DB migration execution in pipeline

### Dependencies
- Phase 0 completion (repository and basic configs)

### Parallelizable Work
- Server provisioning can proceed while database/installation tasks happen
- Monitoring setup can run in parallel with security configurations
- Backup system configuration can proceed alongside CI/CD setup

### Risks
- Server provisioning delays
- Database/TimescaleDB tuning complexity
- Certificate deployment issues
- Network/firewall misconfiguration

### Estimated Complexity
Medium (involves multiple system administrations tasks)

### Deliverables
- Provisioned and hardened AlmaLinux server
- PostgreSQL 16 + TimescaleDB installed and tuned
- Valkey 8.x installed with persistence configured
- NGINX deployed with TLS 1.3, HTTP/2, security headers
- Prometheus node exporters and Grafana deployed
- Loki log aggregation system configured
- Systemd unit templates created for pat-* services
- Wasabi S3 bucket configured with lifecycle policies
- Initial CI/CD pipeline configured with build caching
- Basic infrastructure documentation

---

## Phase 2: Contracts (Weeks 2-3, Parallel with Phase 1)

**Objective**: Define every interface before any implementation begins.

### Tasks
#### Weeks 2-3 (Concurrent with Phase 1)
- Publish `engine-output-contract-v2.0.json` - JSON Schema for all ten engine families
- Publish `master-verdict-contract-v2.0.json` - JSON Schema for Master Engine output
- Publish `api-contract-v2.0.yaml` - OpenAPI 3.1 specification covering all v2 endpoints
- Define database schema via Alembic migration skeleton - all tables, hypertables, ENUMs, indexes, foreign keys
- Define inter-service authentication protocol (HMAC token format, nonce structure, replay window)
- Publish WebSocket channel specification (5 channels, message formats, heartbeat, reconnection)
- Set up contract validation in CI pipeline to prevent implementation drift

### Dependencies
- Phase 0 completion (basic repo structure)

### Parallelizable Work
- Contract definition runs fully parallel with Phase 1 infrastructure work
- Different contract types (engine, master, API, DB, auth) can be worked on in parallel by different team members

### Risks
- Contract inconsistencies between related specifications
- Missing critical fields in engine contracts
- Overly restrictive schemas hindering implementation
- Failure to update contracts when implementation reveals gaps

### Estimated Complexity
Medium-High (requires careful attention to detail and consistency)

### Deliverables
- Engine Output Contract v2.0 JSON Schema (versioned in `/contracts/v2.0/`)
- Master Verdict Contract v2.0 JSON Schema (versioned in `/contracts/v2.0/`)
- API Contract v2.0 OpenAPI 3.1 YAML (versioned in `/contracts/v2.0/`)
- Database migration skeleton (Alembic) with all tables defined
- Inter-service authentication protocol specification
- WebSocket channel specification document
- Contract validation configured in CI pipeline
- All contracts tagged with version v2.0.0

---

## Phase 3: Data Platform (Weeks 3-5)

**Objective**: Build the data foundation that all engines read from.

### Tasks
#### Week 3-4
- **Ingestion Pipeline**: TwelveData/Yahoo/AlphaVantage provider abstraction with exponential backoff retry
- **Instrument Registry**: 187-instrument seed script with asset class, pip size, lot size, trading hours, session metadata
- **OHLCV Storage**: Upsert to TimescaleDB hypertable `market.ohlcv_data` with conflict handling
- **Data Validation Layer**: Schema validation on every ingested bar (OHLC ordering, volume non-neg, timestamp monotonicity)
- **Quarantine Table**: For rejected data with alerting on validation failures

#### Week 4-5
- **Ephemeris Cache (2015-2030)**: Precompute all 17 celestial body positions at 1-hour granularity
  - Store in TimescaleDB hypertable `astro.ephemeris_cache`
  - Composite index on `(timestamp, body_id, coordinate_system)`
- **News Feed Pipeline**: RSS/API aggregation into `macro.news_feed` hypertable with FinBERT sentiment scoring
- **Continuous Aggregates**: TimescaleDB policies for downsampled data (1H, 4H, 1D from M1)
- **Retention Policies**: Automated drop_chunks - ticks 7 days, M1 bars 90 days, D1 bars 10 years

### Dependencies
- Phase 1 completion (PostgreSQL/TimescaleDB/Valkey installed)
- Phase 2 completion (database schema skeleton defined)

### Parallelizable Work
- Ingestion pipeline and ephemeris cache can be developed in parallel
- News feed pipeline can proceed alongside continuous aggregate setup
- Data validation and quarantine handling can be worked on separately
- Instrument registry seeding is a discrete task that can happen early

### Risks
- Data provider API rate limits and reliability issues
- Ephemeris computation accuracy and performance
- TimescaleDB hypertable configuration complexity
- Data validation false positives/negatives
- News feed duplication and sentiment scoring accuracy

### Estimated Complexity
High (involves multiple integrated data systems)

### Deliverables
- Market data ingestion pipeline with provider abstraction and retry logic
- Instrument registry seeded with 187 instruments and metadata
- TimescaleDB `market.ohlcv_data` hypertable with data validation
- Ephemeris cache hypertable `astro.ephemeris_cache` (2015-2030, 1-hr granularity)
- News feed pipeline `macro.news_feed` with FinBERT sentiment scoring
- Data validation layer with quarantine table and alerting
- TimescaleDB continuous aggregates for downsampled data
- Automated retention policies configured
- Data platform documentation and operational procedures
- Initial data load verification (sample data queryable)

---

## Phase 4: Independent Engines (Weeks 4-9)

**Objective**: Build all ten engine families in isolation as dedicated services.

### Build Order (Critical Path - Longest First)

#### Weeks 4-6: Long-Lead Engines
**AI Engine (Week 4-6)**
- GLM-4 Flash/Long integration with API client
- Prompt template system for different analysis types
- Structured output parsing and validation
- Response caching mechanism (Valkey-based)
- Fallback to local models if API unavailable
- Score range: [-80, +80]

**DI Engine (Week 4-6)**
- PySwissEph wrappers for planetary calculations
- Shadbala 4-component analysis implementation
- Vimshottari Dasha L1/L2/L3 calculation
- Hora and Nakshatra computation
- Major+minor aspects with Gaussian orb model
- Kala penalty gates implementation
- Score range: [-70, +70]

#### Weeks 5-7: Medium-Lead Engines
**SMC-ICT Engine (Week 5-7)**
- BOS/MSS (Break of Structure / Market Structure Shift) detection algorithm
- Order Block identification and validation (mitigation, strength)
- Fair Value Gap (FVG) mapping and validation
- Liquidity sweep detection algorithm
- Optimal Trade Entry (OTE) zone computation
- Confluence scoring mechanism
- Score range: [0, +120]

**Vision Engine (Week 5-7)**
- Chart rendering engine (matplotlib/plotly configuration)
- GLM-4V image submission pipeline with prompt engineering
- 10-agent parallel analysis architecture design
- Conflict detection and resolution system
- Fusion scoring mechanism for final output
- Score range: [-100, +100]

#### Weeks 6-7: Shorter Engines
**Technical Engine (Week 6-7)**
- 33 technical indicators implementation (Ichimoku, RSI, MACD, Bollinger, ADX, VWAP, etc.)
- Harmonic pattern detection (6 types with Fibonacci validation)
- Elliott Wave analysis (5-impulse + ABC corrective)
- Support/resistance level identification algorithms
- Trend line analysis and channel detection
- Score range: [-80, +80]

#### Weeks 6-8: Cultural/Symbolic Engines
**Chinese Wisdom Engine (Week 6-8)**
- Chinese lunisolar calendar calculations
- BaZi 4 Pillars/12 Day Officers computation
- Feng Shui 9 Flying Stars (annual/monthly/daily) implementation
- Five Elements generative/control cycles implementation
- I-Ching 64-hexagram encoding (3 methods: coin, yarrow, plug-in)
- Score range: [-50, +50]

**Western Astrology Engine (Week 7-8)**
- Tropical ephemeris calculations (planetary positions)
- Gold natal chart (Nixon Shock 1971-08-15) implementation
- Transit aspects calculation (conjunction, square, trine, sextile, opposition)
- Retrograde flags computation and tracking
- Synodic cycles analysis for major planetary pairs
- Score range: [-30, +30]

#### Weeks 7-9: Contextual Engines
**Macro Engine (Week 7-8)**
- COT report parsing and analytics (CFTC data formatting)
- Economic calendar integration (major indicators classification)
- Central bank rate tracker (Fed, ECB, BOJ, etc.)
- Seasonal pattern analysis (monthly tendencies, holiday effects)
- Score range: [-60, +60]

**Sentiment Engine (Week 8-9)**
- FinBERT inference pipeline for news and social media
- Social media sentiment aggregation (Twitter/X, Reddit, StockTwits)
- Options flow analysis (put/call ratio, volatility skew)
- Institutional sentiment indicators (if data available)
- Score range: [-40, +40]

**Intermarket Engine (Week 8-9)**
- Cross-asset correlation matrix computation (rolling windows)
- ETF flow ingestion and analysis (creation/redemption signals)
- Futures basis calculation (spot-future differences)
- Pairs trading signal generation (cointegration, z-score)
- Commodity-correlation analysis (gold/oil, silver/copper, etc.)
- Score range: [-50, +50]

### Standard Requirements for All Engines
- Accept identical request shape: `{instrument_id, timeframe, bar_count, ephemeris_position?}`
- Return validated Engine Output Contract (schema validation in service)
- Include deterministic test case with known inputs producing known output
- Pass contract schema validation in automated test suite
- Deployable as independent systemd service with health check
- Log engine computation time for performance monitoring
- Implement circuit breaker for external API dependencies
- Provide Prometheus metrics endpoint (`/metrics`)

### Dependencies
- Phase 3 completion (Data Platform - market data and ephemeris available)
- Phase 2 completion (Engine Output Contract defined)

### Parallelizable Work
- Engines within the same timeblock can be developed in parallel by different engineers
- Engine development can overlap with late Phase 3 data platform tasks
- API client development for external services (GLM-4, FinBERT) can be shared work

### Risks
- External API dependencies (GLM-4, FinBERT) reliability and latency
- Complex algorithm implementation errors (especially for cyclic calculations)
- Performance issues with computationally intensive engines
- Data format mismatches between ingestion and engine expectations
- Deterministic test case creation for complex algorithms
- Ephemeris data format compatibility issues

### Estimated Complexity
High (involves 10 complex domain-specific implementations)

### Deliverables
- All ten engine services implemented and deployable:
  - `pat-engine-ai` (AI Signal Engine)
  - `pat-engine-di` (Discretionary Intelligence Engine)
  - `pat-engine-cw` (Chinese Wisdom Engine)
  - `pat-engine-wa` (Western Astrology Engine)
  - `pat-engine-smc-ict` (SMC-ICT Engine)
  - `pat-engine-vision` (Vision Engine)
  - `pat-engine-macro` (Macro Engine)
  - `pat-engine-technical` (Technical Structure Engine)
  - `pat-engine-sentiment` (Sentiment Engine)
  - `pat-engine-intermarket` (Intermarket Engine)
- Each engine with:
  - HTTP `/analyze` endpoint returning Engine Output Contract
  - Contract schema validation
  - Deterministic reproducibility test
  - Systemd service unit file
  - Dockerfile for containerization
  - Prometheus metrics endpoint
  - Health check endpoint (`/health`)
  - Comprehensive logging and error handling
- Engine development documentation and runbooks
- Initial engine performance baselines

---

## Phase 5: Master Engine (Weeks 8-11, Overlapping with Late Phase 4)

**Objective**: Build the adjudication layer that consumes engine outputs and produces authoritative verdicts.

### Tasks
#### Weeks 8-9: Core Adjudication Functions
- **Normalisation Engine**: Linear range mapping - project engine scores onto [-1.0, +1.0] with configurable clipping
- **Weight Computation**: Dynamic weight vector per instrument/timeframe using:
  - Rolling 90-day engine Sharpe ratio (performance-based)
  - Regime classifier output (trending vs ranging vs breakout)
  - Temporal alignment scoring (engine suitability for timeframe)
- **Independence Discounting**: Overlap detection matrix between engine pairs
  - DI↔WA via shared ephemeris inputs (Jaccard similarity of planetary data usage)
  - AI↔Sentiment via shared GLM-4 API dependency
  - Discount combined weight by `1 - overlap_coefficient`
- **Directional Fusion**: Weighted average with conflict detection
  - `weighted_direction = Σ(w_i * normalized_direction_i)`
  - Flag as HEDGE if std dev of engine directions > conflict_threshold (0.4)
  - Special handling for opposing strong signals

#### Weeks 9-10: Scoring and Override Systems
- **15-Dimension Scoring**: Full implementation of all 15 scoring dimensions:
  1. Real-Time Context Quality
  2. Directional Predictive Signal Quality
  3. Timing Alignment Quality
  4. Structural Trend Quality
  5. Liquidity / Execution Quality
  6. Positioning Intelligence Quality
  7. Seasonal Context Quality
  8. Symbolic Confluence Quality
  9. Risk Environment Quality
  10. Implementation Readiness
  11. Contradiction Severity (Penalty Dimension)
  12. Evidence Integrity
  13. Confidence Calibration
  14. Regime Compatibility
  15. Final Opportunity Attractiveness
- **Hard Override Pipeline**: Ordered evaluation of:
  - DI Kala penalty gates (specific planetary combinations)
  - CW mandatory flat threshold (specific Flying Star combinations)
  - Risk circuit breakers (volatility, spread, liquidity thresholds)
  - Exchange halts (from market data feeds)
  - Session boundaries (market open/close times)
  - Any trigger immediately forces FLAT verdict regardless of score

#### Weeks 10-11: Output and Verification
- **Verdict Emission**: 
  - Publish Master Verdict Contract to Valkey Pub/Sub `verdicts:{instrument}:{timeframe}`
  - Persist to TimescaleDB `signals.master_verdicts` hypertable
  - Include SHA-256 immutability hash covering all inputs and computed output
- **SHA-256 Immutability System**:
  - Content-hash generation for every verdict
  - Replay verification system that recomputes hash and compares
  - Audit trail of all inputs used for each verdict
- **Performance Optimization**:
  - Cache frequently used reference data (instrument metadata, etc.)
  - Optimize weight computation lookup tables
  - Streamline 15-dimension scoring calculations
  - Async processing where possible without compromising determinism

### Dependencies
- Phase 4 completion (sufficient engines available for testing - minimum 5 engines)
- Phase 2 completion (Master Verdict Contract defined)
- Phase 3 completion (Data Platform for ephemeris and market data)

### Parallelizable Work
- Different Master Engine subsystems can be developed in parallel:
  - Normalization and weight computation
  - 15-dimension scoring system
  - Override pipeline and verdict emission
  - Replay verification and immutability system
- Overlap with late Phase 4 engine development is expected and beneficial

### Risks
- Weight computation instability or performance issues
- 15-dimension scoring complexity and potential for errors
- Override gate ordering and priority conflicts
- SHA-256 implementation correctness and performance
- Deterministic replay verification complexity
- Circular dependency risks (engines needing master outputs)

### Estimated Complexity
High (central component with complex algorithms and strict requirements)

### Deliverables
- `pat-master` service implemented with:
  - Engine Output Contract validation and normalization
  - Dynamic weight computation system (90-day performance, regime, temporal)
  - Independence discounting algorithm (Jaccard similarity overlap detection)
  - Directional fusion with conflict detection and HEDGE flagging
  - Complete 15-dimension scoring framework implementation
  - Hard override pipeline with DI Kala, CW mandatory flat, risk breakers
  - Verdict emission to Valkey Pub/Sub and TimescaleDB persistence
  - SHA-256 immutability hash generation and replay verification
  - Comprehensive test suite including 100+ precomputed test scenarios
  - Deterministic replay verification system
  - Systemd service unit and Dockerfile
  - Prometheus metrics and health check endpoints
  - Detailed documentation of all algorithms and parameters
- Performance benchmarks showing <5s computation time
- Deterministic reproducibility verified on historical data

---

## Phase 6: Research & Validation (Weeks 10-13)

**Objective**: Statistically validate that MOIL produces measurable alpha.

### Tasks
#### Weeks 10-11: Walk-Forward Analysis Framework
- **Expanding Window Validation**: 
  - Training on 90-day rolling windows
  - Testing on subsequent 30-day windows
  - Period: 2020-2026 historical data
- **Metrics Calculation**:
  - Sharpe ratio, Calmar ratio, Sortino ratio
  - Win rate, profit factor, average win/loss
  - Maximum drawdown and recovery time
  - Volatility-adjusted returns
- **Baseline System Configurations**:
  - B1: Technical indicators only (pat-engine-technical)
  - B2: All quantitative engines (AI, Technical, Macro, Sentiment, Intermarket)
  - B3: Full MOIL with all ten engines including metaphysical (DI, CW, WA)
- **Statistical Significance Testing**:
  - Diebold-Mariano test on squared forecast errors
  - Pairwise comparisons: B3 vs B1, B3 vs B2
  - Confidence intervals and p-value reporting

#### Weeks 11-12: Historical Replay and Stress Testing
- **Full Historical Replay**:
  - Replay 2024-2025 market data through complete MOIL pipeline
  - Compare emitted verdicts against actual subsequent price movement
  - Measure directional accuracy (percentage correct)
  - Average favorable excursion (AFE) and average adverse excursion (AAE)
  - Profit factor and expectancy calculations
- **Scenario-Based Testing**:
  - Flash crash replay (2010, 2015, 2020) scenarios
  - Correlation breakdown situations (risk-on/risk-off extremes)
  - Data feed interruption simulations (partial and complete loss)
  - Engine failure modes (individual engine downtime)
  - Regime change simulations (trending to ranging transitions)

#### Weeks 12-13: Explainability and Attribution
- **SHAP Decomposition**:
  - For XGBoost meta-model (if used in Master Engine)
  - Compute SHAP values for each engine family
  - Quantify marginal contribution to final verdict
  - Primary hypothesis: metaphysical engine SHAP values non-zero and stable
- **Feature Importance Analysis**:
  - Permutation importance for non-model-based engines
  - Correlation analysis between engine outputs and verdict components
  - Temporal stability analysis of engine contributions
- **Validation Reporting**:
  - Comprehensive validation report with all metrics
  - Visualization of equity curves and drawdown periods
  - Engine contribution analysis over time
  - Risk-adjusted performance comparison

### Dependencies
- Phase 5 completion (Master Engine functional with test engines)
- Phase 3-4 completion (sufficient historical data and engines available)
- Phase 2 completion (contracts for data format consistency)

### Parallelizable Work
- Walk-forward analysis setup can proceed alongside historical replay
- Different stress test scenarios can be run in parallel
- SHAP analysis and feature importance can be worked on separately
- Report writing can happen while computations are running

### Risks
- Insufficient historical data quality or completeness
- Overfitting to historical period in parameter tuning
- Statistical significance difficult to achieve with noisy financial data
- Computational requirements for extensive historical replay
- Engine-specific bugs affecting validation results
- Interpretation challenges of SHAP values for rule-based systems

### Estimated Complexity
High (involves sophisticated statistical analysis and large-scale computation)

### Deliverables
- Walk-forward analysis framework implemented and tested
- Historical replay system capable of processing multi-year datasets
- Baseline comparison system (B1, B2, B3 configurations)
- Statistical significance testing (Diebold-Mariano test implementation)
- Flash crash and scenario replay capabilities
- SHAP explainability system for model-based components
- Feature importance and attribution analysis tools
- Comprehensive validation report including:
  - Walk-forward Sharpe ratio > 1.0 (target)
  - Maximum drawdown < 25% (target)
  - Statistically significant improvement over technical-only baseline (p < 0.05)
  - Directional accuracy and profit factor metrics
  - Engine contribution analysis and stability metrics
  - Stress test results for various failure scenarios
- Validation documentation and runbooks

---

## Phase 7: Frontend & Delivery (Weeks 11-14)

**Objective**: Build the Verdict Terminal and all delivery channels.

### Tasks
#### Weeks 11-12: Core Application
- **Verdict Terminal (Next.js 15 App Router)**:
  - Dashboard with real-time Master Verdict display
  - Instrument selector with search, autocomplete, and favorites
  - Timeframe switcher (M1, M5, M15, H1, H4, D1) with persistent preference
  - 6-pillar radar hexagon visualization (Recharts/D3) showing dimension scores
  - Engine output drill-down per engine family with expand/collapse
  - Verdict history table with:
    - Multi-column sorting (clickable headers)
    - Per-column filtering (text, date, range filters)
    - Date range presets (today, week, month, year, custom)
    - Export functionality (PDF, Excel, CSV, JSON)
  - Responsive layout breaking at tablet/mobile breakpoints
  - Dark/light theme toggle with system preference detection
  - Accessibility compliance (WCAG 2.1 AA) with ARIA labels and semantic HTML

#### Weeks 12-13: Real-Time and Alerting
- **WebSocket Real-Time System**:
  - JWT-authenticated WebSocket connections to pat-api
  - 5-channel subscription system (verdicts, engines, instruments, alerts, system)
  - Automatic reconnection with exponential backoff and jitter
  - Heartbeat keepalive mechanism (25-second interval)
  - Message ordering and duplicate detection
  - Verdict update delivery within 100ms of Master Engine emission
- **Alert Configuration System**:
  - User-defined alert thresholds:
    - Direction change (bullish/bearish/neutral transitions)
    - Conviction threshold crossing (user-configurable levels)
    - Override gate triggering (specific gate selections)
    - Engine health degradation (non-responsive engines)
    - Custom verdict dimension thresholds
  - Notification delivery selection:
    - Email (SMTP with TLS and HTML/templates)
    - Telegram Bot API (with markdown formatting)
    - Discord Webhooks (with embed support)
    - SMS (Twilio with message templating)
    - Slack Webhooks (for internal team alerts)
  - Alert history and suppression (prevent notification storms)
  - Integration with WebSocket real-time system for instant alerts

#### Weeks 13-14: Export and Enhancement
- **Export Pipeline Enhancement**:
  - PDF export (jsPDF) with professional formatting and charts
  - Excel export (SheetJS) with multiple worksheets and styling
  - CSV export with proper quoting and encoding
  - JSON export with full fidelity and formatting options
  - All exports include cryptographic integrity checksums (SHA-256)
  - Scheduled export capability (daily/weekly/monthly)
- **Performance Optimization**:
  - Code splitting and lazy loading for route-based splitting
  - Image optimization and next/image integration
  - SWR caching strategy optimization for data fetching
  - Bundle analysis and reduction
  - Performance budget enforcement (<5s TTI on mid-tier devices)
- **User Experience Refinement**:
  - Onboarding tutorial for new users
  - Contextual help and tooltips throughout interface
  - Keyboard navigation and shortcut support
  - Error boundaries and graceful degradation
  - Loading states and skeleton UIs for better perceived performance
  - Offline capability with data caching and sync

### Dependencies
- Phase 5 completion (Master Engine producing verdicts)
- Phase 2 completion (API contract defined)
- Phase 1 completion (NGINX/API infrastructure available)

### Parallelizable Work
- Dashboard development can proceed alongside real-time system setup
- Alerting system can be developed in parallel with export functionality
- Performance optimization can be ongoing throughout development
- UX refinement can happen as features are completed

### Risks
- Browser compatibility issues with advanced web features
- State management complexity as application grows
- Real-time connection reliability under various network conditions
- Alert notification fatigue and user preference management
- Export functionality edge cases (large datasets, special characters)
- Performance regression as features are added
- Accessibility compliance verification and remediation

### Estimated Complexity
Medium-High (involves complex frontend application with real-time features)

### Deliverables
- `pat-frontend` Next.js 15 application deployed with:
  - Real-time Master Verdict dashboard display
  - Instrument selector with search, autocomplete, favorites
  - Timeframe switcher (M1-D1) with persistent preferences
  - 6-pillar radar hexagon visualization showing dimension scores
  - Engine output drill-down per engine family with expand/collapse
  - Verdict history table with sorting, filtering, date ranges, export
  - Responsive layout (desktop/tablet/mobile) with dark/light themes
  - Accessibility compliance (WCAG 2.1 AA)
  - JWT authentication flow with refresh token mechanism
  - WebSocket real-time system (5 channels, auto-reconnect, heartbeat)
  - Alert configuration system with multiple notification channels
  - Export functionality (PDF, Excel, CSV, JSON) with integrity checksums
  - Performance optimization (code splitting, lazy loading, bundle budget)
  - User experience refinements (onboarding, help, keyboard nav, error boundaries)
  - Comprehensive test suite (unit, integration, Playwright E2E)
  - Dockerfile and systemd service unit
  - Prometheus metrics and health check endpoints
  - User guide and administrative documentation
- Lighthouse performance score > 90
- Playwright E2E test suite passing on core user journeys

---

## Phase 8: Execution Integration (Weeks 13-16)

**Objective**: Verdicts become trades.

### Tasks
#### Weeks 13-14: ZeroMQ Bridge and Execution Preparation
- **ZeroMQ Bridge v2**:
  - ROUTER/DEALER pattern for point-to-point EA communication
  - PUB/SUB pattern for broadcast verdicts to multiple EAs
  - Proper framing protocol with message length prefixes
  - HMAC-SHA256 message signing with key rotation capability
  - Sequence numbering for EA-side deduplication
  - Bidirectional health-check pings (EA to bridge and vice versa)
  - Connection pooling and resource management
  - Comprehensive logging and error handling
  - Fallback mechanisms for connection loss
- **MQL5 Expert Advisor v2**:
  - PredictATradeEA v2 consuming Master Verdict Contracts (not raw engine outputs)
  - Strategy factory updated for MOIL recommendation bands:
    - Aggressive Long, Constructive Long, Watch, Neutral, Constructive Short, Aggressive Short, Block
  - Position sizing integration with risk management signals
  - Circuit breakers with per-instrument max exposure limits
  - Trade execution logging and error handling
  - Compilation instructions and deployment guidance
- **Protocol Documentation**:
  - Complete ZeroMQ message format specification
  - HMAC key management and rotation procedures
  - EA configuration and setup guide
  - Troubleshooting common issues

#### Weeks 14-15: Crypto Gateways and Paper Trading
- **Crypto Exchange Gateways**:
  - Unified REST/WebSocket abstraction layer for Binance and OKX
  - Authentication management (API keys with IP whitelisting)
  - Order abstraction layer supporting:
    - Market orders (immediate execution)
    - Limit orders (price specification)
    - Stop-loss and take-profit orders
    - OCO (one-cancels-other) order pairs
  - Position tracking with realized/unrealized PnL calculation
  - WebSocket subscription for real-time order book and trades
  - Rate limiting compliance and backoff strategies
  - Fallback mechanisms for exchange downtime
- **Paper Trading Engine**:
  - Realistic simulation engine with configurable parameters:
    - Latency distribution: Log-normal (median 150ms, configurable)
    - Slippage model: Volume-weighted average price (VWAP) delay
    - Fill probability function: Exponential decay with distance from mid-price
    - Market impact modeling (optional advanced feature)
  - Order book simulation with depth and liquidity modeling
  - Commission and fee simulation
  - Execution report generation matching live trading log formats
  - Performance analytics and metrics calculation
  - Configurable starting capital and position limits
- **Risk Management Enhancements**:
  - Kelly criterion position sizing with fractional Kelly (user-configurable)
  - Correlation-adjusted Value-at-Risk (VaR) calculation
  - Per-instrument and portfolio exposure limits
  - Drawdown-based circuit breakers (equity curve protection)
  - Volatility spike detection and automatic risk reduction
  - Maximum consecutive loss limits
  - Daily loss limits and trading halt mechanisms

#### Weeks 15-16: Integration Testing and Validation
- **End-to-End Testing**:
  - Simulated Master Verdict generation and transmission
  - ZeroMQ bridge delivery to MQL5 EA stub
  - EA action verification and logging
  - Crypto gateway order submission and simulation
  - Paper trading engine end-to-end flow validation
- **Performance Validation**:
  - Latency measurement from verdict to order submission
  - Throughput testing under simulated high-frequency verdicts
  - Resource utilization monitoring during peak loads
  - Reliability testing under various failure scenarios
- **Documentation and Handoff**:
  - Execution layer setup and configuration guide
  - MQL5 EA deployment and troubleshooting documentation
  - Crypto gateway API key management guide
  - Paper trading engine validation and usage instructions
  - Risk management parameter tuning guide

### Dependencies
- Phase 5 completion (Master Engine producing reliable verdicts)
- Phase 2 completion (API contracts for potential integration points)
- External dependencies: MetaTrader 5 platform, Binance/OKX API access

### Parallelizable Work
- ZeroMQ bridge development can proceed alongside MQL5 EA work
- Crypto gateways and paper trading can be developed in parallel
- Risk management enhancements can overlap with both areas
- Documentation can be written as components are completed

### Risks
- ZeroMQ connection reliability and reconnection handling
- HMAC key management and distribution complexity
- MQL5 language limitations and platform quirks
- Crypto exchange API rate limits and changing requirements
- Paper trading realism limitations and validation challenges
- Risk management false positives/negatives in live markets
- Integration complexity between multiple systems
- Regulatory considerations for automated trading systems

### Estimated Complexity
Medium-High (involves integration with external trading systems)

### Deliverables
- `pat-execution` service deployed with:
  - ZeroMQ Bridge v2 (ROUTER/DEALER + PUB/SUB patterns)
  - HMAC-SHA256 message signing with key rotation
  - Bidirectional health-check pings and connection management
  - Comprehensive logging and error handling
  - Fallback mechanisms for connection loss and network issues
- MQL5 Expert Advisor v2:
  - PredictATradeEA v2 consuming Master Verdict Contracts
  - Strategy factory for MOIL recommendation bands
  - Integrated position sizing and risk management signals
  - Per-instrument max exposure limits circuit breakers
  - Comprehensive logging and error handling
  - Deployment and configuration guidance
- Crypto Exchange Gateways:
  - Unified REST/WebSocket abstraction for Binance and OKX
  - Order abstraction layer (market, limit, stop-loss, take-profit, OCO)
  - Position tracking with realized/unrealized PnL
  - WebSocket subscription for real-time market data
  - Rate limiting compliance and fallback mechanisms
- Paper Trading Engine:
  - Realistic simulation with latency, slippage, and fill probability models
  - Order book simulation and commission/fee modeling
  - Execution report generation matching live trading formats
  - Performance analytics and metrics calculation
- Enhanced Risk Management:
  - Kelly criterion position sizing with fractional Kelly
  - Correlation-adjusted VaR calculation
  - Per-instrument and portfolio exposure limits
  - Drawdown and volatility spike circuit breakers
  - Maximum consecutive loss and daily loss limits
- Integration testing framework and validation procedures
- Comprehensive documentation for all execution components
- Systemd service unit and Dockerfile
- Prometheus metrics and health check endpoints

---

## Phase 9: Ops Hardening & Launch (Weeks 16-20)

**Objective**: Production readiness and launch.

### Tasks
#### Weeks 16-17: Security Hardening
- **Comprehensive Security Audit**:
  - OWASP ASVS Level 3 assessment
  - Network penetration testing (external and internal)
  - Application penetration testing (API endpoints, WebSocket)
  - Infrastructure penetration testing (servers, containers, systemd)
  - Dependency vulnerability scanning (SAST and DAST)
  - Secrets management validation and access control review
  - Social engineering resistance testing (phishing simulation)
- **Remediation and Hardening**:
  - Address all critical and high findings from security audit
  - Implement defense-in-depth improvements based on findings
  - Enhance monitoring and alerting for security events
  - Update access controls and privilege assignments
  - Strengthen encryption and key management practices
  - Improve input validation and output encoding where needed
  - Enhance logging and audit trail completeness

#### Weeks 17-18: Performance and Load Testing
- **Load Testing Framework**:
  - Locust or k6 based load testing scenarios
  - Sustained 200 concurrent WebSocket connections
  - 50+ REST requests per second sustained throughput
  - Engine compute within SLA (< 5s per instrument/timeframe)
  - Mixed workload simulating realistic usage patterns
- **Performance Optimization**:
  - Identify and resolve performance bottlenecks from testing
  - Optimize database queries and indexing strategies
  - Tune Valkey/PubSub configuration for throughput
  - Optimize service resource allocation (CPU, memory, workers)
  - Implement additional caching where beneficial
  - Refine algorithms for better computational efficiency
- **Scalability Validation**:
  - Horizontal scaling tests for engine services
  - Database read replica performance validation
  - WebSocket hub fanout scaling verification
  - API layer load balancing effectiveness
  - Resource utilization under peak load conditions

#### Weeks 18-19: Backup, Disaster Recovery, and Runbooks
- **Backup System Validation**:
  - WAL archiving verification for point-in-time recovery
  - Regular base backup restore testing
  - Wasabi S3 backup integrity validation (checksums)
  - MLflow artifact backup and restore testing
  - Encryption key management and rotation validation
  - Backup schedule optimization and alerting on failures
- **Disaster Recovery Drill**:
  - Simulate primary database loss scenario
  - Restore from WAL archive to read replica
  - Failover procedures execution and validation
  - System promotion and verification of no data loss
  - Recovery time objective (RTO) and recovery point objective (RPO) measurement
  - Documentation of lessons learned and procedure updates
- **Runbook Completion**:
  - Every alertable condition documented with response procedure
  - Runbook testing through tabletop exercises
  - Integration with monitoring/alerting systems (runbook links in alerts)
  - Operations team training on critical procedures
  - Knowledge transfer documentation and accessibility
  - Runbook version control and change management procedures

#### Weeks 19-20: Final Validation and Launch Preparation
- **Launch Checklist Execution**:
  - DNS cutover procedures and validation
  - TLS certificate validation and renewal testing
  - Health-check gating verification for traffic routing
  - Rollback plan testing and validation
  - Final performance benchmarking under production-like loads
  - Security validation re-check after all changes
  - Functional validation of all user-facing features
  - Performance validation of all APIs and integrations
- **Stakeholder Validation**:
  - User acceptance testing with target audience
  - Domain expert validation of engine outputs and verdicts
  - Operations team validation of procedures and runbooks
  - Development team validation of code quality and documentation
  - Executive validation against original SOW and objectives
- **Go-Live Preparation**:
  - 24-hour on-call rotation setup for first week post-launch
  - Final documentation package completion and distribution
  - Monitoring dashboard finalization and stakeholder review
  - Alert threshold tuning based on baseline performance
  - Communication plan for launch announcement
  - Post-launch review schedule (daily week 1, weekly month 1)

### Dependencies
- All previous phases completed and integrated
- External services accessible and configured (data providers, execution platforms)
- Stakeholder availability for validation and testing

### Parallelizable Work
- Security auditing can proceed alongside performance testing setup
- Backup validation and disaster recovery planning can overlap
- Runbook creation can happen as features are stabilized
- Launch checklist execution can be done while final validations run

### Risks
- Security audit revealing critical architectural flaws
- Performance testing showing inability to meet SLAs
- Backup system failures or incomplete validation
- Disaster recovery procedures proving inadequate or overly complex
- Stakeholder validation revealing significant usability issues
- Last-minute scope changes or requirement additions
- Integration issues between previously isolated components
- Unexpected external service changes or deprecations

### Estimated Complexity
Medium (involves validation, testing, and preparation rather than new development)

### Deliverables
- Security audit completion with all critical/high findings resolved
- Load testing validation showing:
  - Sustained 200+ concurrent WebSocket connections
  - 50+ REST requests per second maintained throughput
  - Engine computation consistently < 5s SLA
  - Resource utilization within acceptable bounds
- Backup system validated with:
  - Regular automated backups completing successfully
  - WAL archiving verified for point-in-time recovery
  - MLflow artifact backup and restore validated
  - Encryption key management and rotation working
- Disaster recovery drill completed with:
  - Documented RTO and RPO measurements
  - Successful failover and system restoration
  - Verified no data loss or corruption
  - Updated procedures based on lessons learned
- Runbook library completed with:
  - Response procedures for all alertable conditions
  - Integration with monitoring/alerting systems
  - Operations team training completion
  - Accessible knowledge transfer documentation
- Launch checklist executed and validated:
  - DNS cutover procedures tested and working
  - TLS certificate validation and renewal automated
  - Health-check gating verification for production traffic
  - Rollback plan tested and validated
  - Final performance benchmarks meeting all SLAs
  - Security validation re-confirmed post-hardening
- Stakeholder validation completed:
  - User acceptance testing with positive feedback
  - Domain expert validation of engine outputs and verdicts
  - Operations team validation of procedures and runbooks
  - Development team code quality and documentation approval
  - Executive validation against SOW objectives
- Production-ready system with:
  - All services running and monitored
  - Alerting system operational and tuned
  - Backup system active and verified
  - Documentation package complete and distributed
  - On-call rotation established for initial launch period
  - Post-launch review schedule established
- Final release notes and version tagging (v1.0.0)
- Post-launch review schedule and process defined

---

## Phase Dependencies and Critical Path

### Critical Path (Longest Sequence of Dependencies)
1. Phase 0 → Phase 1 & 2 (Infrastructure & Contracts in parallel)
2. Phase 0 → Phase 2 → Phase 3 (Contracts → Data Platform)
3. Phase 0 → Phase 2 → Phase 3 → Phase 4 (Data Platform → Engines)
4. Phase 0 → Phase 2 → Phase 3 → Phase 4 → Phase 5 (Engines → Master Engine)
5. Phase 0 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 (Master → Research)
6. Phase 0 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 7 (Master → Frontend)
7. Phase 0 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 8 (Master → Execution)
8. Phase 0 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 9 (Master → Operations)

### Parallel Execution Opportunities
- **Weeks 2-3**: Phase 1 (Infrastructure) && Phase 2 (Contracts) run fully in parallel
- **Weeks 3-4**: Phase 3 (Data Platform) starts while Phase 1 completes
- **Weeks 4-6**: Phase 4 (Engines - AI & DI) starts while Phase 3 continues
- **Weeks 5-7**: Phase 4 continues with SMC-ICT & Vision while AI/DI finish
- **Weeks 6-8**: Phase 4 continues with Technical & CW engines
- **Weeks 7-8**: Phase 4 continues with WA & Macro engines while others finish
- **Weeks 8-9**: Phase 5 (Master Engine) starts while late Phase 4 engines finish
- **Weeks 8-10**: Phase 6 (Research) starts while Master Engine develops
- **Weeks 9-11**: Phase 7 (Frontend) starts while Master Engine completes
- **Weeks 11-13**: Phase 8 (Execution) starts while Research & Frontend continue
- **Weeks 13-16**: Phase 8 continues while Frontend finishes
- **Weeks 16-20**: Phase 9 (Operations) runs while final integration and validation occur

### Resource Allocation Guidelines
- **Weeks 1-2**: 100% on Phase 0 (Product Definition)
- **Weeks 2-3**: 50% Phase 1 (Infrastructure), 50% Phase 2 (Contracts)
- **Weeks 3-4**: 33% Phase 1 completion, 33% Phase 2 completion, 34% Phase 3 (Data Platform)
- **Weeks 4-6**: 40% Phase 4 (Engines - AI/DI lead), 30% Phase 3 completion, 30% Phase 5 preparation
- **Weeks 5-7**: 50% Phase 4 (Engines - SMC-ICT/Vision lead), 25% Phase 3 completion, 25% Phase 5 start
- **Weeks 6-8**: 50% Phase 4 (Engines - Technical/CW lead), 25% Phase 3 completion, 25% Phase 5 development
- **Weeks 7-8**: 25% Phase 4 completion, 25% Phase 4 (WA/Macro), 25% Phase 5 development, 25% Phase 6 start
- **Weeks 8-9**: 40% Phase 5 (Master Engine), 30% Phase 4 completion, 20% Phase 6, 10% Phase 7 start
- **Weeks 9-10**: 35% Phase 5, 25% Phase 4 completion, 20% Phase 6, 20% Phase 7
- **Weeks 10-11**: 30% Phase 5 completion, 25% Phase 4 completion, 20% Phase 6, 25% Phase 7
- **Weeks 11-12**: 20% Phase 5 completion, 15% Phase 4 completion, 20% Phase 6, 25% Phase 7, 20% Phase 8 start
- **Weeks 12-13**: 10% Phase 5 completion, 10% Phase 4 completion, 15% Phase 6, 25% Phase 7, 25% Phase 8, 15% Phase 9 preparation
- **Weeks 14-15**: 5% Phase 5 completion, 5% Phase 4 completion, 10% Phase 6, 20% Phase 7, 30% Phase 8, 30% Phase 9
- **Weeks 16-17**: 5% Phase 5 completion, 5% Phase 4 completion, 5% Phase 6, 10% Phase 7, 20% Phase 8, 55% Phase 9 (Security focus)
- **Weeks 18-19**: 5% Phase 5, 5% Phase 4, 5% Phase 6, 5% Phase 7, 10% Phase 8, 70% Phase 9 (Performance/DR focus)
- **Weeks 20**: 5% Phase 5, 5% Phase 4, 5% Phase 6, 5% Phase 7, 5% Phase 8, 75% Phase 9 (Launch prep)

---

## Success Criteria and Phase Gates

### Phase Gate Criteria
Each phase must satisfy specific criteria before proceeding to the next phase.

**Phase 0 Gate**: SOW signed by all stakeholders, contracts published as versioned JSON Schema documents in `/contracts/`.

**Phase 1 Gate**: All infrastructure services respond to health checks. PostgreSQL accepts connections. Valkey ping returns PONG. NGINX serves HTTPS.

**Phase 2 Gate**: All contracts version-tagged in `/contracts/v2.0/`. Schema validators run in CI. No implementation deviates from contracts.

**Phase 3 Gate**: 187 instruments seeded. 6 timeframes ingest successfully. Ephemeris cache queryable for any timestamp in range.

**Phase 4 Gate**: All ten engine services start, accept `/analyze` requests, and return schema-valid Engine Output Contracts. Each engine has at least one deterministic reproducibility test.

**Phase 5 Gate**: Master Engine correctly adjudicates 100+ precomputed test scenarios with known expected outputs. All override gates fire correctly. SHA-256 immutability verified on replay.

**Phase 6 Gate**: Full MOIL (B3) demonstrates statistically significant improvement over technical-only baseline (B1) at p < 0.05 on Diebold-Mariano. Walk-forward Sharpe ratio > 1.0. Max drawdown < 25%.

**Phase 7 Gate**: `/qa` Playwright test suite passes on all core user journeys (view verdict, switch instrument, export report, configure alert). Lighthouse score > 90 on Performance.

**Phase 8 Gate**: Paper trading executes a full week of verdicts with realistic fills. ZeroMQ bridge delivers signed messages verified by the EA stub.

**Phase 9 Gate**: Launch checklist execution completed. DNS cutover, TLS cert validation, health-check gating, rollback plan tested. 24-hour on-call rotation ready for first week.

### Overall Success Criteria
- All phases completed with signed-off phase gates
- System meets all architectural requirements from SOW
- Performance benchmarks meet or exceed SLAs
- Security audit passes with no critical findings
- All automated tests pass in CI/CD pipeline
- User acceptance testing receives positive feedback
- Documentation suite complete and accessible
- Production deployment successful and stable
- Post-launch monitoring shows healthy system operation

---

## Risk Management Throughout Execution

### Ongoing Risk Mitigation
- **Daily standups** to identify blockers early
- **Weekly retrospectives** to adjust plans based on learned lessons
- **Continuous integration** with automated testing to catch regressions
- **Regular architecture reviews** to ensure alignment with MOIL principles
- **Frequent demos** to stakeholders for early feedback
- **Pair programming** on complex algorithms to reduce defects
- **Code reviews** for all changes to maintain quality standards
- **Technical spikes** for uncertain components before full commitment
- **Documentation as you go** to prevent knowledge loss
- **Regular backups** of work in progress to prevent loss
- **Environment parity** between development, staging, and production

### Contingency Planning
- **Time Buffers**: 10-20% time buffer built into each phase estimate
- **Scope Flexibility**: Ability to defer non-critical features to post-launch
- **Resource Adjustment**: Ability to bring in specialists for specific domains
- **Technology Alternatives**: Known alternatives for risky technical choices
- **External Dependency Plans**: Fallbacks for critical external service failures
- **Knowledge Sharing**: Cross-training to prevent single points of failure
- **Regular Re-estimation**: Updating estimates based on actual velocity

### Quality Assurance Throughout
- **Test-Driven Development**: Writing tests before implementation where practical
- **Behavior-Driven Development**: Using scenarios to validate complex functionality
- **Property-Based Testing**: For algorithms with mathematical properties
- **Mutation Testing**: To validate test suite effectiveness (periodic)
- **Performance Testing**: Integrated into development cycle, not just phase end
- **Security Testing**: Regular dependency scanning and basic penetration testing
- **Usability Testing**: Early and frequent feedback on interface designs
- **Accessibility Testing**: Ongoing during frontend development, not just phase end
- **Localization Testing**: Ensuring i18n-readiness even if not implementing translations