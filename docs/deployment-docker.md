# Docker Compose Deployment Guide

## Overview

This guide covers containerized deployment of the Predict-A-Trade v2.0 platform using Docker Compose. Docker Compose is the recommended approach for local development, CI/CD testing, and small-scale staging environments. For production deployments, refer to the Kubernetes or self-hosted guides.

The platform consists of 10 microservices, each packaged as a standalone Docker image, orchestrated via a single `docker-compose.yml` file with supporting infrastructure containers (PostgreSQL+TimescaleDB, Valkey, MLflow, NGINX, Prometheus, Grafana, Loki).

## Architecture in Containers

Each `pat-*` service runs in its own container with defined resource limits, healthchecks, and restart policies. Inter-service communication happens over a dedicated Docker bridge network. External traffic enters through an NGINX reverse proxy container that handles TLS termination and routing.

```
[NGINX:443] --> [pat-frontend:3000]
             --> [pat-api:8001]
                  --> [pat-master:8002]
                       --> [pat-engine-cv:8010]
                       --> [pat-engine-ai:8011]
                       --> [pat-engine-di:8012]
                       --> [pat-engine-cw:8013]
                       --> [pat-engine-western:8014]
                       --> [pat-engine-cot:8015]
                       --> [pat-engine-seasonality:8016]
                       --> [pat-engine-macro:8017]
                       --> [pat-engine-tech:8018]
                       --> [pat-engine-exec:8019]
                  --> [pat-execution:8020]
             --> [pat-data:8000]
```

## docker-compose.yml Structure

### Version and Networks

```yaml
version: "3.9"
networks:
  pat-internal:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
  pat-monitoring:
    driver: bridge
```

### Infrastructure Services

**PostgreSQL 16 + TimescaleDB:**

```yaml
  pat-postgres:
    image: timescale/timescaledb:2.16.1-pg16
    container_name: pat-postgres
    environment:
      POSTGRES_DB: predictatrade
      POSTGRES_USER: ${PG_USER:-pat_user}
      POSTGRES_PASSWORD: ${PG_PASSWORD}
      POSTGRES_INITDB_ARGS: "--data-checksums"
    volumes:
      - pg_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    networks:
      - pat-internal
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U pat_user -d predictatrade"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          cpus: "4"
          memory: 8G
        reservations:
          cpus: "2"
          memory: 4G
    restart: unless-stopped
```

**Valkey (Redis-compatible cache):**

```yaml
  pat-valkey:
    image: valkey/valkey:8.0-alpine
    container_name: pat-valkey
    command: valkey-server --save 60 1 --loglevel warning --maxmemory 2gb --maxmemory-policy allkeys-lru
    volumes:
      - valkey_data:/data
    networks:
      - pat-internal
    healthcheck:
      test: ["CMD", "valkey-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    deploy:
      resources:
        limits:
          cpus: "2"
          memory: 4G
    restart: unless-stopped
```

**MLflow Tracking Server:**

```yaml
  pat-mlflow:
    image: ghcr.io/mlflow/mlflow:v2.17.0
    container_name: pat-mlflow
    command: mlflow server --host 0.0.0.0 --port 5555 --backend-store-uri postgresql://${PG_USER}:${PG_PASSWORD}@pat-postgres:5432/mlflow --default-artifact-root s3://predictatrade-mlflow
    ports:
      - "5555:5555"
    networks:
      - pat-internal
    environment:
      AWS_ACCESS_KEY_ID: ${WASABI_ACCESS_KEY}
      AWS_SECRET_ACCESS_KEY: ${WASABI_SECRET_KEY}
      MLFLOW_S3_ENDPOINT_URL: ${WASABI_ENDPOINT}
    depends_on:
      pat-postgres:
        condition: service_healthy
    restart: unless-stopped
```

### Application Services

Each engine service follows this template pattern:

```yaml
  pat-engine-cv:
    image: ${REGISTRY:-predictatrade}/pat-engine-cv:${TAG:-latest}
    container_name: pat-engine-cv
    environment:
      MASTER_ENGINE_URL: http://pat-master:8002
      PG_DSN: postgresql+asyncpg://${PG_USER}:${PG_PASSWORD}@pat-postgres:5432/predictatrade
      VALKEY_URL: valkey://pat-valkey:6379
      ENGINE_NAME: cv
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
      VAULT_ADDR: ${VAULT_ADDR:-http://pat-vault:8200}
    volumes:
      - engine_cv_models:/app/models
      - ./config/engines/cv.yaml:/app/config.yaml:ro
    networks:
      - pat-internal
    depends_on:
      pat-postgres:
        condition: service_healthy
      pat-valkey:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8010/health"]
      interval: 15s
      timeout: 5s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: "4"
          memory: 8G
        reservations:
          cpus: "2"
          memory: 4G
    restart: unless-stopped
```

Apply this pattern for all 10 engine families: `pat-engine-ai` (8011), `pat-engine-di` (8012), `pat-engine-cw` (8013), `pat-engine-western` (8014), `pat-engine-cot` (8015), `pat-engine-seasonality` (8016), `pat-engine-macro` (8017), `pat-engine-tech` (8018), `pat-engine-exec` (8019).

**Core Orchestration Services:**

- `pat-data` (port 8000): Market data ingestion pipeline. Requires higher I/O priority and access to market data feeds.
- `pat-master` (port 8002): Master Engine -- the sole verdict authority. Coordinates all engines, computes 15-dimension scores, produces final trading verdicts.
- `pat-api` (port 8001): Public REST + WebSocket API gateway. Rate-limited, authenticated via JWT and API keys.
- `pat-execution` (port 8020): Trade execution service. Requires broker API credentials from Vault.
- `pat-frontend` (port 3000): Next.js 15 application server. Serves the React-based dashboard and admin panels.

### Proxy and Monitoring

```yaml
  pat-nginx:
    image: nginx:1.27-alpine
    container_name: pat-nginx
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - certbot_data:/etc/letsencrypt
    ports:
      - "80:80"
      - "443:443"
    networks:
      - pat-internal
    depends_on:
      - pat-frontend
      - pat-api
    restart: unless-stopped

  pat-prometheus:
    image: prom/prometheus:v2.54.0
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    networks:
      - pat-monitoring
    restart: unless-stopped

  pat-grafana:
    image: grafana/grafana:11.3.0
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
    ports:
      - "3001:3000"
    networks:
      - pat-monitoring
    restart: unless-stopped

  pat-loki:
    image: grafana/loki:3.2.0
    volumes:
      - ./loki/loki-config.yaml:/etc/loki/config.yaml:ro
      - loki_data:/loki
    networks:
      - pat-monitoring
    restart: unless-stopped
```

## Named Volumes

```yaml
volumes:
  pg_data:
    driver: local
    driver_opts:
      type: none
      device: ${PG_VOLUME_PATH:-/data/pg}
      o: bind
  valkey_data:
  engine_cv_models:
  engine_ai_models:
  engine_western_models:
  prometheus_data:
  grafana_data:
  loki_data:
  certbot_data:
```

## Environment Variables

Create a `.env` file at the project root with these required variables:

```bash
# Database
PG_USER=pat_user
PG_PASSWORD=<generate-strong-password>
PG_VOLUME_PATH=/data/postgres

# Wasabi S3 (MLflow artifacts & backups)
WASABI_ACCESS_KEY=<your-key>
WASABI_SECRET_KEY=<your-secret>
WASABI_ENDPOINT=https://s3.wasabisys.com
WASABI_BUCKET=predictatrade-backups

# Vault
VAULT_ADDR=http://pat-vault:8200
VAULT_TOKEN=<root-or-approle-token>

# Grafana
GRAFANA_PASSWORD=<admin-password>

# Image Registry
REGISTRY=ghcr.io/predictatrade
TAG=v2.0.0

# Log Level
LOG_LEVEL=INFO

# Swiss Ephemeris Path
SWISS_EPHEMERIS_PATH=/app/ephemeris
```

## Resource Limits Reference

| Service      | CPU Limit | Memory Limit | CPU Reservation | Memory Reservation |
|-------------|-----------|-------------|-----------------|--------------------|
| pat-postgres  | 4 cores   | 8 GB        | 2 cores         | 4 GB              |
| pat-valkey    | 2 cores   | 4 GB        | 1 core          | 2 GB              |
| pat-master    | 4 cores   | 8 GB        | 2 cores         | 4 GB              |
| pat-api       | 2 cores   | 4 GB        | 1 core          | 2 GB              |
| pat-data      | 4 cores   | 8 GB        | 2 cores         | 4 GB              |
| pat-frontend  | 2 cores   | 2 GB        | 1 core          | 1 GB              |
| Each engine   | 4 cores   | 8 GB        | 2 cores         | 4 GB              |
| pat-nginx     | 1 core    | 512 MB      | 0.5 core        | 256 MB            |
| Monitoring    | 1 core    | 2 GB        | 0.5 core        | 1 GB              |

## Quick-Start Commands

```bash
# Clone and setup
git clone https://github.com/predictatrade/platform.git
cd platform

# Configure environment
cp .env.example .env
# Edit .env with your credentials
vim .env

# Pull all images
docker compose pull

# Start all services (detached)
docker compose up -d

# Start specific services
docker compose up -d pat-postgres pat-valkey pat-master

# View logs
docker compose logs -f pat-master

# Check health status
docker compose ps

# Scale engines (if needed for testing)
docker compose up -d --scale pat-engine-cv=2

# Stop all
docker compose down

# Full teardown including volumes
docker compose down -v
```

## Healthcheck Verification

After startup, verify all services are healthy:

```bash
# Check all containers
docker compose ps --format "table {{.Name}}\t{{.Status}}"

# Master engine health
curl http://localhost:8002/health

# API health
curl http://localhost:8001/health

# Full system status
curl http://localhost:8001/v2/system/status
```

## Development Mode

For local development with hot-reload:

```yaml
  pat-frontend:
    build:
      context: ./pat-frontend
      target: development
    volumes:
      - ./pat-frontend:/app
      - /app/node_modules
    command: npm run dev
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8001
```

Use `docker compose -f docker-compose.yml -f docker-compose.dev.yml up` to overlay development configurations without modifying the base compose file.

## CI/CD Integration

For CI pipelines, add a `docker-compose.ci.yml` override that:
- Removes port bindings to avoid conflicts with parallel builds
- Sets `restart: "no"` to let the CI agent control lifecycle
- Adds test container services that exit after test completion
- Uses `docker compose run --rm` for one-off test execution
