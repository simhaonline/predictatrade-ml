# PRODUCTION GRADE SCOPE OF WORK (SOW)
## Predict-A-Trade vNext: Greenfield Master-Orchestrated Intelligence Architecture

**Version:** 2.0 Final (Merged Scope)
**Project:** Predict-A-Trade Rebuild (Greenfield)
**Classification:** Internal Product and Engineering Scope
**Delivery Model:** From-scratch rebuild (No refactor)
**Primary Initial Market:** XAUUSD
**Architecture Style:** Master-Orchestrated Intelligence Layer (MOIL)

---

## 1. EXECUTIVE DEFINITION

Predict-A-Trade vNext is a **greenfield trading intelligence platform** built from first principles. It is not a refactor or cleanup of previous implementations but a completely new system designed around a single architectural law: **analysis is decentralized, but decision authority is centralized.**

The objective is to solve the critical architectural problem where multiple analysis engines (CV, AI, Astrology, DI, COT, etc.) mix conclusions into the final result too early, causing score contamination, hidden double-counting, blurred accountability, and unstable trade decisions.

The new system will ingest market, time, macro, ephemeris, and execution-state data; run multiple independent engines in parallel; store their outputs immutably; and submit those outputs to a dedicated **Master Engine**. This Master Engine is the *only* component authorized to compute the canonical tradable score, client verdict, and execution eligibility.

---

## 2. CORE ARCHITECTURAL LAW

The system shall follow one non-negotiable law:

> **Engines analyze independently. The Master Engine alone decides the official score, verdict, and tradeability state.**

Implications:
*   **No Engine** may publish the final client verdict or trade command.
*   **No Engine** may directly command trade execution or override another engine.
*   **No GUI** component may invent its own verdict from raw engine data.
*   **No Execution** bridge may redefine market direction independently of the Master Engine.

---

## 3. SYSTEM ARCHITECTURE: THE 6-LAYER MODEL

The platform shall operate as a strict six-layer stack to enforce separation of concerns.

| Layer | Role | Final Verdict Authority? |
| :--- | :--- | :--- |
| **1. Data Foundation Layer** | Raw ingestion, normalization, caching, historical replay, feature prep. | **NO** |
| **2. Independent Analysis Layer** | Engine-specific analysis (CV, AI, DI, etc.) and immutable output generation. | **NO** |
| **3. Master Decision Layer** | Score normalization, weighting, conflict resolution, overrides, canonical verdict. | **YES** |
| **4. Delivery Layer** | APIs, GUI (Verdict Terminal), alerts, subscriptions. | **NO** |
| **5. Execution Layer** | MT4/MT5 bridge, crypto router, order gating, lifecycle controls. | **NO** |
| **6. Operations Layer** | Security, observability, backups, deployment, audit. | **NO** |

---

## 4. ENGINE INVENTORY & DOMAIN LOGIC

The following independent engine families are defined for the rebuild. Each must adhere to the **Standard Engine Output Contract** (Section 6.1). The Master Engine will evaluate each based on specific domain logic defined below.

| Engine Family | Role & Domain | Master Engine Evaluation Criteria |
| :--- | :--- | :--- |
| **CV / VisionAI** | Real-time context engine (Microstructure, Liquidity, 8-source fusion). | Score heavily on **freshness** and **microstructure relevance**. Penalize overreaction to intraday noise. Check for conflicts between sub-agents. |
| **AI Signal** | Predictive engine (XGBoost, LSTM, Transformer) using price, macro, and symbolic features. | **Do not trust confidence blindly.** Separate model confidence from reliability. Penalize if unsupported by independent engines. |
| **DI / Vedic** | Sidereal timing/bias engine (17 bodies, Dashas, Eclipses, Nakshatras). | Assess **timing utility** over absolute direction. Use primarily for risk modulation. Reward internal coherence; penalize vague mystical language. |
| **Chinese Wisdom** | Symbolic timing (Feng Shui, I Ching, Bazi, Flying Stars). | Demand explicit mapping to tradable implications. Treat as conditional confluence; apply strong confidence discount unless precise. |
| **Western Astrology** | Tropical cycle/timing (Aspects, Retrogrades, Ingesses, Lunations). | Reward explicit date-window clarity. Penalize over-signaling (too many aspects treated as equal). |
| **COT Analytics** | Positioning engine (CFTC data, extremes, crowding). | High relevance for **swing/positional**; low for intraday. Distinguish exhaustion from continuation. |
| **Seasonality** | Historical pattern engine (Calendar tendencies, recurring windows). | Use as **contextual prior** only. Penalize if current macro regime invalidates historical edge. |
| **Technical Structure** | Observable chart engine (ICT/SMC, Price Action, Pattern state). | Standard directional input. Verify alignment with CV engine for micro-confirmation. |
| **Macro / Sentiment** | External context (FinBERT, Economic Calendar, Intermarket). | Assess headwinds/tailwinds. Use for regime filtering. |
| **Execution Readiness** | Implementation gate (Liquidity, Latency, Circuit Breakers, Spreads). | **Critical:** Never allow this engine to determine *directional* truth. Only affects `actionability`. |

### 4.1 The "Composite" Rule
The legacy "Composite Scoring System" is **not** a peer engine. It is a derived aggregate. It must be reclassified as a **Legacy Advisory Module**. If used, its weight must be heavily discounted to avoid double-counting evidence already present in the individual engines.

---

## 5. MASTER ENGINE: LOGIC & ADJUDICATION SPECIFICATION

The Master Engine is the supervisory adjudication system. It transforms heterogeneous engine outputs into one coherent, auditable, confidence-calibrated master intelligence report.

### 5.1 Mandatory Normalization Schema
The Master Engine **must** normalize every engine input into the following internal schema before processing.

**Field Definitions:**
*   `normalized_direction_score`: -100 (Strong Bearish) to +100 (Strong Bullish).
*   `calibrated_confidence`: 0-100 (Adjusted by Master based on reliability).
*   `evidence_quality`: 0-100.
*   `freshness`: 0-100.
*   `independence`: 0-100 (Checks for overlap with other engines).
*   `timeframe_fit`: 0-100.

**Scoring Range:**
*   Strongly Bearish: -80 to -100
*   Moderately Bearish: -40 to -79
*   Neutral: -10 to +10
*   Moderately Bullish: +40 to +79
*   Strongly Bullish: +80 to +100

### 5.2 Default Engine Weight Model
Base influence ranges (adjustable by objective/timeframe):
*   **CV Engine:** 18% (High relevance for intraday/session).
*   **AI Signal:** 18% (Predictive core).
*   **DI / Vedic:** 10% (Timing overlay).
*   **Chinese Wisdom:** 8% (Secondary confluence).
*   **Western Astrology:** 9% (Cyclical timing).
*   **COT:** 11% (Positioning).
*   **Seasonality:** 8% (Context).
*   **Execution Readiness:** 6% (Actionability only).
*   **Legacy Composite:** 12% (Advisory, discounted).

### 5.3 Dimensional Master Scoring (15 Dimensions)
The Master Engine must score the final instrument/setup across these dimensions (0-100) before composing the verdict:
1.  Real-Time Context Quality
2.  Directional Predictive Signal Quality
3.  Timing Alignment Quality
4.  Structural Trend Quality
5.  Liquidity / Execution Quality
6.  Positioning Intelligence Quality
7.  Seasonal Context Quality
8.  Symbolic Confluence Quality
9.  Risk Environment Quality
10. Implementation Readiness
11. **Contradiction Severity** (Penalty Dimension)
12. Evidence Integrity
13. Confidence Calibration
14. Regime Compatibility
15. Final Opportunity Attractiveness

### 5.4 Fusion & Conviction Logic
**1. Directional Fusion:**
*   Calculate `weighted_direction = normalized_score * effective_weight * calibrated_confidence`.
*   Apply **Independence Discount**: If multiple engines rely on the same underlying premise (e.g., price), treat as 1 confirmation.
*   Apply **Timeframe-Fit Discount**: Down-weight COT/Seasonality for scalping.
*   Sum results to produce `net_direction_score`.

**2. Conviction Calculation:**
*   Driven by evidence quality, independent agreement, freshness, and absence of unresolved conflicts.
*   **Rule:** High Direction + Low Conviction = "Monitor Only" (Do not trade).
*   **Rule:** Unresolved high-quality conflicts must cap conviction severely.

**3. Conflict Reconciliation:**
*   Classify conflicts: Timeframe vs. Evidence, Symbolic vs. Observable, Stale vs. Fresh.
*   **Symbolic Rule:** If DI/CW/Western align on timing but differ on direction, treat as "Heightened Event Window," not directional consensus.
*   **Rule:** Do not manufacture consensus. Preserve "Uncertainty" explicitly.

### 5.5 Scenario Framework
The Master Engine must generate probability-weighted scenarios for the GUI:
*   **Bull Case** (Probability %, Thesis, Drivers).
*   **Base Case** (Probability %, Thesis, Drivers).
*   **Bear Case** (Probability %, Thesis, Drivers).
*   **Failure Case** (Probability %, Invalidation Triggers).

---

## 6. DATA CONTRACTS & SCHEMAS

### 6.1 Engine Output Contract (Immutable)
Every engine writes a standardized result to the database.

```json
{
  "engine_name": "String",
  "engine_version": "String",
  "decision_ts_utc": "Timestamp",
  "normalized_direction_score": -100 to 100,
  "raw_confidence": 0 to 100,
  "calibrated_confidence": 0 to 100,
  "evidence_quality": 0 to 100,
  "freshness": 0 to 100,
  "independence_hint": 0 to 100,
  "key_factors": ["String"],
  "risk_flags": ["String"],
  "invalidation_conditions": ["String"],
  "recommended_use": "timing|context|positioning|prediction|execution_gating",
  "output_hash": "SHA-256"
}
```

### 6.2 Master Verdict Contract (Final Output)
The output delivered to GUI and Execution.

```json
{
  "instrument": "String",
  "timeframe": "String",
  "final_direction": "bullish|bearish|neutral",
  "recommendation_band": "Aggressive Long|Constructive Long|Watch|Neutral|Constructive Short|Aggressive Short|Block",
  "net_direction_score": -100 to 100,
  "conviction_score": 0 to 100,
  "confidence_score": 0 to 100,
  "uncertainty_level": "low|medium|high|severe",
  "execution_readiness": "ready|conditional|blocked",
  "dimension_scores": { },
  "engine_registry": [ ],
  "top_risks": ["String"],
  "execution_layer": {
    "execution_allowed": true|false,
    "mode": "autonomous|semi-auto|manual",
    "risk_state": "normal|reduced|blocked"
  }
}
```

---

## 7. OVERRIDE & SAFETY FRAMEWORK

### 7.1 Master Risk Override Layer
Current "mandatory-flat" concepts (DI Apocalypse, Eclipses, Hexagram 29, Flying Star 5) must be moved out of engine scoring.
*   Engines may *publish* danger flags.
*   Only the Master Engine decides if these flags result in:
    *   Score Cap
    *   Reduced Size
    *   Watch-Only Status
    *   Execution Block (Hard Stop)

### 7.2 Execution Gating
The Master Engine determines `execution_allowed`.
*   Circuit breakers may block execution regardless of score but must *not* invent direction.
*   Slippage/Latency/Spread risk factors directly reduce `Implementation Readiness` scores.

---

## 8. TECHNOLOGY STACK & DEPLOYMENT

### 8.1 Tech Stack
| Domain | Technology |
| :--- | :--- |
| **OS** | Alma Linux 10 (Hardened) |
| **Backend** | Python 3.12, FastAPI |
| **Database** | PostgreSQL 16 + TimescaleDB |
| **Cache/Queue** | Valkey |
| **Frontend** | Next.js 15 + TailwindCSS |
| **Proxy** | NGINX |
| **ML/Research** | MLflow, Pandas, NumPy, PyTorch/TensorFlow |
| **Astro Data** | Swiss Ephemeris |
| **Observability** | Prometheus, Grafana, Loki |
| **Secrets** | HashiCorp Vault |
| **Backup** | Wasabi S3-compatible |

### 8.2 Deployment Model
*   **Bare-metal or Dedicated VPS.**
*   **No Docker/Kubernetes dependency.**
*   Systemd-managed services.
*   **Service Split:**
    *   `pat-data`: Ingestion.
    *   `pat-master`: Orchestration/Scoring.
    *   `pat-engine-[name]`: Specific engines (CV, AI, DI, etc.).
    *   `pat-execution`: MT4/MT5 & Crypto bridges.
    *   `pat-api`: Public/Private API.
    *   `pat-frontend`: GUI.

---

## 9. DATABASE & OPERATIONS

### 9.1 Database Requirements
*   **Replay-safe historical storage.**
*   Deterministic version-aware result recovery.
*   **Logical Entities:** `app`, `market_data`, `engine_outputs`, `master_scores`, `master_conflicts`, `master_overrides`, `execution_decisions`, `audit_events`.
*   **Key Rule:** The master verdict must be reproducible from stored engine outputs + stored master logic version.

### 9.2 Observability & Security
*   **Monitoring:** Per-service health, per-engine latency, stale-feed monitoring, master cycle completion.
*   **Security:** SELinux enforcing, firewalld, TLS, Vault-managed secrets, MFA, RBAC.
*   **Backup:** Daily WAL archival, scheduled base backups, MLflow artifact backup.

---

## 10. DEVELOPMENT PHASES (ROADMAP)

### Phase 0: Product Definition
*   Approve SOW, freeze Greenfield principles, confirm asset universe.

### Phase 1: Foundation Infrastructure
*   Provision servers (Alma Linux), harden OS, install DB/Cache/Proxy/Observability/Backup stacks.

### Phase 2: Contracts First
*   Define Engine Output Schema.
*   Define Master Verdict Schema.
*   Define API contracts.

### Phase 3: Data Platform
*   Instrument master, market ingestion, macro calendar, COT, seasonality jobs.
*   Precompute ephemeris and symbolic caches (2015–2030 target).

### Phase 4: Independent Engines
*   Build each engine (CV, AI, DI, etc.) with isolated inputs/outputs.
*   **Prohibit** final-score logic inside engines.

### Phase 5: Master Engine (Core Build)
*   Implement Normalization, Weighting, Conflict Handling, Override Framework.
*   Implement Canonical Score Generation.

### Phase 6: Research & Validation
*   Walk-forward framework.
*   Engine validation + Master validation.
*   Historical replay; Score stability analysis.

### Phase 7: Frontend & Delivery
*   Verdict Terminal (Next.js).
*   Alerts (Telegram/Email/Webhook).
*   Explainability views.

### Phase 8: Execution Integration
*   MT4/MT5 routing (ZeroMQ/HTTP).
*   Crypto exchange routing (Custom connectors).
*   Paper trading and staged live rollout.

### Phase 9: Ops Hardening & Launch
*   Load testing, Security review, Runbooks, Go-live checklist.

---

## 11. ACCEPTANCE CRITERIA

The greenfield product is accepted only when all of the following are true:

### 11.1 Architectural Acceptance
*   New codebase is independent from any previous project.
*   All engines run independently and publish immutable outputs.
*   **Only the Master Engine** publishes the canonical verdict.
*   GUI and execution consume *only* Master Engine verdicts.

### 11.2 Functional Acceptance
*   The Verdict Terminal shows one master score as primary.
*   Users can drill into contributor engines, conflicts, and overrides.
*   Alerts and APIs distribute only canonical verdicts.
*   Execution routes cannot trade without master authorization.

### 11.3 Quality Acceptance
*   Score reproduction is deterministic for the same input snapshot.
*   Overlap and double-counting controls are demonstrably implemented.
*   Mandatory-flat and danger rules are handled in a dedicated override layer.
*   Walk-forward tests cover both engine and master layers.

---

## 12. EXPLICIT PROHIBITIONS

The greenfield project shall not permit the following anti-patterns:
*   Engines publishing final client verdicts.
*   Execution services inventing direction.
*   Derived composites pretending to be raw evidence.
*   Hidden score blending in the GUI.
*   Symbolic outputs without explicit trading translation.
*   Ad hoc manual edits to production verdicts without audited override records.

---

## 13. DELIVERABLES

1.  Revised Master SOW and Architecture Blueprint (This Document).
2.  Engine Output JSON Schema.
3.  Master Verdict JSON Schema.
4.  Scoring and Weighting Rules Specification.
5.  Override and Conflict Resolution Specification.
6.  Database ERD for engine/master separation.
7.  GUI Verdict Terminal Specification.
8.  Execution Gate Specification (MT4/MT5 & Crypto).
9.  Security Architecture Document.
10. Bare-metal Deployment Runbook.

### 13.1 Documentation Suite — Organized by Domain (47 Files)

All documentation is organized under `docs/` into five subdirectories:

```
docs/
├── academic/       (8 files)  — PhD thesis: MOIL architecture for financial markets
├── audit/          (15 files) — Security audits, technical audits, data integrity reviews
├── core/           (5 files)  — Architecture blueprint, execution plan, TDD, tech reference
├── guides/         (15 files) — Deployment, API, admin, user, compliance, roadmap, index
└── legal/          (4 files)  — Business model, feasibility, financials, terms & privacy
```

#### 13.1.1 Academic (`docs/academic/`) — PhD Thesis

| File | Purpose |
|---|---|
| `thesis-abstract.md` | 300-word abstract, keywords, 4 research contributions |
| `thesis-ch1-introduction.md` | Problem statement, 5 research questions, scope, 4 contributions |
| `thesis-ch2-literature-review.md` | ML in finance, ensemble methods, multi-agent systems, financial astrology |
| `thesis-ch3-methodology.md` | MOIL 6-layer model, 5-stage adjudication pipeline, engine output contract, 15-dim scoring |
| `thesis-ch4-system-architecture.md` | Service boundaries, TimescaleDB 13 schemas, CV Engine 10-agent pipeline, SHA-256 integrity |
| `thesis-ch5-sustainability-esg.md` | Energy efficiency, algorithmic fairness, risk governance, data privacy |
| `thesis-ch6-conclusion.md` | Findings per RQ1-RQ5, limitations, 6 future work directions |
| `thesis-references.md` | 29 APA-formatted references |

#### 13.1.2 Audit (`docs/audit/`) — Security & Technical Audits

| File | Purpose |
|---|---|
| `pre-audit-security-assessment.md` | OWASP ASVS Level 2/3 coverage, STRIDE threat modeling, risk register (10 risks), 14-item checklist |
| `technical-audit-report.md` | 92/100 platform score, 6-layer enforcement review, 24 remediation recommendations (P0-P3) |
| `audit-report.md` | Comprehensive codebase audit (104 findings across 5 domains) |
| `audit_security.md` | Security domain deep-dive: OWASP Top 10, injection vectors, secrets management |
| `audit_data_integrity.md` | Data pipeline integrity, SHA-256 verification, schema compliance |
| `audit_functional_logic.md` | Business logic audit: scoring, signal generation, billing workflows |
| `audit_performance.md` | Performance profiling, query optimization, caching effectiveness |
| `security-audit-report.md` | Consolidated security report (512 lines, 7 domains) |
| `security_audit_cicd.md` | CI/CD pipeline security review |
| `security_audit_data.md` | Data layer security assessment |
| `security_audit_dependencies.md` | Dependency vulnerability scan |
| `security_audit_infrastructure.md` | Infrastructure hardening review |
| `security_audit_injection.md` | Injection vector analysis |
| `security_audit_runtime.md` | Runtime security assessment |
| `security_audit_secrets.md` | Secrets management review |

#### 13.1.3 Core (`docs/core/`) — Architecture & Engineering Foundation

| File | Purpose |
|---|---|
| `architecture.md` | Full 6-layer MOIL spec, service topology, data flow, security boundaries, scaling strategy |
| `execution-plan.md` | 10-phase roadmap (16-20 weeks), team structure, critical path, phase-gate criteria |
| `reference.md` | Glossary, scoring ranges, recommendation bands, API endpoints, config paths, env vars |
| `tdd.md` | Contract-first testing, 50+ Master fixture scenarios, walk-forward validation, CI/CD gates |
| `technical-report.md` | Normalisation algorithm, directional fusion math, independence discount, 15-dim framework, latency analysis |

#### 13.1.4 Guides (`docs/guides/`) — Operational & Deployment Documentation

| File | Purpose |
|---|---|
| `INDEX.md` | Master catalog of all 47 docs across 5 directories with quick-nav by audience |
| `admin-guide.md` | User lifecycle, RBAC, audit queries, backup/restore, PITR, incident response, hardening checklist |
| `user-guide.md` | Verdict Terminal, reading verdicts, contributor drill-down, alerts, API keys, subscriptions, FAQ |
| `api-guide.md` | REST + WebSocket API reference, JWT/API key auth, pagination, error codes, curl/Python/JS examples |
| `architecture-summary.md` | Condensed 1-page blueprint with ASCII layer diagram, 7 architectural decisions, data flow |
| `deployment-overview.md` | 6-target comparison matrix, decision guide, minimum vs distributed deployment |
| `deployment-self-hosted.md` | Bare-metal/VPS systemd deployment (primary model), OS hardening, unit files, NGINX TLS, monitoring |
| `deployment-aws.md` | AWS: EC2 types, RDS+TimescaleDB, ElastiCache, ALB, CloudWatch, cost estimate (~$8,470/mo) |
| `deployment-gcp.md` | GCP: Compute Engine, Cloud SQL/Memorystore, HTTPS LB, Cloud Monitoring, cost (~$5,970/mo) |
| `deployment-hetzner.md` | Hetzner bare-metal: AX102/EX130-R, hcloud CLI, 60-70% cost savings, bootstrap |
| `deployment-docker.md` | Docker Compose for local/dev/staging, all pat-* containers, volumes, env vars, healthchecks |
| `deployment-k8s.md` | Kubernetes (GKE/EKS/AKS): Deployments, StatefulSet, HPA, NetworkPolicy, Helm, Ingress |
| `implementation-summary.md` | Build status tracker: phase completion %, engine status, current blockers, sprint goals |
| `technical-roadmap.md` | Dated milestones Q2 2026–Q4 2027, dependencies, success criteria, risk register |
| `technical-compliance-guidelines.md` | Coding standards, git workflow, testing/security/perf/accessibility requirements |

#### 13.1.5 Legal (`docs/legal/`) — Business & Legal Foundation

| File | Purpose |
|---|---|
| `business-model.md` | SaaS tiers (Free/Pro $29/Elite $99), ARR projections, customer segments, GTM, monetization |
| `feasibility-report.md` | Technical/market/regulatory/operational/financial assessment, risk matrix, GO recommendation |
| `financial-projections.md` | 3-year projections (3 scenarios), cost structure, break-even (Month 8-10), sensitivity analysis |
| `terms-and-privacy-policy.md` | ToS, no-financial-advice disclaimer, IP protection, GDPR/CCPA privacy, arbitration clause |

## 14. FINAL DIRECTIVE

Predict-A-Trade vNext shall be built as a brand-new system, in a brand-new project folder, with brand-new contracts, brand-new service boundaries, and a brand-new Master Engine-centered decision model.

**Build many engines. Trust one Master Engine. Publish one canonical score.**
