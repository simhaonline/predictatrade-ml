# Deployment Overview & Comparison Matrix

## Purpose

Predict-A-Trade v2.0 supports six deployment targets, each optimized for different operational requirements, budgets, and team expertise levels. This document provides a unified comparison to help you select the right deployment strategy for your context.

## Deployment Targets

1. **Self-Hosted (systemd)** -- Bare-metal or VPS with systemd service units. The primary recommended model for production and the reference implementation.
2. **Docker Compose** -- Local development, CI testing, and small-scale staging environments.
3. **Kubernetes (GKE/EKS/AKS)** -- Managed Kubernetes for elastic scaling, zero-downtime deployments, and multi-region production.
4. **Hetzner Cloud** -- Bare-metal at 60-70% cost savings vs AWS/GCP. Ideal for compute-heavy, cost-sensitive production.
5. **Single-Node (Minimum)** -- All services on one machine for personal use or evaluation. Not for production.
6. **Distributed (Multi-Node)** -- Services split across multiple machines with network isolation. Production-grade without Kubernetes.

## Comparison Matrix

| Criterion                    | Self-Hosted (systemd) | Docker Compose | Kubernetes      | Hetzner Cloud  | Single-Node | Distributed |
|-----------------------------|----------------------|----------------|-----------------|----------------|-------------|-------------|
| **Complexity**              | Medium               | Low            | High            | Medium-High    | Very Low    | Medium      |
| **Setup Time**              | 2-4 hours            | 15-30 minutes  | 4-8 hours       | 3-6 hours      | 30 minutes  | 3-5 hours   |
| **Scalability**             | Manual               | Manual (single host) | Automatic (HPA) | Manual (add servers) | None | Manual |
| **Zero-Downtime Deploy**   | Yes (rolling)        | No (restart)   | Yes (rolling)   | Yes (rolling)  | No           | Yes (rolling) |
| **Auto-Healing**           | systemd restarts     | restart policy | Native (liveness probes) | systemd restarts | systemd | systemd |
| **Monitoring**             | Prometheus/Grafana/Loki | Built-in containers | Built-in + Cloud Monitoring | Prometheus/Grafana/Loki | Lightweight | Prometheus/Grafana/Loki |
| **Secret Management**      | Vault or .env        | .env file or Vault | External Secrets + Vault | Vault or .env | .env file | Vault |
| **Cost (Monthly Est.)**    | EUR 100-500          | EUR 20-100     | EUR 1,000-5,000 | EUR 140-1,200 | EUR 10-50  | EUR 150-800 |
| **Best For**               | Production, full control | Dev, CI, staging | Large-scale production | Cost-optimized production | Personal use | Small team production |

## Decision Guide

Use this flowchart to determine your deployment target:

```
Q1: Is this for personal use or evaluation?
    YES --> Single-Node
    NO  --> Q2

Q2: Is this for local development or CI testing?
    YES --> Docker Compose
    NO  --> Q3

Q3: Do you need elastic auto-scaling (sub-minute)?
    YES --> Kubernetes
    NO  --> Q4

Q4: Is budget the primary constraint?
    YES --> Hetzner Cloud or Self-Hosted
    NO  --> Q5

Q5: Do you want maximum control and simplicity?
    YES --> Self-Hosted (systemd)
    NO  --> Distributed
```

## Minimum vs Distributed Deployment

### Minimum Deployment (Single-Node)

All services co-located on a single machine. Suitable for development, testing, and personal use. Not suitable for production because a single point of failure takes down the entire platform.

**Minimum hardware requirements:**
- 16 CPU cores
- 32 GB RAM
- 200 GB SSD (NVMe preferred)
- Alma Linux 10 or Ubuntu 24.04

**Limitations:**
- No horizontal scaling
- Single point of failure
- Contention for CPU and I/O between engines and database
- One machine must run PostgreSQL, Valkey, 10 engine processes, the Master Engine, API, frontend, and monitoring concurrently

### Distributed Deployment (Multi-Node)

Services split across three to six machines for isolation, fault tolerance, and independent scaling.

**Recommended distribution:**

| Machine Role    | Services                                                                | Specs              |
|-----------------|-------------------------------------------------------------------------|--------------------|
| Load Balancer   | NGINX, certbot, Prometheus, Grafana, Loki                              | 4 cores, 8 GB RAM  |
| Database        | PostgreSQL 16+TimescaleDB, Valkey, pat-data, MLflow                    | 16 cores, 64 GB RAM, NVMe RAID |
| Engine Pool 1   | pat-master, CV, AI, Western, COT engines                               | 32+ cores, 128 GB RAM |
| Engine Pool 2   | DI, CW, Seasonality, Macro, Tech, Exec engines                         | 16 cores, 64 GB RAM |
| API/Frontend    | pat-api, pat-frontend, pat-execution                                   | 8 cores, 16 GB RAM |

## Shared Configuration Across All Targets

Regardless of deployment target, the following configuration files are shared and versioned in the repository:

```
config/
  engine_registry.yaml        # Engine family definitions, ports, scoring weights
  master_config.yaml          # Master Engine settings, timeouts, verdict thresholds
  scoring_weights.yaml        # 15-dimension scoring matrix
  data_pipeline.yaml          # Data ingestion schedule and sources
  broker_config.yaml          # Broker API endpoints (credentials from Vault)
  monitoring.yaml             # Prometheus scrape targets, alerting rules
```

Environment-specific overrides are stored in `config/env/` and applied at deploy time:

```
config/env/
  development.yaml
  staging.yaml
  production.yaml
  ci.yaml
```

## Monitoring Stack (Common)

All deployments include the same monitoring triad:

- **Prometheus** -- Metrics collection, alerting rules, 15s scrape interval
- **Grafana** -- Dashboards for system health, engine performance, trading activity, and ML model drift
- **Loki** -- Centralized log aggregation with structured logging (JSON format) from all services

Pre-built dashboards in `grafana/dashboards/`:
- `system-overview.json` -- CPU, memory, disk, network per host
- `engine-performance.json` -- Per-engine latency, throughput, error rates
- `master-verdicts.json` -- Verdict volume, confidence distribution, scoring breakdown
- `trading-activity.json` -- Order flow, execution latency, P&L

## Security Posture (Common)

All deployments enforce these security controls:

- TLS 1.3 for all external traffic (Let's Encrypt or commercial certificates)
- Internal service communication over private networks (no public exposure of databases or engines)
- JWT + API key authentication on the API gateway
- RBAC for admin operations
- Secrets stored in HashiCorp Vault (production) or encrypted .env files (development)
- SELinux enforcing on all hosts
- firewalld with default-deny and explicit service allowlisting
- Regular security audits via `pat-cso` engine (Compliance and Security Officer engine family)

## Backup Strategy (Common)

- **Databases:** Hourly WAL archiving to Wasabi S3, daily full `pg_dump`
- **MLflow models:** Synced to Wasabi S3 after each training run
- **Configuration:** Git versioned, mirrored to Wasabi S3 weekly
- **Logs:** Retained 30 days in Loki, archived beyond 30 days to Wasabi S3
- **Retention:** 90-day rolling window for backups, 7-year minimum for financial records (compliance)

## Recommended Path

For most teams starting with Predict-A-Trade v2.0:

1. **Begin with Docker Compose** for local development and understanding the platform.
2. **Move to Single-Node (systemd)** for staging and small-scale testing.
3. **Adopt Self-Hosted (Distributed)** for production with 2-6 servers.
4. **Consider Hetzner Cloud** for cost-optimized bare-metal production.
5. **Scale to Kubernetes** only when auto-scaling and multi-region requirements justify the operational overhead.

Each target shares the same core platform, so migrating between them requires only configuration changes, not application logic changes.
