# Predict-A-Trade vNext — Administration Guide

> **Version:** 2.0 | **Audience:** System Administrators, DevOps, SRE
> **Scope:** User management, RBAC, audit logging, backup/restore, system health

---

## 1. System Overview

Predict-A-Trade vNext is deployed as a set of systemd-managed services on Alma Linux 10.
The platform follows a 6-layer architecture with the Master Engine as the central decision
authority. This guide covers day-2 operations: user lifecycle, security, backups, and
incident response.

### 1.1 Service Inventory

| Service | Unit Name | Port | Purpose |
|---|---|---|---|
| API Server | `pat-api` | 8000 | REST + WebSocket endpoints |
| Master Engine | `pat-master` | 8001 | Orchestration, scoring, verdict dispatch |
| Data Ingestion | `pat-data` | 8002 | Market data, ephemeris, macro ingestion |
| Engine: CV | `pat-engine-cv` | 8100 | VisionAI 10-agent pipeline |
| Engine: AI | `pat-engine-ai` | 8101 | ML predictive models |
| Engine: DI | `pat-engine-di` | 8102 | Vedic Jyotish computations |
| Engine: CW | `pat-engine-cw` | 8103 | Chinese Wisdom computations |
| Engine: Western | `pat-engine-western` | 8104 | Western Astrology computations |
| Engine: COT | `pat-engine-cot` | 8105 | COT Analytics |
| Engine: Seasonality | `pat-engine-seasonality` | 8106 | Seasonal patterns |
| Engine: Macro | `pat-engine-macro` | 8107 | Macro / Sentiment |
| Engine: Tech | `pat-engine-tech` | 8108 | Technical Structure |
| Engine: Execution | `pat-engine-exec` | 8109 | Execution Readiness gating |
| Execution Bridge | `pat-execution` | 8200 | MT4/MT5 + Crypto routing |
| Frontend | `pat-frontend` | 3001 | Next.js Verdict Terminal |

### 1.2 Infrastructure Components

| Component | Port | Purpose |
|---|---|---|
| NGINX | 80/443 | TLS termination, reverse proxy, rate limiting |
| PostgreSQL 16 | 5432 | Primary database |
| TimescaleDB | — | Time-series extension (same PG instance) |
| Valkey | 6379 | Cache, session store, pub/sub |
| Prometheus | 9090 | Metrics collection |
| Grafana | 3000 | Dashboards, alerts |
| Loki | 3100 | Log aggregation |
| HashiCorp Vault | 8200 | Secrets management |

---

## 2. User & Access Management

### 2.1 Role-Based Access Control (RBAC)

| Role | Scope | Capabilities |
|---|---|---|
| `superadmin` | Global | Full system access, user CRUD, billing overrides, engine config |
| `admin` | Global | User CRUD, audit review, system health, backup management |
| `operator` | Operational | Monitor dashboards, restart services, view audit logs |
| `analyst` | Read + Research | View all signals, run backtests, export data |
| `trader_elite` | Execution | Full signal access + autonomous execution (Elite tier) |
| `trader_pro` | Limited Execution | Signal access + manual execution (Pro tier) |
| `trader_free` | Read-Only | 5 signals/day, XAUUSD only, no execution (Free tier) |
| `api_client` | API-Only | Programmatic access via API keys, quota-enforced |

### 2.2 User Lifecycle Commands

```bash
# Create a new user
sudo -u pat pat-cli user create --email user@example.com --role trader_pro

# Suspend a user (preserves data, blocks login)
sudo -u pat pat-cli user suspend --email user@example.com

# Reactivate a suspended user
sudo -u pat pat-cli user activate --email user@example.com

# Delete user and all associated data (requires confirmation)
sudo -u pat pat-cli user delete --email user@example.com --confirm

# List all users with filters
sudo -u pat pat-cli user list --role trader_elite --status active
sudo -u pat pat-cli user list --subscription elite --expiring-within 7d

# View user activity log
sudo -u pat pat-cli user activity --email user@example.com --since 30d
```

### 2.3 API Key Management

```bash
# Generate API key for a user
sudo -u pat pat-cli apikey create --user-id 42 --label "Algo Trading Bot" --scopes signals,market

# Revoke an API key
sudo -u pat pat-cli apikey revoke --key-id 15

# List all active API keys
sudo -u pat pat-cli apikey list --status active

# Rotate API keys expiring within 30 days
sudo -u pat pat-cli apikey rotate --expiring-within 30d
```

---

## 3. Audit & Compliance

### 3.1 Audit Event Taxonomy

| Category | Events | Retention |
|---|---|---|
| `auth` | Login, logout, MFA challenge, failed attempts, password resets | 90 days |
| `user_mgmt` | User CRUD, role changes, suspension/reactivation | 365 days |
| `verdict` | Master Engine verdict generation, override application | 365 days |
| `execution` | Trade orders, fills, cancellations, circuit breaker triggers | 365 days |
| `engine` | Engine run start/end, output hash, error states | 90 days |
| `config` | System config changes, weight adjustments, rule modifications | 365 days |
| `billing` | Subscription changes, payments, refunds, tier upgrades | 7 years |
| `admin` | Manual override records, DB schema changes, backup operations | 365 days |

### 3.2 Audit Query Examples

```sql
-- All overrides applied in the last 24 hours
SELECT override_ts, instrument, reason, applied_by, old_verdict, new_verdict
FROM audit_events.master_overrides
WHERE override_ts > NOW() - INTERVAL '24 hours'
ORDER BY override_ts DESC;

-- Failed login attempts by IP (potential brute force)
SELECT ip_address, COUNT(*) AS attempts, MAX(attempt_ts) AS last_attempt
FROM audit_events.auth_failures
WHERE attempt_ts > NOW() - INTERVAL '1 hour'
GROUP BY ip_address
HAVING COUNT(*) > 10
ORDER BY attempts DESC;

-- Engine output changes between versions
SELECT engine_name, old_version, new_version, output_delta
FROM audit_events.engine_version_changes
WHERE change_ts > NOW() - INTERVAL '7 days';
```

### 3.3 Manual Override Protocol

Every manual edit to a production verdict **must** go through the audited override system:

```bash
# Apply an override (generates immutable audit record)
sudo -u pat pat-cli override create \
  --instrument XAUUSD \
  --timeframe H1 \
  --reason "Geopolitical event: unexpected central bank intervention" \
  --action score_cap \
  --cap-value 30 \
  --authorized-by "admin-oncall@predictatrade.com"

# List all active overrides
sudo -u pat pat-cli override list --instrument XAUUSD --active

# Expire an override
sudo -u pat pat-cli override expire --override-id 128
```

---

## 4. Backup & Disaster Recovery

### 4.1 Backup Schedule

| Backup Type | Frequency | Retention | Target |
|---|---|---|---|
| WAL Archiving | Continuous | 30 days | Wasabi S3 (`pat-pg-wal`) |
| Base Backup (pg_basebackup) | Daily 02:00 UTC | 30 days | Wasabi S3 (`pat-pg-base`) |
| Logical Dump (pg_dump) | Weekly Sun 03:00 UTC | 12 weeks | Wasabi S3 (`pat-pg-dump`) |
| MLflow Artifacts | Daily 04:00 UTC | 90 days | Wasabi S3 (`pat-mlflow`) |
| Vault Snapshots | Daily 01:00 UTC | 30 days | Wasabi S3 (`pat-vault`) |
| Config Backup (/etc/pat/) | Daily 01:30 UTC | 90 days | Wasabi S3 (`pat-config`) |

### 4.2 Manual Backup Commands

```bash
# Trigger immediate base backup
sudo -u pat pat-cli backup run --type base

# Trigger immediate logical dump
sudo -u pat pat-cli backup run --type logical --database pat_production

# Verify backup integrity
sudo -u pat pat-cli backup verify --backup-id 2026-05-05-base

# List available backups
sudo -u pat pat-cli backup list --type all --since 30d
```

### 4.3 Point-in-Time Recovery (PITR)

```bash
# Restore to a specific point in time
# Step 1: Restore base backup
sudo -u pat pat-cli restore base --backup-id 2026-05-04-base --target-dir /var/lib/pgsql/16/restore

# Step 2: Configure recovery.conf
cat > /var/lib/pgsql/16/restore/recovery.signal << 'RECOVERY'
restore_command = 'pat-cli wal fetch --source wasabi --wal-file %f --target %p'
recovery_target_time = '2026-05-04 14:30:00 UTC'
RECOVERY

# Step 3: Start PostgreSQL in recovery mode
sudo -u postgres pg_ctl start -D /var/lib/pgsql/16/restore

# Step 4: Promote after recovery completes
sudo -u postgres pg_ctl promote -D /var/lib/pgsql/16/restore
```

### 4.4 Restore Validation Checklist

- [ ] Base backup restored successfully
- [ ] WAL segments applied to target time
- [ ] pg_isready reports accepting connections
- [ ] Row counts match expected (check `engine_outputs`, `master_scores`)
- [ ] Recent master verdicts are reproducible from restored engine outputs
- [ ] API server starts and responds to `/health`
- [ ] Valkey cache warmed (session state restored)

---

## 5. Monitoring & Alerting

### 5.1 Critical Alerts (PagerDuty / On-Call)

| Alert | Condition | Severity |
|---|---|---|
| API 5xx rate | > 5% of requests over 5 min | P1 |
| Master Engine stall | No verdict produced in > 2 cycles | P1 |
| Data feed stale | Ingestion lag > 15 min for primary instrument | P1 |
| DB replication lag | > 100 MB behind, > 5 min | P2 |
| Disk usage | > 85% on any partition | P2 |
| Engine timeout | Any engine > 60s per cycle | P2 |
| Valkey disconnected | > 3 failed health checks | P2 |
| TLS cert expiry | < 14 days remaining | P3 |
| Backup failure | Any scheduled backup fails | P3 |

### 5.2 Prometheus Metrics

```
# Per-service health
pat_service_up{service="pat-master"} 1
pat_service_latency_seconds{service="pat-engine-cv", quantile="0.95"} 2.3

# Master Engine
pat_master_cycle_duration_seconds{status="complete"} 4.2
pat_master_verdicts_total{instrument="XAUUSD", timeframe="H1"} 1440
pat_master_conflicts_detected_total 12
pat_master_overrides_active 0

# Per-Engine
pat_engine_outputs_total{engine="cv", status="success"} 288
pat_engine_error_total{engine="ai", error_type="timeout"} 3

# Execution
pat_execution_orders_total{status="filled"} 47
pat_execution_circuit_breakers_triggered 0
```

### 5.3 Health Check Endpoints

```bash
# Aggregate health
curl -s https://api.predictatrade.com/health | jq .

# Per-service health (requires admin JWT)
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.predictatrade.com/admin/health/services | jq .

# Engine-specific health
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.predictatrade.com/admin/health/engines | jq '.engines[] | {name, status, last_run, latency_ms}'
```

---

## 6. Incident Response

### 6.1 Service Restart Procedures

```bash
# Graceful restart (waits for active cycles to finish)
sudo systemctl reload pat-master

# Force restart (immediate, drops active cycle)
sudo systemctl restart pat-engine-cv

# Restart the full stack in order
sudo systemctl restart pat-data
sleep 5
sudo systemctl restart pat-engine-{cv,ai,di,cw,western,cot,seasonality,macro,tech,exec}
sleep 5
sudo systemctl restart pat-master
sudo systemctl restart pat-api pat-execution pat-frontend
```

### 6.2 Emergency Execution Block

```bash
# Block ALL execution immediately (market emergency)
sudo -u pat pat-cli execution block-all --reason "Emergency: unexpected FOMC statement" \
  --authorized-by "admin-oncall@predictatrade.com"

# Block specific instrument
sudo -u pat pat-cli execution block --instrument XAUUSD --reason "Liquidity vacuum"

# Lift execution block
sudo -u pat pat-cli execution unblock --block-id 42 \
  --authorized-by "admin-oncall@predictatrade.com"
```

### 6.3 Common Issues

| Symptom | Likely Cause | Action |
|---|---|---|
| Master Engine producing no verdicts | Data feed stale | Check `pat-data` logs, verify OHLCV ingestion |
| All engines returning errors | Valkey unreachable | `systemctl restart valkey`, check memory |
| Increasing engine latency | DB connection pool exhausted | Check PG connections, increase pool size |
| Verdict Terminal blank | API down or NGINX misconfigured | Check `pat-api` status, NGINX error log |
| Executions failing | Bridge disconnected | Restart `pat-execution`, verify MT5 ZMQ socket |
| Disk space critical | WAL accumulation or log growth | Run `pg_archivecleanup`, rotate logs |

---

## 7. Configuration Management

### 7.1 Key Configuration Files

| File | Purpose | Managed By |
|---|---|---|
| `/etc/pat/master.yaml` | Master Engine weights, thresholds, rules | GitOps (config repo) |
| `/etc/pat/engines/cv.yaml` | CV Engine agent config, fusion weights | GitOps |
| `/etc/pat/database.yaml` | DB connection pools, read replicas | GitOps |
| `/etc/pat/secrets.env` | Vault token, S3 creds, API keys | Vault agent |
| `/etc/nginx/conf.d/pat.conf` | TLS, rate limits, upstream blocks | GitOps |
| `/etc/prometheus/rules/pat.yml` | Alerting rules, thresholds | GitOps |

### 7.2 Configuration Validation

```bash
# Validate all config files before applying
sudo -u pat pat-cli config validate --all

# Dry-run a master engine weight change
sudo -u pat pat-cli config dry-run \
  --component master \
  --change "engine_weights.cv=0.20" \
  --against-snapshot 2026-05-04T12:00:00Z

# Roll back to a known-good config
sudo -u pat pat-cli config rollback --version v2.0.3
```

---

## 8. System Hardening Checklist

- [ ] SELinux enforcing mode with custom `pat_t` domain
- [ ] firewalld: only 80/443 open to public; all engine ports internal-only
- [ ] PostgreSQL: `pg_hba.conf` restricted to localhost + internal CIDR
- [ ] Valkey: `requirepass` set, bound to 127.0.0.1
- [ ] Vault: auto-unseal via transit engine, TLS everywhere
- [ ] NGINX: TLS 1.3 only, HSTS preload, CSP headers
- [ ] SSH: key-only auth, non-standard port, fail2ban active
- [ ] All services run as unprivileged `pat` user, not root
- [ ] Kernel hardening: `kernel.kptr_restrict=2`, `kernel.dmesg_restrict=1`
- [ ] Auditd rules for `/etc/pat/`, `/var/lib/pgsql/`
- [ ] Automatic security updates: `dnf-automatic` for critical CVEs
- [ ] MFA enforced for all `superadmin` and `admin` roles

---

## 9. Maintenance Windows

| Activity | Recommended Window | Max Duration |
|---|---|---|
| Database minor version upgrade | Saturday 07:00–09:00 UTC | 30 min |
| PG major version upgrade | Scheduled, announced 7d ahead | 2 hours |
| Engine weight recalibration | Any time (hot reload) | 0 downtime |
| OS kernel update + reboot | Sunday 06:00–08:00 UTC | 15 min |
| Valkey cache flush + warm | Any time | 5 min (degraded) |
| Schema migration (Alembic) | Thursday 08:00–09:00 UTC | 15 min |
| Full stack restart | Sunday 07:00–08:00 UTC | 5 min |

---

## 10. Quick Reference

```bash
# Health check
curl -s https://api.predictatrade.com/health

# View running services
systemctl status pat-{api,master,data,engine-*,execution,frontend}

# Tail all logs
journalctl -u 'pat-*' -f --since '5 min ago'

# Check database connections
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity WHERE datname='pat_production';"

# Check disk
df -h /var/lib/pgsql /var/log/pat /opt/pat

# Last 10 master verdicts
sudo -u pat pat-cli verdict list --instrument XAUUSD --limit 10

# Active circuit breakers
sudo -u pat pat-cli execution breakers --active

# Pending configuration changes
sudo -u pat pat-cli config diff --staged
```
