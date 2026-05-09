# Predict-A-Trade vNext — Deployment: AWS

> **Target:** Amazon Web Services (EC2, RDS, S3) | **OS:** Alma Linux 10
> **No Docker/Kubernetes dependency** — native services managed by systemd

---

## 1. Infrastructure Architecture (AWS)

```
                               AWS Cloud
  ┌──────────────────────────────────────────────────────────────┐
  │                                                              │
  │  Route 53 ─── CloudFront CDN ─── ALB (TLS termination)       │
  │                                     │                        │
  │              ┌──────────────────────┼──────────────────┐     │
  │              │                      │                  │     │
  │     ┌────────┴────────┐  ┌─────────┴─────────┐  ┌────┴───┐ │
  │     │ pat-frontend    │  │ pat-api EC2       │  │  S3    │ │
  │     │ EC2 (ASG)       │  │ pat-master EC2    │  │ Static │ │
  │     │                 │  │ pat-engine-* EC2  │  │ Assets │ │
  │     └─────────────────┘  │ pat-execution EC2 │  └────────┘ │
  │                          └────────┬──────────┘             │
  │                                   │                         │
  │              ┌────────────────────┼──────────────────┐     │
  │              │                    │                  │     │
  │     ┌────────┴────────┐  ┌───────┴────────┐  ┌──────┴────┐│
  │     │ RDS PostgreSQL  │  │ ElastiCache    │  │ S3 Wasabi ││
  │     │ + TimescaleDB   │  │ (Valkey)       │  │ Backup    ││
  │     └─────────────────┘  └────────────────┘  └───────────┘│
  │                                                              │
  │  Secrets Manager ─── CloudWatch ─── IAM ─── Security Hub    │
  └──────────────────────────────────────────────────────────────┘
```

---

## 2. Prerequisites

### 2.1 AWS CLI Setup

```bash
aws configure --profile predictatrade-prod
# Enter: AWS Access Key ID, Secret Access Key, region (us-east-1), output (json)

# Verify
aws sts get-caller-identity --profile predictatrade-prod
```

### 2.2 Required IAM Roles & Policies

| Role | Attached Policies | Purpose |
|---|---|---|
| `pat-ec2-role` | `AmazonSSMManagedInstanceCore`, `CloudWatchAgentServerPolicy`, custom S3 access | EC2 instances |
| `pat-rds-monitoring` | `AmazonRDSEnhancedMonitoringRole` | RDS monitoring |
| `pat-backup` | S3 bucket write (Wasabi-mapped) | Backup automation |

### 2.3 Required AWS Services (Provision Beforehand)

- **VPC:** Default or custom with public + private subnets
- **Security Groups:** Defined per tier (see Section 4)
- **Route 53:** Hosted zone for `predictatrade.com`
- **ACM:** TLS certificate for ALB/CloudFront

---

## 3. Compute: EC2 Instances

### 3.1 EC2 Instance Specifications

| Service | Instance Type | vCPU | RAM | Storage | Count |
|---|---|---|---|---|---|
| pat-api | c7i.xlarge | 4 | 8 GB | 50 GB gp3 | 1 (+ standby) |
| pat-master | c7i.2xlarge | 8 | 16 GB | 50 GB gp3 | 1 |
| pat-engine-cv | g5.xlarge (GPU) | 4 | 16 GB | 100 GB gp3 | 1 |
| pat-engine-ai | p3.2xlarge (GPU) | 8 | 61 GB | 200 GB gp3 | 1 |
| pat-engine-di | c7i.large | 2 | 4 GB | 50 GB gp3 | 1 |
| pat-engine-cw | c7i.large | 2 | 4 GB | 50 GB gp3 | 1 |
| pat-engine-western | c7i.large | 2 | 4 GB | 50 GB gp3 | 1 |
| pat-engine-cot | c7i.large | 2 | 4 GB | 50 GB gp3 | 1 |
| pat-engine-seasonality | c7i.large | 2 | 4 GB | 50 GB gp3 | 1 |
| pat-engine-macro | c7i.large | 2 | 4 GB | 50 GB gp3 | 1 |
| pat-engine-tech | c7i.large | 2 | 4 GB | 50 GB gp3 | 1 |
| pat-engine-exec | c7i.large | 2 | 4 GB | 50 GB gp3 | 1 |
| pat-execution | c7i.xlarge | 4 | 8 GB | 50 GB gp3 | 1 |
| pat-frontend | c7i.xlarge | 4 | 8 GB | 50 GB gp3 | 1 |
| Monitoring | c7i.xlarge | 4 | 8 GB | 200 GB gp3 | 1 |

### 3.2 Launch via AWS CLI

```bash
# Launch API server
aws ec2 run-instances \
  --profile predictatrade-prod \
  --image-id ami-0abcdef1234567890 \
  --instance-type c7i.xlarge \
  --key-name predictatrade-prod-key \
  --security-group-ids sg-xxx \
  --subnet-id subnet-xxx \
  --iam-instance-profile Name=pat-ec2-role \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":50,"VolumeType":"gp3","DeleteOnTermination":true}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=pat-api-prod},{Key=Environment,Value=production},{Key=Service,Value=pat-api}]' \
  --count 1
```

### 3.3 Bootstrapping (User Data Script)

```bash
#!/bin/bash
# User data script — runs on first boot

# Update & install base
dnf update -y
dnf install -y python3.12 postgresql16-server valkey nginx \
  prometheus2 grafana loki logrotate firewalld selinux-policy-targeted

# Install Predict-A-Trade (via ansible-pull or pre-baked AMI)
curl -sL https://releases.predictatrade.com/v2.0/install-aws.sh | bash -s -- \
  --role api \
  --environment production \
  --region us-east-1

# Start services
systemctl enable --now pat-api nginx
```

---

## 4. Networking & Security Groups

### 4.1 Security Group Matrix

| SG Name | Inbound Sources | Ports | Purpose |
|---|---|---|---|
| `pat-alb-sg` | 0.0.0.0/0 | 443 | ALB public TLS |
| `pat-api-sg` | ALB SG | 8000 | API from ALB |
| `pat-internal-sg` | All pat SGs | 8001–8200, 5432, 6379 | Internal engine/DB/cache comms |
| `pat-db-sg` | `pat-internal-sg` | 5432 | Database |
| `pat-cache-sg` | `pat-internal-sg` | 6379 | Valkey |
| `pat-ssh-sg` | Bastion/VPN CIDR | 22 | Admin SSH |

### 4.2 Security Group Creation

```bash
# Internal SG (engines inter-communication)
aws ec2 create-security-group \
  --group-name pat-internal-prod \
  --description "Internal engine comms" \
  --vpc-id vpc-xxx

aws ec2 authorize-security-group-ingress \
  --group-id sg-internal \
  --protocol tcp --port 8001-8200 \
  --source-group sg-internal
```

---

## 5. Database: RDS PostgreSQL + TimescaleDB

### 5.1 RDS Creation

```bash
aws rds create-db-instance \
  --db-instance-identifier pat-prod-pg \
  --db-instance-class db.r6g.2xlarge \
  --engine postgres \
  --engine-version 16.4 \
  --allocated-storage 1000 \
  --storage-type gp3 \
  --iops 12000 \
  --master-username pat_admin \
  --master-user-password "$(vault read -field=password secret/aws/rds/master)" \
  --vpc-security-group-ids sg-db \
  --db-subnet-group-name pat-db-subnet \
  --multi-az \
  --backup-retention-period 30 \
  --preferred-backup-window 02:00-04:00 \
  --preferred-maintenance-window sun:07:00-sun:09:00 \
  --enable-performance-insights \
  --monitoring-interval 60 \
  --monitoring-role-arn arn:aws:iam::123456789012:role/pat-rds-monitoring \
  --tags Key=Environment,Value=production Key=Service,Value=postgresql
```

### 5.2 TimescaleDB Extension

```sql
-- Connect after RDS creation
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
-- Verify
SELECT extname, extversion FROM pg_extension WHERE extname = 'timescaledb';
```

### 5.3 RDS Parameter Group Overrides

| Parameter | Value | Reason |
|---|---|---|
| `shared_preload_libraries` | `pg_stat_statements,timescaledb,auto_explain` | Required extensions |
| `max_connections` | 500 | Engine pool requirements |
| `work_mem` | 256MB | Complex query sorts |
| `maintenance_work_mem` | 2GB | VACUUM, CREATE INDEX |
| `effective_cache_size` | 48GB | Query planner |
| `random_page_cost` | 1.1 | SSD optimization |
| `wal_level` | `replica` | WAL archiving |
| `archive_mode` | `on` | WAL to S3 |
| `archive_command` | `pat-cli wal archive --target s3://pat-pg-wal/%f` | WAL path |

---

## 6. Cache: ElastiCache (Valkey-Compatible)

```bash
aws elasticache create-serverless-cache \
  --serverless-cache-name pat-valkey-prod \
  --engine valkey \
  --major-engine-version 8 \
  --security-group-ids sg-cache \
  --subnet-ids subnet-private-a subnet-private-b \
  --tags Key=Environment,Value=production
```

> **Note:** If using Valkey (not Redis), ensure compatibility mode. Alternatively, run Valkey
> directly on the monitoring EC2 instance to avoid ElastiCache pricing for small deployments.

---

## 7. Load Balancing: ALB + Target Groups

```bash
# Target group for API
aws elbv2 create-target-group \
  --name pat-api-tg \
  --protocol HTTP --port 8000 \
  --vpc-id vpc-xxx \
  --health-check-path /health \
  --health-check-interval-seconds 15 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3

# Target group for Frontend
aws elbv2 create-target-group \
  --name pat-frontend-tg \
  --protocol HTTP --port 3001 \
  --vpc-id vpc-xxx \
  --health-check-path /api/health \
  --health-check-interval-seconds 15

# ALB
aws elbv2 create-load-balancer \
  --name pat-alb-prod \
  --subnets subnet-public-a subnet-public-b \
  --security-groups sg-alb \
  --scheme internet-facing \
  --type application

# HTTPS Listener
aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTPS --port 443 \
  --certificates CertificateArn=$ACM_ARN \
  --default-actions Type=forward,TargetGroupArn=$FRONTEND_TG_ARN

# API routing rule
aws elbv2 create-rule \
  --listener-arn $LISTENER_ARN \
  --priority 10 \
  --conditions Field=host-header,Values=api.predictatrade.com \
  --actions Type=forward,TargetGroupArn=$API_TG_ARN
```

---

## 8. Observability: CloudWatch

### 8.1 CloudWatch Agent Configuration

```json
{
  "agent": {
    "metrics_collection_interval": 60,
    "logfile": "/opt/aws/amazon-cloudwatch-agent/logs/amazon-cloudwatch-agent.log"
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/pat/api.log",
            "log_group_name": "/predictatrade/production/api",
            "log_stream_name": "{instance_id}"
          },
          {
            "file_path": "/var/log/pat/master.log",
            "log_group_name": "/predictatrade/production/master",
            "log_stream_name": "{instance_id}"
          }
        ]
      }
    }
  },
  "metrics": {
    "metrics_collected": {
      "statsd": { "service_address": ":8125", "metrics_collection_interval": 15 }
    }
  }
}
```

### 8.2 Key CloudWatch Alarms

```bash
# API 5xx high
aws cloudwatch put-metric-alarm \
  --alarm-name pat-api-5xx-high \
  --metric-name HTTPCode_Target_5XX_Count \
  --namespace AWS/ApplicationELB \
  --statistic Sum --period 300 --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions $SNS_TOPIC_ARN

# RDS CPU high
aws cloudwatch put-metric-alarm \
  --alarm-name pat-rds-cpu-high \
  --metric-name CPUUtilization \
  --namespace AWS/RDS --dimensions Name=DBInstanceIdentifier,Value=pat-prod-pg \
  --statistic Average --period 300 --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 3
```

---

## 9. Deployment Script (Full Stack)

```bash
#!/bin/bash
# deploy-aws.sh — Full Predict-A-Trade AWS deployment
set -euo pipefail

ENV="${1:-production}"
REGION="${2:-us-east-1}"
PROFILE="predictatrade-$ENV"

echo "=== Predict-A-Trade v2.0 AWS Deployment ==="
echo "Environment: $ENV | Region: $REGION"

# 1. Validate prerequisites
echo "[1/8] Validating AWS prerequisites..."
aws sts get-caller-identity --profile "$PROFILE" > /dev/null
aws ec2 describe-vpcs --profile "$PROFILE" --region "$REGION" > /dev/null

# 2. Launch DB (if not exists)
echo "[2/8] Ensuring RDS instance..."
if ! aws rds describe-db-instances --db-instance-identifier "pat-$ENV-pg" --profile "$PROFILE" --region "$REGION" &>/dev/null; then
  ./scripts/aws-create-rds.sh "$ENV" "$REGION"
fi

# 3. Launch Cache (if not exists)
echo "[3/8] Ensuring ElastiCache..."
# Script creates or verifies cache cluster

# 4. Launch engine EC2 instances
echo "[4/8] Launching engine instances..."
for engine in cv ai di cw western cot seasonality macro tech exec; do
  ./scripts/aws-launch-engine.sh "$engine" "$ENV" "$REGION"
done

# 5. Launch Master Engine
echo "[5/8] Launching Master Engine..."
./scripts/aws-launch-engine.sh master "$ENV" "$REGION"

# 6. Launch API + Frontend
echo "[6/8] Launching API and Frontend..."
./scripts/aws-launch-engine.sh api "$ENV" "$REGION"
./scripts/aws-launch-engine.sh frontend "$ENV" "$REGION"

# 7. Configure ALB
echo "[7/8] Configuring Application Load Balancer..."
./scripts/aws-configure-alb.sh "$ENV" "$REGION"

# 8. Smoke tests
echo "[8/8] Running smoke tests..."
sleep 30
curl -sf "https://api.$ENV.predictatrade.com/health" && echo "✓ API healthy"
curl -sf "https://$ENV.predictatrade.com" && echo "✓ Frontend healthy"

echo "=== Deployment Complete ==="
```

---

## 10. Estimated Monthly Cost

| Resource | Spec | Monthly Estimate |
|---|---|---|
| EC2 (14 instances) | c7i.xlarge – p3.2xlarge | $6,200 |
| RDS PostgreSQL | db.r6g.2xlarge, Multi-AZ, 1TB | $1,400 |
| ElastiCache | serverless, 8 GB | $320 |
| ALB | per GB processed | $60 |
| CloudFront | 500 GB egress | $50 |
| S3 (Wasabi mapping) | 5 TB stored | $30 |
| Route 53 | Hosted zone + queries | $10 |
| Data Transfer | ~2 TB/month cross-AZ + egress | $400 |
| **TOTAL** | | **~$8,470/mo** |

> Cost optimization: consolidate engine instances (combine DI/CW/Western onto one c7i.2xlarge)
> for ~$1,200/month savings. Use Reserved Instances (1-year) for ~30% discount.
