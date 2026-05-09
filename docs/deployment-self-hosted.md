# Self-Hosted Deployment Guide (systemd)

## Overview

This is the primary deployment model for Predict-A-Trade v2.0. The self-hosted approach uses bare-metal servers or VPS instances with systemd service units managing all platform processes. This configuration delivers full operational control, minimal dependency overhead, and excellent performance without the orchestration complexity of Kubernetes.

The guide covers single-machine (minimum) and multi-machine (distributed) deployments on Alma Linux 10, the platform's target operating system. All commands assume root access or a user with `sudo` privileges.

## Server Requirements

### Single-Node Deployment

| Resource  | Minimum      | Recommended    |
|----------|-------------|----------------|
| CPU      | 16 cores    | 32+ cores      |
| RAM      | 32 GB       | 64+ GB         |
| Storage  | 200 GB SSD  | 500 GB NVMe    |
| OS       | Alma Linux 10 | Alma Linux 10 |
| Network  | 1 Gbps      | 1 Gbps+        |

### Distributed Deployment

Follow the service distribution table in `deployment-overview.md`. Each machine should meet at minimum:
- Database server: 16 cores, 64 GB RAM, 500 GB NVMe RAID
- Engine servers: 32+ cores, 128 GB RAM, 200 GB NVMe
- Load balancer: 4 cores, 8 GB RAM, 80 GB SSD

## Step-by-Step OS Installation and Hardening

### Step 1: Base Install

Provision Alma Linux 10 minimal on each server. If using a VPS provider, select the Alma Linux 10 image. For bare metal, boot from ISO:

```bash
# After first boot, ensure the system is current
dnf update -y
dnf upgrade -y

# Install EPEL and base development tools
dnf install -y epel-release dnf-plugins-core
dnf groupinstall -y "Development Tools"
```

### Step 2: Install Platform Dependencies

```bash
# Python 3.12
dnf install -y python3.12 python3.12-devel python3.12-pip
alternatives --set python3 /usr/bin/python3.12

# PostgreSQL 16 + TimescaleDB
dnf install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-10-x86_64/pgdg-redhat-repo-latest.noarch.rpm

# Disable built-in PostgreSQL module
dnf -qy module disable postgresql

# Install PostgreSQL 16
dnf install -y postgresql16-server postgresql16-contrib

# Add TimescaleDB repository
cat > /etc/yum.repos.d/timescale_timescaledb.repo << 'EOF'
[timescale_timescaledb]
name=TimescaleDB for PostgreSQL
baseurl=https://packagecloud.io/timescale/timescaledb/el/10/x86_64
enabled=1
gpgcheck=0
EOF

dnf install -y timescaledb-2-postgresql-16

# Tune PostgreSQL for TimescaleDB
timescaledb-tune --yes --conf-path /var/lib/pgsql/16/data/postgresql.conf

# Initialize and start PostgreSQL
/usr/pgsql-16/bin/postgresql-16-setup initdb
systemctl enable --now postgresql-16
```

### Step 3: Install Runtime Services

```bash
# Valkey (Redis-compatible)
dnf install -y valkey
systemctl enable --now valkey

# Node.js 22 (for Next.js 15 frontend)
dnf install -y nodejs22 npm

# NGINX
dnf install -y nginx certbot python3-certbot-nginx

# Swiss Ephemeris
mkdir -p /opt/swisseph
# Download ephemeris files from https://www.astro.com/ftp/swisseph/ephe/
# Place all .se1 files in /opt/swisseph/
chown -R pat:pat /opt/swisseph
```

### Step 4: Application User and Directory Structure

```bash
# Create application user
useradd -m -s /bin/bash pat

# Create directory structure
mkdir -p /opt/pat/{services,config,data,models,logs}
mkdir -p /opt/pat/services/{master,api,frontend,data,execution,engines}
mkdir -p /opt/pat/engines/{cv,ai,di,cw,western,cot,seasonality,macro,tech,exec}
chown -R pat:pat /opt/pat

# Clone the platform
su - pat
git clone https://github.com/predictatrade/platform.git /opt/pat/platform
cd /opt/pat/platform
pip3.12 install -e .
```

### Step 5: PostgreSQL Database Setup

```sql
-- Connect as postgres superuser
sudo -u postgres psql

CREATE USER pat_user WITH PASSWORD 'generate-strong-password-here';
CREATE DATABASE predictatrade OWNER pat_user;
CREATE DATABASE mlflow OWNER pat_user;

-- Connect to predictatrade database and enable TimescaleDB
\c predictatrade
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Run migrations (from the application)
-- su - pat -c "cd /opt/pat/platform && python -m pat_data.migrations.up"
```

### Step 6: systemd Unit Files

Create service unit files for every `pat-*` service. Each follows this template:

**/etc/systemd/system/pat-master.service:**

```ini
[Unit]
Description=Predict-A-Trade Master Engine
Documentation=https://docs.predictatrade.com
After=network.target postgresql-16.service valkey.service
Requires=postgresql-16.service valkey.service
Wants=network-online.target

[Service]
Type=simple
User=pat
Group=pat
WorkingDirectory=/opt/pat/platform
EnvironmentFile=/opt/pat/config/master.env
ExecStart=/usr/bin/python3.12 -m uvicorn pat_master.main:app --host 0.0.0.0 --port 8002 --workers 4
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=5
LimitNOFILE=65536
LimitNPROC=32768
MemoryMax=8G
CPUQuota=400%
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/opt/pat/logs /opt/pat/data
ReadOnlyPaths=/opt/pat/config
NoNewPrivileges=yes

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=pat-master

[Install]
WantedBy=multi-user.target
```

**/etc/systemd/system/pat-engine-cv.service:**

```ini
[Unit]
Description=Predict-A-Trade Computer Vision Engine
After=network.target pat-master.service
Requires=pat-master.service

[Service]
Type=simple
User=pat
Group=pat
WorkingDirectory=/opt/pat/platform
EnvironmentFile=/opt/pat/config/engine-cv.env
ExecStart=/usr/bin/python3.12 -m uvicorn pat_engine_cv.main:app --host 0.0.0.0 --port 8010 --workers 2
Restart=always
RestartSec=5
LimitNOFILE=65536
MemoryMax=8G
CPUQuota=400%
PrivateTmp=yes
NoNewPrivileges=yes
StandardOutput=journal
StandardError=journal
SyslogIdentifier=pat-engine-cv

[Install]
WantedBy=multi-user.target
```

Create equivalent unit files for all 10 engine families, plus:
- `/etc/systemd/system/pat-api.service` (port 8001)
- `/etc/systemd/system/pat-data.service` (port 8000)
- `/etc/systemd/system/pat-execution.service` (port 8020)
- `/etc/systemd/system/pat-frontend.service` (port 3000)
- `/etc/systemd/system/pat-mlflow.service` (port 5555)

**pat-frontend.service** (Next.js with Bun):

```ini
[Unit]
Description=Predict-A-Trade Frontend (Next.js 15)
After=network.target pat-api.service

[Service]
Type=simple
User=pat
Group=pat
WorkingDirectory=/opt/pat/frontend
EnvironmentFile=/opt/pat/config/frontend.env
ExecStart=/usr/bin/bun run start
Restart=always
RestartSec=5
MemoryMax=2G
CPUQuota=200%
PrivateTmp=yes
NoNewPrivileges=yes
StandardOutput=journal
StandardError=journal
SyslogIdentifier=pat-frontend

[Install]
WantedBy=multi-user.target
```

### Step 7: NGINIX TLS Configuration

**/etc/nginx/conf.d/predictatrade.conf:**

```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name api.predictatrade.com app.predictatrade.com;
    return 301 https://$host$request_uri;
}

# API Gateway
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.predictatrade.com;

    ssl_certificate /etc/letsencrypt/live/api.predictatrade.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.predictatrade.com/privkey.pem;
    ssl_protocols TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    client_max_body_size 10m;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400s;
    }

    location /health {
        proxy_pass http://127.0.0.1:8001/health;
        access_log off;
    }
}

# Frontend
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name app.predictatrade.com;

    ssl_certificate /etc/letsencrypt/live/app.predictatrade.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.predictatrade.com/privkey.pem;
    ssl_protocols TLSv1.3;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Obtain certificates:

```bash
systemctl stop nginx
certbot certonly --standalone -d api.predictatrade.com
certbot certonly --standalone -d app.predictatrade.com
systemctl start nginx

# Auto-renewal
echo "0 3 * * * certbot renew --quiet --post-hook 'systemctl reload nginx'" | crontab -
```

### Step 8: Firewall and SELinux

```bash
# Firewalld
systemctl enable --now firewalld

# Allow only necessary ports
firewall-cmd --permanent --add-service=ssh
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --reload

# Internal services (if distributed, restrict to internal network)
firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="10.0.0.0/16" port port="5432" protocol="tcp" accept'
firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="10.0.0.0/16" port port="6379" protocol="tcp" accept'
firewall-cmd --reload

# SELinux context for application
semanage fcontext -a -t httpd_sys_content_t "/opt/pat(/.*)?"
semanage fcontext -a -t httpd_log_t "/opt/pat/logs(/.*)?"
restorecon -Rv /opt/pat

# Allow NGINX to proxy to backend ports
setsebool -P httpd_can_network_connect 1
```

### Step 9: Start and Enable All Services

```bash
# Reload systemd to pick up new units
systemctl daemon-reload

# Enable all services to start on boot
systemctl enable pat-master pat-api pat-frontend pat-data pat-execution pat-mlflow
systemctl enable pat-engine-{cv,ai,di,cw,western,cot,seasonality,macro,tech,exec}

# Start all services
systemctl start pat-master pat-api pat-frontend pat-data pat-execution pat-mlflow
systemctl start pat-engine-{cv,ai,di,cw,western,cot,seasonality,macro,tech,exec}

# Verify all services are running
systemctl status 'pat-*'
```

### Step 10: Monitoring Stack

```bash
# Prometheus
dnf install -y prometheus2
# Configure /etc/prometheus/prometheus.yml with scrape targets
systemctl enable --now prometheus

# Grafana
cat > /etc/yum.repos.d/grafana.repo << 'EOF'
[grafana]
name=Grafana
baseurl=https://rpm.grafana.com
enabled=1
gpgcheck=1
gpgkey=https://rpm.grafana.com/gpg.key
EOF
dnf install -y grafana
systemctl enable --now grafana-server

# Loki and Promtail for log aggregation
dnf install -y loki promtail
# Configure /etc/loki/config.yaml and /etc/promtail/config.yaml
systemctl enable --now loki promtail
```

### Step 11: Backup Cron Jobs

Create `/opt/pat/scripts/backup.sh`:

```bash
#!/bin/bash
set -euo pipefail
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR=/opt/pat/backups/$TIMESTAMP
mkdir -p $BACKUP_DIR

# Database backup
pg_dump -U pat_user predictatrade | gzip > $BACKUP_DIR/pg-dump.sql.gz

# WAL archive
pg_receivewal -U pat_user -D $BACKUP_DIR/wal --slot=pat_backup --create-slot

# Model backup
tar -czf $BACKUP_DIR/models.tar.gz /opt/pat/models/

# Upload to Wasabi S3
s3cmd sync $BACKUP_DIR/ s3://predictatrade-backups/daily/$TIMESTAMP/

# Cleanup old backups (keep 90 days)
find /opt/pat/backups -maxdepth 1 -type d -mtime +90 -exec rm -rf {} \;
```

```bash
chmod +x /opt/pat/scripts/backup.sh
# Hourly WAL archiving, daily full dump
echo "0 * * * * pg_receivewal -U pat_user -D /opt/pat/backups/wal_stream --slot=pat_backup" | crontab -
echo "0 2 * * * /opt/pat/scripts/backup.sh" | crontab -
```

## Full Bootstrap Script

For rapid provisioning, combine all steps into a single bootstrap script at `scripts/bootstrap-alma10.sh` in the repository. This script is idempotent -- safe to run on an already-configured server to update configurations.

```bash
#!/bin/bash
# bootstrap-alma10.sh -- Full platform bootstrap for Alma Linux 10
# Usage: curl -sL https://raw.githubusercontent.com/predictatrade/platform/main/scripts/bootstrap-alma10.sh | sudo bash -s -- --role engine

set -euo pipefail
ROLE="${1:-single}"
echo "Bootstrapping Predict-A-Trade v2.0 with role: $ROLE"
# ... (all above steps, conditioned on ROLE)
```

## Verification Checklist

After bootstrapping, verify:

- [ ] All systemd units are `active (running)` via `systemctl status 'pat-*'`
- [ ] PostgreSQL is accepting connections: `psql -U pat_user -h 127.0.0.1 -d predictatrade -c "SELECT 1"`
- [ ] Master Engine health endpoint returns 200: `curl -s http://127.0.0.1:8002/health`
- [ ] API health endpoint returns 200: `curl -s http://127.0.0.1:8001/health`
- [ ] Frontend serves on port 3000: `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000`
- [ ] NGINX is serving and redirecting HTTP to HTTPS
- [ ] TLS certificate is valid and not expired
- [ ] Prometheus is scraping all targets
- [ ] Grafana dashboards are loading
- [ ] Wasabi S3 backup completed successfully

## Troubleshooting

| Symptom                        | Likely Cause            | Fix                                  |
|-------------------------------|------------------------|--------------------------------------|
| `pat-master.service` fails    | PostgreSQL not running  | `systemctl start postgresql-16`       |
| Engine connection refused     | Firewall blocking port  | Check `firewall-cmd --list-all`       |
| NGINX 502 Bad Gateway         | Backend service down    | `systemctl status pat-api`            |
| Permission denied on /opt/pat | Wrong ownership         | `chown -R pat:pat /opt/pat`           |
| SELinux denies proxy          | Boolean not set         | `setsebool -P httpd_can_network_connect 1` |
