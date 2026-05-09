# Kubernetes Deployment Guide

## Overview

This guide describes the Kubernetes deployment architecture for Predict-A-Trade v2.0 on managed Kubernetes services: Google Kubernetes Engine (GKE), Amazon Elastic Kubernetes Service (EKS), and Azure Kubernetes Service (AKS). Kubernetes is the recommended choice for production deployments requiring auto-scaling, zero-downtime rollouts, multi-region failover, and GitOps-based operational workflows.

All manifests are organized in the `k8s/` directory at the repository root and are designed to be environment-agnostic, with per-environment overrides handled via Kustomize overlays.

## Namespace Architecture

```
predictatrade-system    # Core platform services
predictatrade-engines   # Engine fleet (10 engine families)
predictatrade-data      # Data pipeline and storage
predictatrade-monitoring # Prometheus, Grafana, Loki
```

Each namespace enforces ResourceQuotas and NetworkPolicies. The `predictatrade-system` namespace is the single entry point, hosting the NGINX Ingress, API gateway, and Master Engine.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: predictatrade-system
  labels:
    pod-security.kubernetes.io/enforce: restricted
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: system-quota
  namespace: predictatrade-system
spec:
  hard:
    requests.cpu: "16"
    requests.memory: "32Gi"
    limits.cpu: "32"
    limits.memory: "64Gi"
    persistentvolumeclaims: "10"
```

## Deployments per Microservice

Each microservice uses a standard Deployment template with liveness/readiness probes, resource constraints, and pod anti-affinity for fault tolerance.

**Master Engine Deployment:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pat-master
  namespace: predictatrade-system
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: pat-master
  template:
    metadata:
      labels:
        app: pat-master
        version: v2.0.0
    spec:
      serviceAccountName: pat-master-sa
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            - labelSelector:
                matchExpressions:
                  - key: app
                    operator: In
                    values: [pat-master]
              topologyKey: kubernetes.io/hostname
      containers:
        - name: pat-master
          image: ghcr.io/predictatrade/pat-master:v2.0.0
          ports:
            - containerPort: 8002
          envFrom:
            - configMapRef:
                name: pat-master-config
            - secretRef:
                name: pat-master-secrets
          resources:
            requests:
              cpu: "2"
              memory: "4Gi"
            limits:
              cpu: "4"
              memory: "8Gi"
          livenessProbe:
            httpGet:
              path: /health
              port: 8002
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /ready
              port: 8002
            initialDelaySeconds: 10
            periodSeconds: 5
```

Each engine family follows an identical pattern, differing only in image name, port, and resource allocations. Compute-intensive engines (CV, AI, Western) receive higher CPU/memory reservations.

## StatefulSet for PostgreSQL+TimescaleDB

PostgreSQL with TimescaleDB runs as a StatefulSet with persistent storage, leveraging TimescaleDB compression and retention policies for efficient time-series storage.

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: pat-postgres
  namespace: predictatrade-data
spec:
  serviceName: pat-postgres
  replicas: 1
  selector:
    matchLabels:
      app: pat-postgres
  template:
    metadata:
      labels:
        app: pat-postgres
    spec:
      containers:
        - name: postgres
          image: timescale/timescaledb:2.16.1-pg16
          ports:
            - containerPort: 5432
          env:
            - name: POSTGRES_DB
              value: predictatrade
            - name: POSTGRES_USER
              valueFrom:
                secretKeyRef:
                  name: pg-credentials
                  key: username
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: pg-credentials
                  key: password
          volumeMounts:
            - name: pg-data
              mountPath: /var/lib/postgresql/data
            - name: pg-config
              mountPath: /etc/postgresql/postgresql.conf
              subPath: postgresql.conf
          resources:
            requests:
              cpu: "4"
              memory: "16Gi"
            limits:
              cpu: "8"
              memory: "32Gi"
  volumeClaimTemplates:
    - metadata:
        name: pg-data
      spec:
        accessModes: [ReadWriteOnce]
        storageClassName: premium-ssd
        resources:
          requests:
            storage: 500Gi
```

For production, use a managed database service (Cloud SQL, RDS, or Azure PostgreSQL Flexible Server) for automated backups, patching, and high availability. The StatefulSet approach is suitable for staging and smaller deployments.

## ConfigMaps and External Secrets

Configuration is split into ConfigMaps (non-sensitive) and External Secrets Operator references (sensitive data backed by HashiCorp Vault or cloud secret managers).

**ConfigMap example:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: pat-master-config
  namespace: predictatrade-system
data:
  LOG_LEVEL: "INFO"
  ENGINE_TIMEOUT_SECONDS: "30"
  VERDICT_CACHE_TTL: "60"
  SCORING_DIMENSIONS: "15"
  ENGINE_REGISTRY_PATH: "/app/config/engine_registry.yaml"
```

**ExternalSecret example:**

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: pat-master-secrets
  namespace: predictatrade-system
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: pat-master-secrets
  data:
    - secretKey: PG_DSN
      remoteRef:
        key: predictatrade/production/database
        property: dsn
    - secretKey: VALKEY_URL
      remoteRef:
        key: predictatrade/production/valkey
        property: url
    - secretKey: BROKER_API_KEY
      remoteRef:
        key: predictatrade/production/broker
        property: api_key
```

## Horizontal Pod Autoscaler (HPA) Rules

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: pat-api-hpa
  namespace: predictatrade-system
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: pat-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Percent
          value: 100
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Pods
          value: 1
          periodSeconds: 120
```

Engine services scale based on queue depth in Valkey rather than CPU/memory, using custom metrics from Prometheus:

```yaml
    - type: Pods
      pods:
        metric:
          name: engine_queue_depth
        target:
          type: AverageValue
          averageValue: "10"
```

## NetworkPolicy

Deny all by default, then explicitly allow required communication paths:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
  namespace: predictatrade-engines
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-from-master
  namespace: predictatrade-engines
spec:
  podSelector:
    matchLabels:
      app: pat-engine
  policyTypes:
    - Ingress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: predictatrade-system
          podSelector:
            matchLabels:
              app: pat-master
      ports:
        - protocol: TCP
          port: 8000
```

## Helm Chart Outline

The platform ships as a Helm chart with a single `values.yaml` controlling all services:

```
helm/predictatrade/
  Chart.yaml
  values.yaml
  values-gke.yaml
  values-eks.yaml
  values-aks.yaml
  templates/
    namespaces.yaml
    _helpers.tpl
    configmaps.yaml
    secrets.yaml
    postgres-statefulset.yaml
    valkey-deployment.yaml
    master-deployment.yaml
    api-deployment.yaml
    engine-deployments.yaml
    frontend-deployment.yaml
    execution-deployment.yaml
    data-deployment.yaml
    ingress.yaml
    hpa.yaml
    networkpolicies.yaml
    serviceaccounts.yaml
```

Installation:

```bash
helm repo add predictatrade https://charts.predictatrade.com
helm install pat predictatrade/predictatrade \
  --namespace predictatrade-system \
  --create-namespace \
  -f values-gke.yaml
```

## Ingress and cert-manager

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: pat-ingress
  namespace: predictatrade-system
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - api.predictatrade.com
        - app.predictatrade.com
      secretName: predictatrade-tls
  rules:
    - host: api.predictatrade.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: pat-api
                port:
                  number: 8001
    - host: app.predictatrade.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: pat-frontend
                port:
                  number: 3000
```

## CI/CD Pipeline (GitHub Actions)

```yaml
name: Deploy to GKE
on:
  push:
    branches: [main]
    tags: ["v*"]
jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - id: auth
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ vars.GCP_WIP }}
          service_account: ${{ vars.GCP_SA }}
      - uses: google-github-actions/get-gke-credentials@v2
        with:
          cluster_name: predictatrade-prod
          location: us-central1
      - name: Build and push images
        run: |
          docker build -t ghcr.io/predictatrade/pat-master:${{ github.sha }} -f Dockerfile.master .
          docker push ghcr.io/predictatrade/pat-master:${{ github.sha }}
      - name: Deploy with Helm
        run: |
          helm upgrade --install pat ./helm/predictatrade \
            --namespace predictatrade-system \
            -f helm/predictatrade/values-gke.yaml \
            --set image.tag=${{ github.sha }}
```

## Multi-Cloud Considerations

| Feature            | GKE                     | EKS                      | AKS                      |
|-------------------|------------------------|--------------------------|--------------------------|
| Workload Identity  | Native integration      | IRSA (IAM Roles for SA)  | Workload Identity        |
| Secret Manager     | Secret Manager CSI      | Secrets Manager CSI      | Key Vault CSI            |
| GPU Support        | T4/L4/A100 autopilot   | G5/P4d instances         | NCasT4_v3                |
| CNI               | Cilium (default)        | VPC CNI or Cilium        | Azure CNI or Cilium      |
| Persistent Storage | Persistent Disk SSD     | gp3 or io2               | Premium SSD              |

For cost optimization, use spot/preemptible VMs for engine pods and reserved instances for stateful workloads (databases, message queues). Implement pod disruption budgets to gracefully handle preemptions.
