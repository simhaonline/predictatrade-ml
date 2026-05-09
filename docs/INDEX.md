# Documentation Index

## Overview

This is the master index of all Predict-A-Trade v2.0 project documentation. It catalogs every document across the `docs/` directory tree, organized by category. Use this page to quickly locate the document you need.

## Document Catalog

### Guides (`docs/guides/`)

Operational guides for developers, operators, and integrators.

| Document | Path | Purpose | Audience |
|---------|------|---------|----------|
| API Guide | `docs/guides/api-guide.md` | Complete REST + WebSocket API reference with authentication, endpoints, pagination, rate limiting, and code examples in curl, Python, and JavaScript | Developers, Integrators |
| Architecture Summary | `docs/guides/architecture-summary.md` | Condensed one-page blueprint of the MOIL 6-layer architecture with ASCII diagram, key decisions, service topology, data flow, and tech stack justification | Architects, Engineers, Leadership |
| Deployment: Docker | `docs/guides/deployment-docker.md` | Docker Compose configuration for local development, CI, and staging with service definitions, volumes, environment variables, resource limits, and healthchecks | Developers, DevOps |
| Deployment: Kubernetes | `docs/guides/deployment-k8s.md` | Kubernetes deployment on GKE/EKS/AKS with namespaces, Deployments, StatefulSets, ConfigMaps, External Secrets, HPA, NetworkPolicies, Helm chart, Ingress, and CI/CD pipeline | DevOps, SRE, Platform Engineers |
| Deployment: Hetzner Cloud | `docs/guides/deployment-hetzner.md` | Hetzner Cloud bare-metal deployment with server specs, cost comparison (60-70% savings), hcloud CLI provisioning, step-by-step bootstrap, and trade-off analysis | DevOps, Decision Makers |
| Deployment: Overview | `docs/guides/deployment-overview.md` | Comparison matrix across all 6 deployment targets with decision guide, minimum vs. distributed, shared config, monitoring stack, and security posture | All Audiences |
| Deployment: Self-Hosted | `docs/guides/deployment-self-hosted.md` | Bare-metal/VPS deployment with systemd -- the primary model. Covers OS hardening, service unit files, NGINX TLS, PostgreSQL+TimescaleDB, firewall/SELinux, monitoring, and backups | DevOps, System Administrators |
| Implementation Summary | `docs/guides/implementation-summary.md` | Current-state snapshot: what's built, in progress, next. Engine build status per engine, blockers, milestones, sprint goals, resource allocation, and risk assessment | Engineers, PMs, Stakeholders |
| Technical Roadmap | `docs/guides/technical-roadmap.md` | Dated milestones Q2 2026 through Q4 2027 across 5 phases. Dependencies, success criteria, risk register, and resource allocation | Leadership, PMs, All Teams |
| Technical Compliance | `docs/guides/technical-compliance-guidelines.md` | Coding standards (Python, TS, infra-as-code), git workflow, test requirements, security, accessibility, performance budgets, documentation, and dependency management | Developers, Reviewers |
| Documentation Index | `docs/guides/INDEX.md` | This file: master catalog of all project documentation | All Audiences |

### Core Documentation (`docs/core/`)

Foundational architecture and design documents.

| Document | Path | Purpose | Audience |
|---------|------|---------|----------|
| Platform Architecture | `docs/core/architecture.md` | Full system architecture, layer definitions, component interactions, and design philosophy | Architects, Engineers |
| Master Engine Design | `docs/core/master-engine.md` | Deep dive into the Master Engine: orchestration logic, scoring framework, verdict lifecycle, fault tolerance | Engineers |
| Engine Registry | `docs/core/engine-registry.md` | Definitions for all 10 engine families: inputs, outputs, scoring dimensions, model types | Engineers |
| Data Model | `docs/core/data-model.md` | Database schema, TimescaleDB hypertable definitions, relationships, indexing strategy | Data Engineers |
| Scoring Framework | `docs/core/scoring-framework.md` | 15-dimension scoring methodology, weight calibration, confidence intervals | Quantitative Analysts |
| Security Architecture | `docs/core/security.md` | Authentication flow, authorization model, secret management, network security | Security Engineers |
| ADR Index | `docs/core/adr/` | Architecture Decision Records -- numbered decisions with context and rationale | Architects |

### Audit Documentation (`docs/audit/`)

Compliance, security audit, and governance records.

| Document | Path | Purpose | Audience |
|---------|------|---------|----------|
| Audit Trail | `docs/audit/audit-trail.md` | Log of all audits conducted, findings, and remediation | Compliance Officers |
| SOC 2 Checklist | `docs/audit/soc2-checklist.md` | SOC 2 Type I/II control mapping and status | Compliance Officers |
| Security Review Log | `docs/audit/security-reviews.md` | Log of completed security reviews per feature/release | Security Engineers |

### Academic Documentation (`docs/academic/`)

Research papers, whitepapers, and methodological background.

| Document | Path | Purpose | Audience |
|---------|------|---------|----------|
| MOIL Whitepaper | `docs/academic/moil-whitepaper.md` | Formal description of the Master-Orchestrated Intelligence Layer concept and framework | Researchers, Academics |
| Engine Methodology | `docs/academic/engine-methodology.md` | Per-engine research basis, literature review, and validation methodology | Quantitative Researchers |
| Backtesting Framework | `docs/academic/backtesting.md` | Backtesting methodology, metrics, benchmark construction, and statistical validation | Quantitative Analysts |
| References | `docs/academic/references.md` | Academic and industry references cited across the platform documentation | Researchers |

### Legal Documentation (`docs/legal/`)

Terms, policies, and legal disclosures.

| Document | Path | Purpose | Audience |
|---------|------|---------|----------|
| Terms of Service | `docs/legal/terms-of-service.md` | Platform terms of service for users | Users, Legal |
| Privacy Policy | `docs/legal/privacy-policy.md` | Data collection, processing, and retention policies | Users, Legal |
| Risk Disclaimer | `docs/legal/risk-disclaimer.md` | Trading risk disclosures and limitations of liability | Users, Legal |
| GDPR Compliance | `docs/legal/gdpr.md` | GDPR compliance documentation and data processing records | DPO, Legal |

### Operational Documentation (`docs/ops/`)

Runbooks, incident response, and operational procedures.

| Document | Path | Purpose | Audience |
|---------|------|---------|----------|
| Incident Response | `docs/ops/incident-response.md` | Incident severity levels, escalation paths, communication templates | SRE, On-Call |
| Database Failover | `docs/ops/database-failover.md` | Runbook for PostgreSQL failover and recovery procedures | SRE, DBAs |
| Engine Degradation | `docs/ops/engine-degradation.md` | Runbook for handling engine timeouts, degraded outputs, and recovery | SRE |
| Backup & Restore | `docs/ops/backup-restore.md` | Backup verification and disaster recovery procedures | SRE |
| Monitoring Setup | `docs/ops/monitoring.md` | Prometheus/Grafana/Loki configuration details and alert routing | SRE |

## Quick Navigation

### By Role

**Developer:**
- Start with: `docs/guides/architecture-summary.md`
- Setup: `docs/guides/deployment-docker.md`
- API: `docs/guides/api-guide.md`
- Standards: `docs/guides/technical-compliance-guidelines.md`

**DevOps/SRE:**
- Overview: `docs/guides/deployment-overview.md`
- Production: `docs/guides/deployment-self-hosted.md` or `docs/guides/deployment-k8s.md`
- Cost-Optimized: `docs/guides/deployment-hetzner.md`
- Runbooks: `docs/ops/`

**Product Manager/Stakeholder:**
- Status: `docs/guides/implementation-summary.md`
- Future: `docs/guides/technical-roadmap.md`
- Context: `docs/guides/architecture-summary.md`

**Integrator/API Consumer:**
- API: `docs/guides/api-guide.md`
- Architecture: `docs/guides/architecture-summary.md`

**Security/Compliance:**
- Standards: `docs/guides/technical-compliance-guidelines.md`
- Architecture: `docs/core/security.md`
- Records: `docs/audit/`
- Legal: `docs/legal/`

### By Topic

| Topic | Key Documents |
|-------|--------------|
| Getting Started | `deployment-docker.md`, `deployment-self-hosted.md` |
| Architecture | `architecture-summary.md`, `docs/core/architecture.md` |
| API Integration | `api-guide.md` |
| Engine Development | `docs/core/engine-registry.md`, `docs/core/scoring-framework.md` |
| Deployment | `deployment-overview.md` (start here, then choose target) |
| Testing & QA | `technical-compliance-guidelines.md` (testing section) |
| Security | `docs/core/security.md`, `technical-compliance-guidelines.md` (security section) |
| Operations | `docs/ops/` |
| Roadmap & Planning | `implementation-summary.md`, `technical-roadmap.md` |

## External Links

- **GitHub Repository:** [https://github.com/predictatrade/platform](https://github.com/predictatrade/platform)
- **API Documentation (live):** [https://api.predictatrade.com/v2/openapi.json](https://api.predictatrade.com/v2/openapi.json)
- **Swagger UI:** [https://api.predictatrade.com/docs](https://api.predictatrade.com/docs)
- **Grafana Dashboards:** [https://monitoring.predictatrade.com](https://monitoring.predictatrade.com)
- **MLflow Tracking:** [https://mlflow.predictatrade.com](https://mlflow.predictatrade.com)
- **Status Page:** [https://status.predictatrade.com](https://status.predictatrade.com)

## Document Status Legend

| Status | Meaning |
|--------|---------|
| **Complete** | Fully written and reviewed. Reflects current state. |
| **In Progress** | Being actively written or revised. |
| **Planned** | Placeholder exists, content pending. |
| **Deprecated** | Superseded by a newer document. Retained for historical reference. |

## Conventions

- All document paths in this index are relative to the repository root (`/srv/predictatrade.com/`).
- Documents are in Markdown format (`.md`) unless otherwise noted.
- This index is regenerated on each significant documentation change. To request an update, open a `docs` issue on GitHub.

---

Last updated: 2026-05-05
