# Hetzner Cloud Deployment Guide

## Overview

Hetzner Cloud provides dedicated bare-metal and virtual servers at approximately 60-70% lower cost than equivalent AWS EC2 or GCP Compute Engine instances. This guide covers deploying Predict-A-Trade v2.0 on Hetzner infrastructure using a combination of dedicated servers for core workloads and cloud VMs for auxiliary services.

The recommended architecture uses two to four bare-metal servers for the compute fleet (Master Engine and 10 engine families), one bare-metal server for PostgreSQL+TimescaleDB, and cloud VMs for load balancing and monitoring. This arrangement provides substantial compute resources, predictable performance, and full control over the software stack.

## Why Hetzner

- **Cost:** An AX102 (AMD EPYC 9754, 192 cores, 256 GB RAM) costs approximately EUR 400/month. Equivalent AWS compute would exceed EUR 2,000/month.
- **Performance:** Bare metal eliminates the virtualization tax. No noisy neighbors. Full access to CPU caches, memory bandwidth, and NVMe storage.
- **Network:** 1 Gbps guaranteed bandwidth per server, with burst up to 10 Gbps on newer models.
- **Traffic:** 20-30 TB of included traffic per server, drastically reducing data egress costs compared to cloud providers (where egress can dominate the bill).
- **Location:** Data centers in Nuremberg, Falkenstein, and Helsinki (EU only), making it suitable for GDPR compliance with European hosting.

## Recommended Server Specs

### Option A: All-Cloud VM (Lower Cost, Good for Staging)

| Service       | VM Type   | vCPUs | RAM   | Storage       | Cost/Month |
|--------------|-----------|-------|-------|---------------|------------|
| Core services | CX52 x2   | 16    | 32 GB | 160 GB NVMe   | EUR 80     |
| Database     | CX52      | 8     | 16 GB | 160 GB NVMe   | EUR 40     |
| Load Balancer | CX32     | 4     | 8 GB  | 80 GB NVMe    | EUR 20     |
| **Total**    |           |       |       |               | **EUR 140** |

### Option B: Bare-Metal Production (Recommended)

| Service           | Model       | Cores/Threads | RAM     | Storage           | Cost/Month |
|-------------------|-------------|---------------|---------|--------------------|------------|
| Engine Fleet (x2) | AX102       | 192c/384t    | 256 GB  | 2x3.84 TB NVMe    | EUR 820    |
| Database           | EX130-R     | 64c/128t     | 256 GB  | 2x3.84 TB NVMe    | EUR 280    |
| Load Balancer      | CX42 (x2)   | 8            | 16 GB   | 80 GB NVMe        | EUR 40     |
| Backup Storage     | Storage Box | --           | --      | 10 TB              | EUR 40     |
| **Total**          |             |              |         |                    | **EUR 1,180** |

This EUR 1,180/month configuration replaces an estimated EUR 4,000-5,000/month GCP/GKE deployment.

## Step-by-Step Bootstrap

### Step 1: Provision Servers via hcloud CLI

```bash
# Install hcloud CLI
curl -sL https://github.com/hetznercloud/cli/releases/download/v1.48.0/hcloud-linux-amd64.tar.gz | tar xz
sudo mv hcloud /usr/local/bin/

# Authenticate
hcloud context create predictatrade
# Enter your API token from https://console.hetzner.cloud/

# Create private network
hcloud network create --name pat-network --ip-range 10.0.0.0/16

# Provision engine servers
hcloud server create \
  --name pat-engine-01 \
  --type ax102 \
  --image ubuntu-24.04 \
  --location nbg1 \
  --ssh-key pat-admin \
  --network pat-network \
  --label env=production \
  --label role=engine

hcloud server create \
  --name pat-engine-02 \
  --type ax102 \
  --image ubuntu-24.04 \
  --location fsn1 \
  --ssh-key pat-admin \
  --network pat-network \
  --label env=production \
  --label role=engine

# Provision database server
hcloud server create \
  --name pat-db-01 \
  --type ex130-r \
  --image ubuntu-24.04 \
  --location nbg1 \
  --ssh-key pat-admin \
  --network pat-network \
  --label env=production \
  --label role=database

# Provision load balancer VMs
for i in 01 02; do
  hcloud server create \
    --name pat-lb-$i \
    --type cx42 \
    --image ubuntu-24.04 \
    --location nbg1 \
    --ssh-key pat-admin \
    --network pat-network \
    --label env=production \
    --label role=loadbalancer
done

# Add floating IP for the public-facing entry point
hcloud floating-ip create --type ipv4 --description "PAT Production IP" --home-location nbg1
hcloud floating-ip assign <ip-id> pat-lb-01
```

### Step 2: Configure Alma Linux 10

After provisioning, replace Ubuntu with Alma Linux 10 for consistency with the platform's target OS:

```bash
# SSH into each server and run:
curl -O https://repo.almalinux.org/almalinux/10.0/isos/x86_64/AlmaLinux-10.0-x86_64-minimal.iso
# Mount ISO and perform install via rescue system
# Or alternatively, use Alma Linux 10 with systemd directly via the custom ISO boot option
```

For production, maintain a golden image with Alma Linux 10 pre-installed via the Hetzner custom ISO feature.

### Step 3: Initial Server Hardening

```bash
#!/bin/bash
# Run on each server after provisioning: 00-bootstrap.sh

set -euo pipefail

# System update
dnf update -y
dnf upgrade -y

# Install base packages
dnf install -y python3.12 python3.12-devel git curl wget vim htop \
  nginx firewalld chrony fail2ban policycoreutils-python-utils

# SSH hardening
sed -i 's/^#PermitRootLogin.*/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config
sed -i 's/^#PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd

# Firewall
systemctl enable --now firewalld
firewall-cmd --permanent --add-service=ssh
firewall-cmd --permanent --add-service=https
firewall-cmd --permanent --add-service=http
firewall-cmd --reload

# Chrony (time sync -- critical for trading timestamps)
systemctl enable --now chronyd

# Fail2ban
systemctl enable --now fail2ban

# SELinux enforcing
setenforce 1
sed -i 's/SELINUX=permissive/SELINUX=enforcing/' /etc/selinux/config

# Create application user
useradd -m -s /bin/bash pat
usermod -aG docker pat
```

### Step 4: Deploy Platform Services via systemd

Follow the self-hosted deployment guide (`deployment-self-hosted.md`) for creating systemd unit files for all `pat-*` services. Distribute services across servers:

**pat-engine-01:** pat-master, pat-engine-cv, pat-engine-ai, pat-engine-western, pat-engine-cot
**pat-engine-02:** pat-engine-di, pat-engine-cw, pat-engine-seasonality, pat-engine-macro, pat-engine-tech, pat-engine-exec
**pat-db-01:** pat-data, PostgreSQL 16 + TimescaleDB, Valkey, MLflow
**pat-lb-01/lb-02:** NGINX with TLS termination, Prometheus, Grafana, Loki

### Step 5: Internal Networking

Configure the private network between servers:

```bash
# On each engine server, bring up private interface (assigned by hcloud)
ip addr add 10.0.0.x/16 dev ens10
ip link set ens10 up

# Add to /etc/hosts for service discovery
cat >> /etc/hosts << 'EOF'
10.0.0.10  pat-db-01
10.0.0.11  pat-engine-01
10.0.0.12  pat-engine-02
10.0.0.20  pat-lb-01
10.0.0.21  pat-lb-02
EOF
```

### Step 6: Wasabi S3 Backup Configuration

```bash
# Install s3cmd for Wasabi S3 backup
dnf install -y s3cmd
s3cmd --configure
# Endpoint: s3.wasabisys.com
# Use path-style: Yes
# Region: eu-central-1

# Create backup script
cat > /usr/local/bin/pat-backup.sh << 'BACKUP'
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
pg_dump -U pat_user -h 10.0.0.10 predictatrade | gzip > /tmp/pg-backup-$TIMESTAMP.sql.gz
s3cmd put /tmp/pg-backup-$TIMESTAMP.sql.gz s3://predictatrade-backups/database/
s3cmd sync /opt/pat/models/ s3://predictatrade-backups/models/
rm /tmp/pg-backup-$TIMESTAMP.sql.gz
BACKUP
chmod +x /usr/local/bin/pat-backup.sh

# Cron: daily at 02:00 UTC
echo "0 2 * * * /usr/local/bin/pat-backup.sh" | crontab -
```

## Cost Comparison (Monthly)

| Component           | Hetzner (Production) | AWS Equivalent  | GCP Equivalent  | Savings  |
|--------------------|---------------------|-----------------|-----------------|----------|
| Compute (engines)   | EUR 820             | EUR 2,600       | EUR 2,400       | 68%      |
| Database            | EUR 280             | EUR 900         | EUR 850         | 68%      |
| Network/Ingress     | EUR 40              | EUR 200         | EUR 180         | 79%      |
| Storage             | EUR 40              | EUR 120         | EUR 110         | 65%      |
| Traffic/Egress      | Included (30 TB)    | EUR 300-500     | EUR 250-400     | 100%     |
| **Total**           | **EUR 1,180**       | **EUR 4,220**   | **EUR 3,890**   | **71%**  |

## Trade-offs

| Advantage                          | Disadvantage                              |
|-----------------------------------|-------------------------------------------|
| 60-70% cost reduction             | No managed services (self-manage PG)       |
| Full hardware control             | Limited to EU data centers only            |
| No noisy neighbors                | No multi-region failover out of the box    |
| Predictable billing               | Manual bare-metal provisioning             |
| Excellent compute density          | Longer time-to-scale (hours vs minutes)    |

## When to Choose Hetzner

- You are cost-sensitive and willing to manage infrastructure.
- Your primary user base is in Europe.
- You do not require sub-minute auto-scaling.
- You are comfortable with systemd, firewalld, and SELinux.
- You want deterministic performance for compute-heavy engines (CV, AI).

Hetzner is particularly attractive as the primary deployment target for Predict-A-Trade because the engine fleet requires consistent, high-throughput compute that benefits from bare-metal execution. Combined with Wasabi S3 for backups and Cloudflare for CDN/DDoS protection, the Hetzner deployment achieves enterprise-grade reliability at a fraction of cloud provider costs.
