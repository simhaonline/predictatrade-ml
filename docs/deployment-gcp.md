# Predict-A-Trade vNext — Deployment: GCP

> **Target:** Google Cloud Platform (Compute Engine, Cloud SQL, Cloud Storage)
> **OS:** Alma Linux 10 | **No Docker/Kubernetes dependency**

---

## 1. Infrastructure Architecture (GCP)

```
                              Google Cloud
  ┌──────────────────────────────────────────────────────────────┐
  │                                                              │
  │  Cloud CDN ─── Global HTTPS LB ─── Cloud Armor               │
  │                       │                                      │
  │              ┌────────┴────────┐                             │
  │              │                 │                             │
  │  ┌───────────┴──┐   ┌─────────┴──────────┐                   │
  │  │ MIG: frontend│   │ MIG: api           │                   │
  │  │ (Next.js)    │   │ MIG: master        │                   │
  │  └──────────────┘   │ MIG: engine-*      │                   │
  │                     │ MIG: execution     │                   │
  │                     └────────┬───────────┘                   │
  │                              │                                │
  │             ┌────────────────┼────────────────┐              │
  │             │                │                │              │
  │  ┌──────────┴───┐  ┌────────┴────────┐  ┌───┴───────────┐  │
  │  │ Cloud SQL    │  │ Memorystore     │  │ Cloud Storage │  │
  │  │ PostgreSQL   │  │ (Valkey compat) │  │ (Backup)      │  │
  │  │ +TimescaleDB │  └─────────────────┘  └───────────────┘  │
  │  └──────────────┘                                            │
  │                                                              │
  │  Secret Manager ─── Cloud Monitoring ─── IAM ─── SCC        │
  └──────────────────────────────────────────────────────────────┘
```

---

## 2. Prerequisites

### 2.1 GCloud CLI Setup

```bash
gcloud auth login
gcloud config set project predictatrade-prod
gcloud config set compute/region us-central1
gcloud config set compute/zone us-central1-a

# Enable required APIs
gcloud services enable \
  compute.googleapis.com \
  sqladmin.googleapis.com \
  memorystore.googleapis.com \
  secretmanager.googleapis.com \
  monitoring.googleapis.com \
  cloudresourcemanager.googleapis.com \
  servicenetworking.googleapis.com

# Verify
gcloud projects describe predictatrade-prod
```

### 2.2 Service Accounts

```bash
# Create SA for Compute Engine instances
gcloud iam service-accounts create pat-compute-sa \
  --display-name "Predict-A-Trade Compute Engine SA"

# Grant permissions
gcloud projects add-iam-policy-binding predictatrade-prod \
  --member "serviceAccount:pat-compute-sa@predictatrade-prod.iam.gserviceaccount.com" \
  --role "roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding predictatrade-prod \
  --member "serviceAccount:pat-compute-sa@predictatrade-prod.iam.gserviceaccount.com" \
  --role "roles/monitoring.metricWriter"

gcloud projects add-iam-policy-binding predictatrade-prod \
  --member "serviceAccount:pat-compute-sa@predictatrade-prod.iam.gserviceaccount.com" \
  --role "roles/logging.logWriter"
```

---

## 3. Compute: Compute Engine VMs

### 3.1 VM Specifications

| Service | Machine Type | vCPU | RAM | Boot Disk | Count |
|---|---|---|---|---|---|
| pat-api | c3-standard-4 | 4 | 16 GB | 50 GB pd-ssd | 2 (MIG) |
| pat-master | c3-standard-8 | 8 | 32 GB | 50 GB pd-ssd | 1 |
| pat-engine-cv | g2-standard-4 (L4 GPU) | 4 | 16 GB | 100 GB pd-ssd | 1 |
| pat-engine-ai | g2-standard-8 (L4 GPU) | 8 | 32 GB | 200 GB pd-ssd | 1 |
| pat-engine-di | c3-standard-2 | 2 | 8 GB | 50 GB pd-ssd | 1 |
| pat-engine-cw | c3-standard-2 | 2 | 8 GB | 50 GB pd-ssd | 1 |
| pat-engine-western | c3-standard-2 | 2 | 8 GB | 50 GB pd-ssd | 1 |
| pat-engine-cot | c3-standard-2 | 2 | 8 GB | 50 GB pd-ssd | 1 |
| pat-engine-seasonality | c3-standard-2 | 2 | 8 GB | 50 GB pd-ssd | 1 |
| pat-engine-macro | c3-standard-2 | 2 | 8 GB | 50 GB pd-ssd | 1 |
| pat-engine-tech | c3-standard-2 | 2 | 8 GB | 50 GB pd-ssd | 1 |
| pat-engine-exec | c3-standard-2 | 2 | 8 GB | 50 GB pd-ssd | 1 |
| pat-execution | c3-standard-4 | 4 | 16 GB | 50 GB pd-ssd | 1 |
| pat-frontend | c3-standard-4 | 4 | 16 GB | 50 GB pd-ssd | 2 (MIG) |
| pat-monitoring | c3-standard-4 | 4 | 16 GB | 200 GB pd-ssd | 1 |

### 3.2 VM Creation

```bash
# Master Engine
gcloud compute instances create pat-master-prod \
  --zone us-central1-a \
  --machine-type c3-standard-8 \
  --image-family alma-linux-10 \
  --image-project alma-linux-cloud \
  --boot-disk-size 50GB \
  --boot-disk-type pd-ssd \
  --service-account pat-compute-sa@predictatrade-prod.iam.gserviceaccount.com \
  --scopes cloud-platform \
  --network-interface network=default,subnet=internal-subnet,no-address \
  --metadata startup-script='#!/bin/bash
curl -sL https://releases.predictatrade.com/v2.0/gcp/install.sh | bash -s -- --role master --env production'

# Engine: CV (GPU)
gcloud compute instances create pat-engine-cv-prod \
  --zone us-central1-a \
  --machine-type g2-standard-4 \
  --accelerator type=nvidia-l4,count=1 \
  --maintenance-policy TERMINATE \
  --image-family alma-linux-10 \
  --image-project alma-linux-cloud \
  --boot-disk-size 100GB \
  --boot-disk-type pd-ssd \
  --service-account pat-compute-sa@predictatrade-prod.iam.gserviceaccount.com \
  --scopes cloud-platform \
  --network-interface network=default,subnet=internal-subnet,no-address
```

### 3.3 Startup Script (for all VMs)

```bash
#!/bin/bash
# GCP startup script: Predict-A-Trade v2.0

set -euo pipefail

ROLE=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/role" -H "Metadata-Flavor: Google")
ENV=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/env" -H "Metadata-Flavor: Google")

echo "Bootstrapping Predict-A-Trade ${ROLE} in ${ENV}..."

# Base packages
dnf update -y
dnf install -y python3.12 postgresql16 valkey nginx \
  firewalld selinux-policy-targeted google-cloud-ops-agent

# Mount additional disk (GPU instances)
if [[ "$ROLE" == "ai" || "$ROLE" == "cv" ]]; then
  mkdir -p /opt/pat-ml/data
  mount /dev/sdb /opt/pat-ml/data || true
fi

# Install PAT binaries
curl -sL "https://releases.predictatrade.com/v2.0/gcp/pat-${ROLE}.tar.gz" | tar xz -C /opt/pat

# Fetch secrets from Secret Manager
for secret in DB_PASSWORD VAULT_TOKEN API_JWT_SECRET; do
  gcloud secrets versions access latest --secret="pat-${ENV}-${secret,,}" > "/etc/pat/secrets/${secret,,}"
done

# Start service
systemctl enable --now "pat-${ROLE}" nginx firewalld
```

---

## 4. Database: Cloud SQL for PostgreSQL

### 4.1 Cloud SQL Instance Creation

```bash
gcloud sql instances create pat-prod-pg \
  --database-version POSTGRES_16 \
  --tier db-custom-8-32768 \
  --region us-central1 \
  --storage-type SSD \
  --storage-size 1000 \
  --storage-auto-increase \
  --backup-start-time 02:00 \
  --maintenance-window-day SUN \
  --maintenance-window-hour 07:00 \
  --availability-type REGIONAL \
  --network default \
  --no-assign-ip \
  --insights-config-query-insights-enabled \
  --insights-config-query-plans-per-minute 10 \
  --insights-config-record-application-tags \
  --insights-config-record-client-address

# Database user
gcloud sql users create pat_app --instance pat-prod-pg --password "$(gcloud secrets versions access latest --secret pat-prod-db-password)"

# Database
gcloud sql databases create pat_production --instance pat-prod-pg
```

### 4.2 TimescaleDB Extension on Cloud SQL

```sql
-- Cloud SQL does not include TimescaleDB by default.
-- For full TimescaleDB support on GCP:
-- Option A: Run PostgreSQL on Compute Engine with TimescaleDB installed
-- Option B: Use AlloyDB which supports TimescaleDB-compatible hypertables via extensions
-- Option C: Use Cloud SQL and implement app-level partitioning

-- If Option A (Compute Engine PG):
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
```

> **Recommendation:** For GCP deployments requiring TimescaleDB, run PostgreSQL directly on
> a Compute Engine VM rather than Cloud SQL. Use a c3-standard-8 with 1 TB pd-ssd for the
> database tier. Cloud SQL is viable if TimescaleDB hypertables are not required, but the
> project's performance requirements (M1 bars for 10+ years) demand hypertable partitioning.

### 4.3 Compute Engine PostgreSQL Alternative

```bash
# Dedicated DB VM
gcloud compute instances create pat-db-prod \
  --zone us-central1-a \
  --machine-type c3-standard-8 \
  --boot-disk-size 50GB \
  --boot-disk-type pd-ssd \
  --create-disk name=pat-pg-data,size=2000GB,type=pd-ssd \
  --service-account pat-compute-sa@predictatrade-prod.iam.gserviceaccount.com \
  --scopes cloud-platform \
  --network-interface network=default,subnet=internal-subnet,no-address
```

---

## 5. Cache: Memorystore for Valkey

```bash
gcloud memorystore instances create pat-valkey-prod \
  --location us-central1-a \
  --tier STANDARD_HA \
  --node-type SHARED_CORE_NANO \
  --replica-count 2 \
  --network default
```

---

## 6. Networking: HTTPS Load Balancer

### 6.1 Instance Groups

```bash
# Create MIG for API
gcloud compute instance-groups managed create pat-api-mig \
  --zone us-central1-a \
  --template pat-api-template \
  --size 2

# Named port
gcloud compute instance-groups managed set-named-ports pat-api-mig \
  --zone us-central1-a \
  --named-ports http:8000

# Auto-healing
gcloud compute instance-groups managed set-auto-healing pat-api-mig \
  --zone us-central1-a \
  --health-check pat-api-healthcheck \
  --initial-delay 300
```

### 6.2 Load Balancer Setup

```bash
# Backend service
gcloud compute backend-services create pat-api-backend \
  --protocol HTTP \
  --health-checks pat-api-healthcheck \
  --global

# Add MIG to backend
gcloud compute backend-services add-backend pat-api-backend \
  --instance-group pat-api-mig \
  --instance-group-zone us-central1-a \
  --global

# URL map
gcloud compute url-maps create pat-url-map \
  --default-service pat-frontend-backend

gcloud compute url-maps add-path-matcher pat-url-map \
  --path-matcher-name api-paths \
  --path-rules "/api/*=pat-api-backend,/v2/*=pat-api-backend" \
  --default-service pat-frontend-backend

# HTTPS proxy
gcloud compute target-https-proxies create pat-https-proxy \
  --url-map pat-url-map \
  --ssl-certificates pat-tls-cert

# Forwarding rule
gcloud compute forwarding-rules create pat-https-forward \
  --global \
  --target-https-proxy pat-https-proxy \
  --ports 443
```

---

## 7. Observability: Cloud Monitoring

### 7.1 Ops Agent Configuration

```yaml
# /etc/google-cloud-ops-agent/config.yaml
logging:
  receivers:
    pat-logs:
      type: files
      include_paths:
        - /var/log/pat/api.log
        - /var/log/pat/master.log
        - /var/log/pat/engines/*.log
  service:
    pipelines:
      pat-pipeline:
        receivers: [pat-logs]

metrics:
  receivers:
    host_metrics:
      type: hostmetrics
  service:
    pipelines:
      host_pipeline:
        receivers: [host_metrics]
```

### 7.2 Alerting Policies

```bash
# Master Engine stall alert
gcloud monitoring policies create \
  --display-name "PAT - Master Engine Cycle Stall" \
  --condition-filter 'metric.type="custom.googleapis.com/pat/master/cycle_duration_seconds"
    resource.type="gce_instance"
    metric.labels.status="ok"' \
  --condition-threshold-value 0 \
  --condition-threshold-duration 600s \
  --condition-absent-duration 300s \
  --notification-channels "$PAGERDUTY_CHANNEL"

# API 5xx alert
gcloud monitoring policies create \
  --display-name "PAT - API 5xx High" \
  --condition-filter 'metric.type="loadbalancing.googleapis.com/https/backend_request_count"
    metric.labels.response_code_class="500"
    resource.type="https_lb_rule"' \
  --condition-threshold-value 10 \
  --condition-threshold-duration 300s \
  --aggregation-per-series-aligner ALIGN_RATE \
  --notification-channels "$PAGERDUTY_CHANNEL"
```

---

## 8. Secret Manager

```bash
# Create secrets
gcloud secrets create pat-prod-db-password --replication-policy automatic
gcloud secrets create pat-prod-vault-token --replication-policy automatic
gcloud secrets create pat-prod-api-jwt-secret --replication-policy automatic
gcloud secrets create pat-prod-wasabi-access-key --replication-policy automatic
gcloud secrets create pat-prod-wasabi-secret-key --replication-policy automatic
gcloud secrets create pat-prod-glm4-api-key --replication-policy automatic
gcloud secrets create pat-prod-stripe-webhook-secret --replication-policy automatic

# Add version values
echo -n "super-secret-db-password" | gcloud secrets versions add pat-prod-db-password --data-file=-
```

---

## 9. Deployment Script (Full Stack)

```bash
#!/bin/bash
# deploy-gcp.sh — Full Predict-A-Trade GCP deployment
set -euo pipefail

ENV="${1:-production}"
REGION="${2:-us-central1}"
PROJECT="predictatrade-$ENV"

echo "=== Predict-A-Trade v2.0 GCP Deployment ==="
echo "Environment: $ENV | Region: $REGION | Project: $PROJECT"

gcloud config set project "$PROJECT"

# 1. Validate
echo "[1/7] Validating..."
gcloud projects describe "$PROJECT" > /dev/null

# 2. DB (Compute Engine PostgreSQL for TimescaleDB support)
echo "[2/7] Launching database VM..."
./scripts/gcp-create-db-vm.sh "$ENV" "$REGION"

# 3. Cache
echo "[3/7] Ensuring Memorystore..."
# Optional: run Valkey on monitoring VM for cost savings

# 4. Engines
echo "[4/7] Launching engine VMs..."
for engine in cv ai di cw western cot seasonality macro tech exec; do
  ./scripts/gcp-create-engine-vm.sh "$engine" "$ENV" "$REGION" &
done
wait

# 5. Master + API + Frontend
echo "[5/7] Launching core services..."
./scripts/gcp-create-engine-vm.sh master "$ENV" "$REGION"
./scripts/gcp-create-mig.sh api "$ENV" "$REGION"
./scripts/gcp-create-mig.sh frontend "$ENV" "$REGION"

# 6. Load Balancer
echo "[6/7] Configuring HTTPS load balancer..."
./scripts/gcp-configure-lb.sh "$ENV"

# 7. Smoke tests
echo "[7/7] Running smoke tests..."
sleep 30
curl -sf "https://api.$ENV.predictatrade.com/health" && echo "✓ API healthy"
curl -sf "https://$ENV.predictatrade.com" && echo "✓ Frontend healthy"

echo "=== Deployment Complete ==="
```

---

## 10. Estimated Monthly Cost

| Resource | Spec | Monthly Estimate |
|---|---|---|
| Compute Engine (15 VMs) | c3-standard-2 to g2-standard-8 | $5,800 |
| GPU (L4 × 2) | g2-standard VMs | $1,200 |
| Cloud Storage | 5 TB | $110 |
| Persistent Disk (SSD) | 3 TB total | $510 |
| HTTPS LB + egress | ~2 TB/month | $270 |
| Monitoring + Logging | 50 GB logs/month | $180 |
| CUD (1-year commit) | –30% across Compute | –$2,100 |
| **TOTAL** | | **~$5,970/mo** |

> Costs assume 1-year committed use discounts on Compute Engine. Use preemptible VMs
> for non-critical engine instances (Seasonality, Chinese Wisdom) for further savings.
