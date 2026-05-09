# Repository Understanding Report

## Project Purpose
Predict-A-Trade vNext is a greenfield trading intelligence platform built around the Master-Orchestrated Intelligence Layer (MOIL) architecture. The system solves the critical problem where multiple analysis engines mix conclusions too early, causing score contamination and unstable trade decisions. Instead, engines analyze independently and submit immutable outputs to a centralized Master Engine that alone computes the canonical tradable score, client verdict, and execution eligibility.

## Current Architecture
Based on the documentation, the planned architecture is a six-layer stack:
1. **Data Foundation Layer** - Market data ingestion, normalization, caching, historical replay
2. **Independent Analysis Layer** - Ten engine families (CV, AI, DI, Chinese Wisdom, Western Astrology, COT Analytics, Seasonality, Technical Structure, Macro/Sentiment, Execution Readiness) producing immutable Engine Output Contracts
3. **Master Decision Layer** - Master Engine that normalizes, weights, resolves conflicts, scores across 15 dimensions, and emits Master Verdict Contracts
4. **Delivery Layer** - APIs, GUI (Verdict Terminal), alerts, subscriptions
5. **Execution Layer** - MT4/MT5 bridge, crypto router, order gating, lifecycle controls
6. **Operations Layer** - Security, observability, backups, deployment, audit

## Tech Stack
- **Backend**: Python 3.12, FastAPI
- **Frontend**: Next.js 15 + TypeScript
- **Database**: PostgreSQL 16 + TimescaleDB
- **Cache/Queue**: Valkey 8.x
- **Execution Bridge**: ZeroMQ (ROUTER/DEALER + PUB/SUB)
- **Monitoring**: Prometheus, Grafana, Loki
- **Experiment Tracking**: MLflow
- **Web Server**: NGINX (TLS 1.3, HTTP/2)
- **Deployment**: systemd services on Alma Linux 10
- **Authentication**: JWT, API Keys, HMAC service-to-service tokens
- **AI/ML**: XGBoost, GLM-4, FinBERT, PyTorch/TensorFlow
- **Ephemeris**: Swiss Ephemeris via PySwissEph

## Modules/Services/Apps
Planned services (none currently implemented):
- `pat-data` - Market data ingestion service
- `pat-master` - Master Engine service (sole verdict authority)
- `pat-api` - REST API gateway with authentication and rate limiting
- `pat-frontend` - Next.js 15 verdict terminal application
- `pat-engine-ai` - AI Signal Engine (GLM-4 reasoning)
- `pat-engine-di` - Discretionary Intelligence Engine (Vedic Jyotish)
- `pat-engine-cw` - Chinese Wisdom Engine (BaZi, Flying Stars, I-Ching)
- `pat-engine-wa` - Western Astrology Engine (tropical transits)
- `pat-engine-smc-ict` - Smart Money Concepts / ICT Engine
- `pat-engine-vision` - Computer Vision Engine (GLM-4V chart recognition)
- `pat-engine-macro` - Macro/Sentiment Engine (COT, economic calendar)
- `pat-engine-technical` - Technical Structure Engine (indicators, patterns)
- `pat-engine-sentiment` - Sentiment Engine (FinBERT, social media)
- `pat-engine-intermarket` - Intermarket Engine (correlation, ETF flows)
- `pat-execution` - Execution layer (ZeroMQ bridge, crypto gateways)

## Existing Functionality
Based on file inspection, no source code currently exists in the repository. Progress logs indicate implementation work was performed on May 5-6, 2026, but no trace remains in the current filesystem.

## Missing Functionality
All implementation needs to be created:
1. Core service implementations (pat-data, pat-master, pat-api, pat-frontend, pat-execution)
2. All ten engine service implementations
3. Database schema and migration system
4. Docker containerization files
5. systemd service unit files
6. Configuration management system
7. Comprehensive test suite (unit, integration, end-to-end)
8. CI/CD pipeline configuration
9. Monitoring and alerting setup
10. Security hardening measures
11. Backup and disaster recovery procedures
12. Documentation (beyond what already exists)

## Technical Debt
None identified as this is a greenfield rebuild. However, careful attention must be paid to:
- Proper separation of concerns between layers
- Immutability of engine outputs
- Master Engine as sole verdict authority
- Security boundaries between zones
- Deterministic reproducibility of verdicts

## Security Concerns
From documentation, key security considerations:
- Zone-based architecture (Public Internet → DMZ → Application Core → Data Layer)
- Master Engine must never be exposed to public internet
- Service-to-service authentication via HMAC tokens
- Rate limiting and input validation
- Secrets management (HashiCorp Vault recommended)
- TLS 1.3 everywhere
- Regular security audits

## Performance Bottlenecks
Potential bottlenecks to address:
- Engine computation time (target <5s per instrument/timeframe)
- Database query optimization for TimescaleDB
- Valkey/PubSub throughput under load
- WebSocket fanout capabilities
- Horizontal scaling strategies for engine services

## Scalability Concerns
Planned scaling approaches:
- Horizontal engine scaling (stateless services behind load balancer)
- Database read replicas for API/frontend read paths
- Valkey clustering for cache/broker layer
- WebSocket hub horizontal scaling with shared PubSub backplane

## DX Issues
Developer experience considerations:
- Contract-first development approach
- Comprehensive API documentation (OpenAPI 3.1)
- Standardized logging and error handling
- Local development environment with Docker Compose
- Automated testing in CI/CD pipeline
- Clear service boundaries and interfaces

## Testing Gaps
Needed testing layers:
- Unit tests for all service components
- Integration tests for service communication
- End-to-end tests for critical user journeys
- Load testing and performance validation
- Security penetration testing
- Walk-forward validation against historical data
- Deterministic reproducibility verification

## Deployment Strategy
Planned deployment model:
- Bare-metal or dedicated VPS (no Docker/Kubernetes dependency preferred)
- Systemd-managed services
- Unified Makefile for service lifecycle management
- Blue-green deployment capability
- Rollback procedures
- Environment promotion (dev → staging → production)

## Infrastructure Overview
From documentation:
- OS: Alma Linux 10 (hardened with SELinux enforcing)
- Database: PostgreSQL 16 + TimescaleDB extension
- Cache/Broker: Valkey 8.x (persistence: AOF + RDB)
- Web Server: NGINX (TLS 1.3 certificates via Let's Encrypt)
- Monitoring: Prometheus node exporters, Grafana dashboards, Loki for log aggregation
- Backup: Wasabi S3-compatible storage with WAL archiving
- CI/CD: Cloud Build or Gitea Actions with build caching and automated DB migrations