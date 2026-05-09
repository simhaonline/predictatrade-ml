# Detailed Scope of Work for Predict-A-Trade vNext

## Functional Requirements

### 1. Core Platform Features
- **Master-Orchestrated Intelligence Layer (MOIL)**: Centralized decision authority with independent engine analysis
- **Engine Output Contract Standardization**: All engines must emit validated JSON contracts
- **Master Verdict Generation**: Single authoritative output from Master Engine
- **Immutability & Replay**: SHA-256 hashing for verdict verification and historical replay
- **Override Framework**: Master Risk Override Layer for mandatory-flat conditions

### 2. Engine Families (10 Independent Services)
Each engine must:
- Accept standardized input: `{instrument_id, timeframe, bar_count, ephemeris_position?}`
- Return validated Engine Output Contract
- Operate in isolation (no inter-engine communication)
- Be deployable as independent systemd service
- Include deterministic reproducibility test

#### Specific Engine Requirements:
**AI Engine (pat-engine-ai)**
- GLM-4 Flash/Long integration
- Multi-pillar fusion and narrative generation
- Prompt templates and structured output parsing
- Response caching mechanism
- Score range: [-80, +80]

**DI Engine (pat-engine-di)**
- PySwissEph wrappers for planetary calculations
- Shadbala 4-component analysis
- Vimshottari Dasha L1/L2/L3
- Hora, Nakshatra, major+minor aspects with Gaussian orb model
- Kala penalty gates
- Score range: [-70, +70]

**Chinese Wisdom Engine (pat-engine-cw)**
- Chinese lunisolar calendar calculations
- BaZi 4 Pillars/12 Day Officers
- Feng Shui 9 Flying Stars (annual/monthly/daily)
- Five Elements generative/control cycles
- I-Ching 64-hexagram encoding (3 methods)
- Score range: [-50, +50]

**Western Astrology Engine (pat-engine-wa)**
- Tropical ephemeris calculations
- Gold natal chart (Nixon Shock 1971-08-15)
- Transit aspects and retrograde flags
- Synodic cycle analysis
- Score range: [-30, +30]

**SMC-ICT Engine (pat-engine-smc-ict)**
- BOS/MSS (Break of Structure / Market Structure Shift) detection
- Order Block identification and validation
- Fair Value Gap (FVG) mapping
- Liquidity sweep detection
- Optimal Trade Entry (OTE) zone computation
- Confluence scoring mechanism
- Score range: [0, +120]

**Vision Engine (pat-engine-vision)**
- Chart rendering (matplotlib/plotly)
- GLM-4V image submission pipeline
- 10-agent parallel analysis with conflict detection
- Fusion scoring mechanism
- Score range: [-100, +100]

**Macro Engine (pat-engine-macro)**
- COT report parsing and analytics (CFTC data)
- Economic calendar integration
- Central bank rate tracker
- Seasonal pattern analysis
- Score range: [-60, +60]

**Technical Engine (pat-engine-technical)**
- 33 technical indicators (Ichimoku, RSI, MACD, Bollinger, ADX, VWAP, etc.)
- Harmonic pattern detection (6 types with Fibonacci validation)
- Elliott Wave analysis (5-impulse + ABC corrective)
- Support/resistance level identification
- Trend line analysis algorithms
- Score range: [-80, +80]

**Sentiment Engine (pat-engine-sentiment)**
- FinBERT inference pipeline for news classification
- Social media sentiment aggregation
- Options flow analysis
- Put/call ratio analysis
- Score range: [-40, +40]

**Intermarket Engine (pat-engine-intermarket)**
- Cross-asset correlation matrix computation
- ETF flow ingestion and analysis
- Futures basis calculation
- Pairs trading signal generation
- Commodity-correlation analysis
- Score range: [-50, +50]

### 3. Core Services

**pat-data Service**
- Market data ingestion from TwelveData, Yahoo Finance, AlphaVantage
- OHLCV upsert to TimescaleDB hypertable `market.ohlcv_data`
- Swiss Ephemeris precomputation (2015-2030) for 17 celestial bodies
- News sentiment aggregation via FinBERT and GLM-4
- Data validation layer (OHLC ordering, volume checks, timestamp monotonicity)
- Retention policies (ticks: 7 days, M1: 90 days, D1: 10 years)
- REST API for historical data access

**pat-master Service**
- Engine Output Contract validation and normalization
- Dynamic weight computation (90-day Sharpe, regime relevance, temporal alignment)
- Independence discounting algorithm (Jaccard similarity overlap detection)
- Directional fusion with conflict detection (standard deviation threshold)
- 15-dimension scoring framework implementation
- Hard override pipeline (DI Kala penalty, CW mandatory flat, risk breakers)
- Verdict emission to Valkey Pub/Sub and TimescaleDB persistence
- SHA-256 immutability hash generation
- Replay verification system

**pat-api Service**
- JWT-based authentication with role-based access control (5 roles)
- API key management system
- Rate limiting middleware (global and per-endpoint limits)
- REST API endpoints for verdicts, engine outputs, instruments
- WebSocket hub for real-time verdict delivery (5 channels)
- Service client for inter-service communication
- Prometheus instrumentation and health endpoints
- Input validation and output sanitization

**pat-frontend Service**
- Next.js 15 App Router implementation
- Real-time Master Verdict dashboard display
- Instrument selector with search and timeframe switcher (M1-D1)
- 6-pillar radar hexagon visualization (Recharts/D3)
- Engine output drill-down per engine family
- Verdict history table with sort/filter/export capabilities
- PDF, Excel, CSV, JSON export functionality
- Alert configuration interface (thresholds, notifications)
- JWT authentication flow and session management
- Dark/light theme toggle
- Mobile-responsive layout

**pat-execution Service**
- ZeroMQ Bridge v2 (ROUTER/DEALER + PUB/SUB protocol)
- HMAC-SHA256 message signing for EA verification
- MQL5 Expert Advisor v2 integration
- Unified crypto exchange connectors (Binance, OKX)
- Paper trading engine with latency/slippage/fill-probability models
- Portfolio risk manager (Kelly criterion, correlation-adjusted VaR)
- Order abstraction layer (market, limit, stop-loss, take-profit)
- Position tracking and PnL calculation
- Circuit breakers and risk limits

### 4. API Requirements

**REST API Endpoints**
- `GET /v2/master/verdicts/{instrument}/{timeframe}` - Latest verdict
- `GET /v2/master/verdicts/{instrument}/{timeframe}/history` - Paginated history
- `GET /v2/engines/{engine}/outputs/{instrument}/{timeframe}` - Engine outputs
- `GET /v2/instruments` - Instrument registry with metadata
- `POST /v2/backtest` - Historical backtesting interface
- `GET /v2/health` - Service health status
- `POST /v2/auth/login` - JWT authentication
- `POST /v2/api-keys` - API key management

**WebSocket Channels**
- `verdicts` - Real-time Master Verdict updates
- `engines` - Individual engine output streams
- `instruments` - Instrument metadata updates
- `alerts` - Triggered alert notifications
- `system` - System status and health updates

**Authentication & Security**
- JWT token validation with refresh mechanism
- API key authentication for service-to-service calls
- Role-based access control (Admin, Trader, Analyst, Viewer, Guest)
- Rate limiting per IP and API key
- Input validation and SQL injection prevention
- Output encoding to prevent XSS

### 5. Data Requirements

**Database Schema**
- TimescaleDB hypertables for time-series data:
  - `market.ohlcv_data` - OHLCV market data
  - `astro.ephemeris_cache` - Planetary positions (2015-2030)
  - `macro.news_feed` - Sentiment-scored news events
  - `signals.engine_outputs` - Immutable engine outputs
  - `signals.master_verdicts` - Master verdicts with SHA-256 hashes
  - `signals.master_conflicts` - Detected conflicts between engines
  - `signals.master_overrides` - Applied override gates
  - `audit.events` - Security and operations audit trail
  - `execution.orders` - Order lifecycle tracking
  - `execution.positions` - Position and PnL tracking

**Data Retention Policies**
- Market tick data: 7 days
- Market M1 bars: 90 days  
- Market D1 bars: 10 years
- Engine outputs: 5 years (replay capability)
- Master verdicts: 10 years (immutable record)
- Audit logs: 7 years (compliance)

### 6. Integration Requirements

**External Data Providers**
- TwelveData (primary OHLCV source)
- Yahoo Finance (backup/secondary source)
- AlphaVantage (tertiary source)
- Swiss Ephemeris (via PySwissEph library)
- Economic calendars (ForexFactory, Investing.com, etc.)
- CFTC COT reports (weekly futures positioning)
- Social media APIs (Twitter/X, Reddit, StockTwits)
- Options data providers (CBOE, ORATS)

**Execution Brokers**
- MetaTrader 4/5 (ZeroMQ bridge)
- Binance Spot and Futures (REST/WebSocket)
- OKX Spot and Futures (REST/WebSocket)
- Paper trading engine (for validation)

**Notification Systems**
- Email (SMTP with TLS)
- Telegram Bot API
- Discord Webhooks
- SMS (Twilio)
- Slack Webhooks (for internal alerts)

## Non-Functional Requirements

### 1. Scalability
- Horizontal scaling of stateless engine services
- Database read replicas for API/frontend workloads
- Valkey clustering for cache/broker layer
- WebSocket hub fanout scaling
- Target: 200+ concurrent WebSocket connections
- Target: 50+ REST requests per second sustained
- Engine computation SLA: <5 seconds per instrument/timeframe

### 2. Reliability
- 99.9% uptime SLA for core services
- Automated failover for critical services
- Data replication and backup verification
- Circuit breakers and graceful degradation
- Health checks and self-healing mechanisms
- Disaster recovery RTO < 4 hours, RPO < 1 hour

### 3. Security
- OWASP ASVS Level 3 compliance
- Defense-in-depth zone architecture
- Mutual TLS for service-to-service communication where applicable
- Regular security scanning and penetration testing
- Secrets management with rotation capabilities
- Audit logging for all privileged operations
- Input validation and output encoding
- Rate limiting and DDoS protection
- SQL injection and XSS prevention
- CSRF protection for web interfaces

### 4. Performance
- Engine response time: <5 seconds (95th percentile)
- API response time: <200ms for 95th percentile requests
- WebSocket message delivery: <100ms latency
- Database query optimization: proper indexing and partitioning
- Caching strategy for frequently accessed data
- Asynchronous processing for non-critical paths
- Resource utilization monitoring and alerting

### 5. Maintainability
- Modular, loosely-coupled service architecture
- Comprehensive API documentation (OpenAPI 3.1)
- Standardized logging (structured JSON)
- Centralized configuration management
- Automated testing (unit >80% coverage)
- Clear service boundaries and contracts
- Versioned APIs with backward compatibility
- Comprehensive runbooks and operational documentation
- Code quality gates (linting, type checking, formatting)

### 6. Observability
- Four Golden Signals monitoring (latency, traffic, errors, saturation)
- Distributed tracing for cross-service requests
- Structured logging with correlation IDs
- Custom business metrics (engine accuracy, verdict distribution)
- Alerting on SLO violations and anomaly detection
- Dashboard for operational and business metrics
- Log retention and analysis capabilities
- Health check endpoints for all services

### 7. Availability
- Rolling restart capability for updates
- Load balancing and health-check gating
- Graceful degradation during partial outages
- Backup and restore procedures tested regularly
- Geographic disaster recovery site (planned)
- Maintenance windows with advance notification

### 8. Compliance
- GDPR/CCPA data privacy considerations
- Financial advice disclaimers prominent
- Audit trail for all regulatory requirements
- Data retention and disposal policies
- Regular compliance reporting capabilities
- Accessibility compliance (WCAG 2.1 AA) for frontend

### 9. Internationalization
- Unicode UTF-8 support throughout
- Date/time handling in UTC with proper timezone conversion
- Numerical formatting localization ready
- Text externalization for future translation
- RTL layout consideration in frontend design

## Acceptance Criteria

### Architectural Acceptance
- [ ] New codebase independent from any previous implementation
- [ ] All engines run independently and publish immutable outputs
- [ ] Only the Master Engine publishes the canonical verdict
- [ ] GUI and execution consume only Master Engine verdicts
- [ ] Deterministic verdict reproduction from stored inputs + logic version

### Functional Acceptance
- [ ] Verdict Terminal shows one master score as primary
- [ ] Users can drill into contributor engines, conflicts, and overrides
- [ ] Alerts and APIs distribute only canonical verdicts
- [ ] Execution routes cannot trade without master authorization
- [ ] Historical replay produces identical verdicts

### Quality Acceptance
- [ ] Score reproduction is deterministic for identical input snapshots
- [ ] Overlap and double-counting controls demonstrably implemented
- [ ] Mandatory-flat and danger rules handled in dedicated override layer
- [ ] Walk-forward tests cover both engine and master validation layers
- [ ] Security audit passes with no critical findings
- [ ] Load testing meets performance SLAs
- [ ] All tests pass in CI/CD pipeline

## Deliverables

### Immediate Deliverables (This Phase)
1. Complete source code implementation for all services
2. Database schema and migration system
3. Dockerfiles and docker-compose for development
4. systemd service unit files for production
5. Configuration management system
6. Comprehensive test suite
7. CI/CD pipeline configuration
8. Deployment documentation and runbooks
9. API documentation (OpenAPI 3.1)
10. Architecture decision records (ADRs)

### Future Deliverables
1. Production deployment to target infrastructure
2. Performance tuning and optimization
3. Security hardening and penetration testing results
4. User acceptance testing completion
5. Documentation suite completion (47 files as specified in SOW)
6. Training materials and user guides
7. Support and maintenance procedures