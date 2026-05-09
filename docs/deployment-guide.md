# Predict-A-Trade v2.0 Deployment Guide

## Table of Contents

1. [Overview](#overview)
2. [System Requirements](#system-requirements)
3. [Deployment Options](#deployment-options)
4. [Self-Hosted Deployment (systemd)](#self-hosted-deployment-systemd)
5. [Docker Compose Deployment](#docker-compose-deployment)
6. [Kubernetes Deployment](#kubernetes-deployment)
7. [Hetzner Cloud Deployment](#hetzner-cloud-deployment)
8. [Single-Node Deployment](#single-node-deployment)
9. [Distributed Deployment](#distributed-deployment)
10. [Configuration Management](#configuration-management)
11. [Monitoring and Logging](#monitoring-and-logging)
12. [Security Considerations](#security-considerations)
13. [Backup and Recovery](#backup-and-recovery)
14. [Troubleshooting](#troubleshooting)

## Overview

Predict-A-Trade v2.0 supports six deployment targets, each optimized for different operational requirements, budgets, and team expertise levels. This guide provides step-by-step instructions for deploying the platform in various environments.

## System Requirements

### Minimum Hardware Requirements

For any production deployment:
- 16 CPU cores (Intel Xeon or AMD EPYC recommended)
- 32 GB RAM
- 200 GB SSD storage (NVMe preferred)
- 1 Gbps network connectivity
- AlmaLinux 10 or Ubuntu 24.04 LTS

### Software Dependencies

- Docker 24.0+
- Docker Compose 2.20+
- Python 3.11+
- Node.js 20+
- PostgreSQL 16 with TimescaleDB 2.15+
- Valkey 7.2+
- HashiCorp Vault 1.15+

## Deployment Options

### 1. Self-Hosted (systemd) - Recommended for Production

Full control with systemd service management. Best for production environments requiring maximum control and stability.

### 2. Docker Compose - Development and Testing

Ideal for local development, CI testing, and small-scale staging environments.

### 3. Kubernetes - Large-Scale Production

Managed Kubernetes for elastic scaling, zero-downtime deployments, and multi-region production.

### 4. Hetzner Cloud - Cost-Optimized Production

Bare-metal at 60-70% cost savings vs AWS/GCP. Ideal for compute-heavy, cost-sensitive production.

### 5. Single-Node - Personal Use

All services on one machine for personal use or evaluation. Not recommended for production.

### 6. Distributed - Multi-Node Production

Services split across multiple machines with network isolation. Production-grade without Kubernetes.

## Self-Hosted Deployment (systemd)

### Prerequisites

1. Fresh installation of AlmaLinux 10 or Ubuntu 24.04 LTS
2. Root or sudo access
3. Internet connectivity for package downloads

### Installation Steps

1. **Update system packages:**
   ```bash
   sudo dnf update -y  # AlmaLinux
   # OR
   sudo apt update && sudo apt upgrade -y  # Ubuntu
   ```

2. **Install required dependencies:**
   ```bash
   # AlmaLinux
   sudo dnf install -y docker docker-compose git python3 python3-pip
   
   # Ubuntu
   sudo apt install -y docker.io docker-compose git python3 python3-pip
   ```

3. **Clone the repository:**
   ```bash
   git clone https://github.com/predictatrade/predictatrade.git /opt/predictatrade
   cd /opt/predictatrade
   ```

4. **Set up systemd services:**
   ```bash
   sudo cp systemd/*.service /etc/systemd/system/
   sudo systemctl daemon-reload
   ```

5. **Configure environment variables:**
   ```bash
   cp config/env/production.yaml config/env/local.yaml
   # Edit config/env/local.yaml with your settings
   ```

6. **Start services:**
   ```bash
   sudo systemctl enable --now pat-data pat-master pat-api pat-frontend pat-execution
   ```

7. **Verify deployment:**
   ```bash
   sudo systemctl status pat-*
   curl http://localhost:8000/health
   ```

## Docker Compose Deployment

### Prerequisites

1. Docker and Docker Compose installed
2. At least 8GB RAM available

### Deployment Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/predictatrade/predictatrade.git
   cd predictatrade
   ```

2. **Configure environment:**
   ```bash
   cp config/env/development.yaml config/env/.env
   # Edit .env with your settings
   ```

3. **Start services:**
   ```bash
   docker-compose up -d
   ```

4. **Monitor logs:**
   ```bash
   docker-compose logs -f
   ```

5. **Access the platform:**
   Open `http://localhost:3000` in your browser

## Kubernetes Deployment

### Prerequisites

1. Kubernetes cluster (GKE/EKS/AKS) with kubectl configured
2. Helm 3.8+
3. At least 3 worker nodes with 16GB RAM each

### Deployment Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/predictatrade/predictatrade.git
   cd predictatrade/k8s
   ```

2. **Configure Helm values:**
   ```bash
   cp values-production.yaml values-local.yaml
   # Edit values-local.yaml with your settings
   ```

3. **Deploy using Helm:**
   ```bash
   helm install predictatrade . -f values-local.yaml
   ```

4. **Monitor deployment:**
   ```bash
   kubectl get pods
   kubectl get services
   ```

5. **Access the platform:**
   ```bash
   kubectl port-forward svc/pat-frontend 3000:3000
   ```

## Hetzner Cloud Deployment

### Prerequisites

1. Hetzner Cloud account
2. hcloud CLI installed and configured
3. SSH key uploaded to Hetzner Cloud

### Deployment Steps

1. **Clone deployment scripts:**
   ```bash
   git clone https://github.com/predictatrade/predictatrade.git
   cd predictatrade/scripts/hetzner
   ```

2. **Configure deployment:**
   ```bash
   cp hetzner-config.example.yaml hetzner-config.yaml
   # Edit hetzner-config.yaml with your settings
   ```

3. **Deploy infrastructure:**
   ```bash
   ./deploy-hetzner.sh
   ```

4. **Monitor deployment:**
   ```bash
   ./check-status.sh
   ```

## Single-Node Deployment

### Prerequisites

1. Single machine with minimum requirements
2. Docker and Docker Compose installed

### Deployment Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/predictatrade/predictatrade.git
   cd predictatrade
   ```

2. **Configure for single node:**
   ```bash
   cp config/env/single-node.yaml config/env/.env
   ```

3. **Start services:**
   ```bash
   docker-compose -f docker-compose.single-node.yml up -d
   ```

## Distributed Deployment

### Prerequisites

1. Multiple machines with network connectivity
2. SSH access to all machines
3. Shared storage (NFS or similar)

### Deployment Steps

1. **Prepare machines:**
   - Machine 1: Load Balancer + Monitoring
   - Machine 2: Database
   - Machine 3: Engine Pool 1
   - Machine 4: Engine Pool 2
   - Machine 5: API/Frontend

2. **Clone repository on all machines:**
   ```bash
   git clone https://github.com/predictatrade/predictatrade.git
   ```

3. **Configure each machine with appropriate services:**
   ```bash
   # On each machine, edit config/env/distributed.yaml
   # Adjust service configurations for distributed deployment
   ```

4. **Start services on each machine:**
   ```bash
   # On Load Balancer machine
   docker-compose -f docker-compose.lb.yml up -d
   
   # On Database machine
   docker-compose -f docker-compose.db.yml up -d
   
   # On Engine Pool machines
   docker-compose -f docker-compose.engines.yml up -d
   
   # On API/Frontend machine
   docker-compose -f docker-compose.api.yml up -d
   ```

## Configuration Management

### Environment Variables

All services use YAML configuration files located in `config/env/`:
- `development.yaml` - Local development settings
- `staging.yaml` - Staging environment settings
- `production.yaml` - Production environment settings

### Secret Management

Use HashiCorp Vault for production deployments:
```bash
# Initialize Vault
vault operator init

# Unseal Vault
vault operator unseal

# Store secrets
vault kv put secret/pat/database username=pat password=secure_password
```

For development, use `.env` files:
```bash
# .env file format
DATABASE_URL=postgresql://pat:secure_password@db:5432/pat
API_SECRET=super_secret_key
JWT_SECRET=jwt_super_secret
```

## Monitoring and Logging

### Prometheus Metrics

All services expose Prometheus metrics at `/metrics` endpoint:
```bash
# Scrape configuration in prometheus.yml
scrape_configs:
  - job_name: 'pat-services'
    static_configs:
      - targets: ['pat-data:8000', 'pat-master:8001', 'pat-api:8002']
```

### Grafana Dashboards

Pre-built dashboards are available in `grafana/dashboards/`:
- `system-overview.json` - System health metrics
- `engine-performance.json` - Engine performance monitoring
- `master-verdicts.json` - Trading verdict analytics
- `trading-activity.json` - Order execution tracking

### Log Aggregation with Loki

Structured logging is enabled by default:
```bash
# Query logs with LogQL
{job="pat-api", level="error"} |~ "database"
```

## Security Considerations

### Network Security

1. **Firewall Rules:**
   ```bash
   # Allow only necessary ports
   sudo firewall-cmd --permanent --add-port=80/tcp
   sudo firewall-cmd --permanent --add-port=443/tcp
   sudo firewall-cmd --permanent --add-port=22/tcp
   sudo firewall-cmd --reload
   ```

2. **Internal Communication:**
   - Use private networks for service-to-service communication
   - Enable mutual TLS for sensitive services

### Authentication and Authorization

1. **JWT Tokens:**
   - Rotate JWT secrets regularly
   - Use strong signing algorithms (RS256)

2. **API Keys:**
   - Implement rate limiting per API key
   - Rotate API keys periodically

### Data Encryption

1. **At Rest:**
   - Enable TDE (Transparent Data Encryption) in PostgreSQL
   - Use encrypted storage volumes

2. **In Transit:**
   - Enforce HTTPS with TLS 1.3
   - Use mutual TLS for service communication

## Backup and Recovery

### Database Backups

1. **Automated Backups:**
   ```bash
   # Daily full backup
   pg_dump -h db -U pat pat_db > /backups/pat_$(date +%Y%m%d).sql
   
   # Hourly WAL archiving
   pg_basebackup -h db -U repuser -D /backups/wal -Fp -X stream
   ```

2. **Restore Process:**
   ```bash
   # Restore from backup
   psql -h db -U pat pat_db < /backups/pat_backup.sql
   ```

### Configuration Backups

1. **Version Control:**
   ```bash
   # Commit configuration changes
   git add config/
   git commit -m "Update production configuration"
   git push origin main
   ```

2. **Offsite Storage:**
   ```bash
   # Sync to cloud storage
   aws s3 sync config/ s3://pat-backups/config/
   ```

## Troubleshooting

### Common Issues

1. **Service Won't Start:**
   ```bash
   # Check service status
   systemctl status pat-api
   
   # Check logs
   journalctl -u pat-api -f
   ```

2. **Database Connection Issues:**
   ```bash
   # Test database connectivity
   psql -h localhost -U pat pat_db
   
   # Check database logs
   journalctl -u postgresql -f
   ```

3. **Performance Problems:**
   ```bash
   # Monitor system resources
   top
   iostat -x 1
   
   # Check service metrics
   curl http://localhost:8000/metrics
   ```

### Health Checks

1. **Platform Health:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Individual Service Health:**
   ```bash
   curl http://localhost:8001/health  # pat-master
   curl http://localhost:8002/health  # pat-api
   ```

### Log Analysis

1. **Error Patterns:**
   ```bash
   # Search for errors in logs
   journalctl -u pat-* | grep ERROR
   
   # Search in Docker logs
   docker-compose logs | grep error
   ```

## Conclusion

This deployment guide covers the essential steps for deploying Predict-A-Trade v2.0 in various environments. Choose the deployment option that best fits your requirements and follow the corresponding steps. Always test your deployment in a staging environment before going to production.

For additional support, refer to the specific deployment guides for each target:
- `deployment-overview.md` - Comparison of all deployment options
- `deployment-gcp.md` - Google Cloud Platform specific instructions
- `deployment-aws.md` - Amazon Web Services specific instructions
- `deployment-hetzner.md` - Hetzner Cloud specific instructions
- `deployment-docker.md` - Docker Compose specific instructions
- `deployment-k8s.md` - Kubernetes specific instructions
- `deployment-self-hosted.md` - Self-hosted specific instructions