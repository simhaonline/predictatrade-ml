# Technical Roadmap

## Overview

This roadmap outlines the development trajectory for Predict-A-Trade v2.0 from Q2 2026 through Q4 2027. It is organized into five phases, each with dated milestones, explicit dependencies, success criteria, resource requirements, and a risk register. The roadmap assumes a core team of 11 engineers plus domain experts as needed.

## Phase 1: Core Platform Foundation (Q2 2026)

**Goal:** Deliver a functional verdict pipeline from market data ingestion through Master Engine scoring to API-exposed verdicts. Minimum three engines operational with validated outputs.

### Milestones

| Milestone                        | Target Date | Owner       | Dependencies                          |
|---------------------------------|------------|-------------|---------------------------------------|
| M1.1: Monorepo & CI/CD           | Apr 15      | Infra       | None                                  |
| M1.2: DB schema + TimescaleDB    | Apr 20      | Data        | M1.1                                  |
| M1.3: pat-master pipeline        | Apr 25      | Master      | M1.1, M1.2                            |
| M1.4: Docker Compose dev env     | Apr 28      | Infra       | M1.1                                  |
| M1.5: CV engine v0.1             | May 10      | Engines     | M1.3, historical data                 |
| M1.6: Western engine v0.1        | May 15      | Engines     | M1.3, Swiss Ephemeris                  |
| M1.7: DI engine v0.1             | May 15      | Engines     | M1.3                                  |
| M1.8: REST API + auth             | May 20      | API         | M1.3                                  |
| M1.9: Frontend dashboard v0.1    | May 25      | Frontend    | M1.8                                  |
| M1.10: Integration tests pass    | Jun 1       | QA          | M1.5-M1.8                             |
| M1.11: Phase 1 release           | Jun 15      | All         | M1.10                                 |

### Success Criteria

- Verdict pipeline delivers end-to-end results in under 5 seconds for a single symbol/timeframe
- Three engines generate outputs with at least 55% directional accuracy in backtesting
- API handles 500 req/min sustained without degradation
- Frontend renders verdicts within 1 second of page load

### Resource Allocation

All 11 engineers focused on Phase 1. No parallel work streams.

## Phase 2: Engine Fleet Expansion (Q3 2026)

**Goal:** Bring all 10 engine families online with validated output quality. Expand to 15-dimension scoring with per-dimension weight calibration.

### Milestones

| Milestone                         | Target Date | Dependencies                     |
|----------------------------------|------------|----------------------------------|
| M2.1: AI engine v0.5 (fine-tuned) | Jul 15      | M1.11, LLM access, training data  |
| M2.2: COT engine v0.5            | Jul 30      | M1.11, CFTC data pipeline         |
| M2.3: Tech engine v0.5           | Jul 30      | M1.11                             |
| M2.4: Seasonality engine v0.5    | Aug 15      | M1.11, 5yr historical data        |
| M2.5: Macro engine v0.5          | Aug 15      | M1.11, FRED/ECB data integration   |
| M2.6: CW engine v0.5             | Aug 30      | M1.11                             |
| M2.7: Exec engine v0.5           | Aug 30      | M1.11, broker API                  |
| M2.8: Scoring calibration         | Sep 15      | M2.1-M2.7                         |
| M2.9: WebSocket API               | Sep 15      | M1.8                              |
| M2.10: Phase 2 release           | Sep 30      | M2.8, M2.9                        |

### Success Criteria

- All 10 engines operate reliably; average availability above 99.5%
- 15-dimension scoring calibrated against 5-year backtest with Sharpe ratio above 1.5
- Directional accuracy across engine fleet above 58%
- WebSocket streaming latency under 200ms from verdict generation to client delivery

## Phase 3: Production Operations (Q4 2026)

**Goal:** Achieve production-grade reliability, security hardening, and operational maturity. Deploy to primary production target (self-hosted or Hetzner). Begin paper trading.

### Milestones

| Milestone                            | Target Date | Dependencies       |
|-------------------------------------|------------|--------------------|
| M3.1: Vault production config        | Oct 15      | M2.10              |
| M3.2: Kubernetes production deploy   | Oct 15      | M2.10              |
| M3.3: Hetzner/self-hosted deploy     | Oct 30      | M2.10              |
| M3.4: Security audit (external)       | Nov 15      | M3.1-M3.3          |
| M3.5: Penetration test remediation   | Nov 30      | M3.4               |
| M3.6: broker paper trading live      | Nov 30      | M3.1, broker API    |
| M3.7: Monitoring alerting complete   | Dec 15      | M3.1-M3.3          |
| M3.8: Runbook & incident response    | Dec 15      | M3.7               |
| M3.9: Phase 3 release (GA)          | Dec 31      | All M3             |

### Success Criteria

- 99.9% platform uptime over trailing 30 days
- All security findings from external audit resolved or accepted with mitigation
- Paper trading operational with order confirmation latency under 1 second
- Mean time to detect (MTTD) under 5 minutes; mean time to resolve (MTTR) under 30 minutes
- SOC 2 Type I audit initiated

## Phase 4: Live Trading & Scale (H1 2027)

**Goal:** Transition from paper trading to live trading with real capital. Scale the platform to support multiple accounts and institutional clients.

### Milestones

| Milestone                              | Target Date | Dependencies     |
|---------------------------------------|------------|------------------|
| M4.1: Paper trading results validated | Jan 30      | M3.9             |
| M4.2: Risk management engine           | Feb 15      | M4.1             |
| M4.3: Live trading (small capital)    | Feb 28      | M4.1, M4.2       |
| M4.4: Multi-account support           | Mar 30      | M4.3             |
| M4.5: Institutional API tier           | Apr 30      | M4.4             |
| M4.6: Performance analytics dashboard | May 30      | M4.3             |
| M4.7: Phase 4 release                 | Jun 30      | All M4           |

### Success Criteria

- 3 months of live trading data with positive P&L
- Institutional client onboarding completed for 2+ beta partners
- Risk management prevents any single-day loss exceeding 5% of account value
- Platform cost as percentage of AUM below 2%

## Phase 5: Intelligence Maturation (H2 2027)

**Goal:** Advance the MOIL's intelligence through continuous learning, multi-asset expansion, and autonomous operation capabilities.

### Milestones

| Milestone                              | Target Date | Dependencies    |
|---------------------------------------|------------|-----------------|
| M5.1: Multi-asset class support       | Aug 30      | M4.7            |
| M5.2: Online learning pipeline         | Sep 30      | M4.7            |
| M5.3: Federated learning research     | Oct 30      | M5.2            |
| M5.4: Autonomous calibration          | Nov 30      | M5.2            |
| M5.5: Cross-asset correlation engine  | Dec 15      | M5.1, M4.7      |
| M5.6: Phase 5 release                 | Dec 31      | All M5          |

### Success Criteria

- Platform covers equities, futures, forex, and crypto
- Online learning improves directional accuracy by at least 2% quarterly
- Autonomous calibration reduces manual engine tuning by 80%
- Platform can operate for 7 days without human intervention

## Dependencies Graph (Critical Path)

```
M1.1 --> M1.3 --> M1.5/M1.6/M1.7 --> M1.10 --> M1.11
                                            \
                                             --> M2.1-M2.7 --> M2.8 --> M2.10
                                                                        \
                                                                         --> M3.1-M3.3 --> M3.4 --> M3.9
                                                                                                          \
                                                                                                           --> M4.1 --> M4.3 --> M4.7
```

## Risk Register

| ID  | Risk                                  | Probability | Impact | Mitigation Strategy                                    | Contingency Plan                        |
|-----|--------------------------------------|------------|--------|-------------------------------------------------------|----------------------------------------|
| R1  | Engine accuracy below 55% threshold  | Medium     | High   | Incremental training, ensemble weighting, feature engineering | Fall back to fewer engines with higher accuracy |
| R2  | LLM API costs exceed budget          | Medium     | Medium | Local model deployment (Llama), prompt caching, batch processing | Use open-weight models on bare metal |
| R3  | Broker API changes or rate limits    | Low        | High   | Abstraction layer, cached snapshots, multiple broker support | Manual order entry as emergency fallback |
| R4  | Data quality gaps in historical data | High       | Medium | Automated validation, multiple data source redundancy | Synthetic data generation for missing periods |
| R5  | Team member churn                    | Low        | Medium | Documentation, pair programming, knowledge sharing | Cross-training, documented onboarding |
| R6  | Regulatory changes (crypto/DeFi)     | Low        | High   | Compliance engine monitoring, legal advisory retainer | Feature flags to disable affected assets |
| R7  | Security breach                      | Low        | Critical | Regular audits, least privilege, Vault, monitoring | Incident response plan, data isolation |
| R8  | Performance degradation at scale     | Medium     | Medium | Load testing, profiling, caching layers | Read replicas, query optimization, rate limiting |

## Resource Allocation Per Phase

| Phase | Timeline     | Engineers | Focus Areas                                          | Budget (Monthly) |
|-------|-------------|-----------|------------------------------------------------------|------------------|
| 1     | Q2 2026     | 11        | Core platform, 3 engines, API, frontend               | EUR 50K          |
| 2     | Q3 2026     | 11        | Remaining 7 engines, scoring calibration, WebSocket   | EUR 55K          |
| 3     | Q4 2026     | 11 + 2 ops | Production deployment, security, paper trading       | EUR 70K          |
| 4     | H1 2027     | 9          | Live trading, scale, multi-account                    | EUR 60K          |
| 5     | H2 2027     | 8          | Intelligence maturation, multi-asset, autonomy        | EUR 55K          |

## Governance

- **Sprint cadence:** 2-week sprints with planning, review, and retrospective
- **Roadmap review:** Quarterly with stakeholders; monthly internal review
- **Change control:** Feature additions require written proposal with impact analysis on critical path
- **Reporting:** Weekly progress report against milestone targets; monthly executive summary

This roadmap is a living document. It will be updated at the end of each phase based on actual progress, lessons learned, and evolving market conditions.
