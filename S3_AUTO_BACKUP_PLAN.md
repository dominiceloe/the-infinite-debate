# S3 Automated Backup Implementation Plan

**Project:** Philosophical Debates Platform
**Purpose:** Production-grade PostgreSQL backups to AWS S3
**Created:** 2025-10-25
**Estimated Implementation Time:** 60-90 minutes

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [AWS Setup](#aws-setup)
5. [Script Implementation](#script-implementation)
6. [Environment Configuration](#environment-configuration)
7. [Automation Setup](#automation-setup)
8. [Testing & Verification](#testing--verification)
9. [Monitoring](#monitoring)
10. [Cost Breakdown](#cost-breakdown)
11. [Disaster Recovery](#disaster-recovery)
12. [Troubleshooting](#troubleshooting)

---

## Overview

### What This Implements

Industry-standard PostgreSQL backup system with:

- ✅ **Daily automated backups** to AWS S3
- ✅ **Monthly archive backups** (kept indefinitely)
- ✅ **30-day retention** for daily backups
- ✅ **AES-256 encryption** at rest
- ✅ **S3 versioning** (protect against accidental deletion)
- ✅ **Cross-region replication** (disaster recovery)
- ✅ **Automated integrity verification**
- ✅ **Restore testing** (monthly)

### Why S3?

- **Durability:** 99.999999999% (11 9's)
- **Compliance:** SOC2, HIPAA, ISO 27001 certified
- **Industry standard:** Used by Netflix, Airbnb, Reddit
- **Cost-effective:** ~$3-5/month for typical database backups
- **Integrated:** Works seamlessly with AWS Lightsail deployment

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Backup Workflow                              │
└─────────────────────────────────────────────────────────────────┘

  PostgreSQL (Docker)
       │
       │ pg_dump
       ↓
  /tmp/backup.sql
       │
       │ gzip compress
       ↓
  /tmp/backup.sql.gz
       │
       │ AWS CLI upload (AES-256 encryption)
       ↓
  S3: s3://philosophical-debates-backups/
       │
       ├── daily/
       │    ├── 2025-10-25/debates_daily_20251025_030000.sql.gz
       │    ├── 2025-10-24/debates_daily_20251024_030000.sql.gz
       │    └── ... (30 days)
       │
       └── monthly/
            ├── 2025-10/debates_monthly_20251001_030000.sql.gz
            ├── 2025-09/debates_monthly_20250901_030000.sql.gz
            └── ... (indefinite)

       ↓ (cross-region replication)

  S3: s3://philosophical-debates-backups-dr/ (us-west-2)
```

### Retention Policy

| Backup Type | Frequency | Retention | Storage Class |
|-------------|-----------|-----------|---------------|
| Daily | Every day at 3 AM | 30 days | S3 Standard |
| Monthly | 1st of month at 4 AM | Indefinite | S3 Standard → Glacier (90 days) |

---

## Prerequisites

### 1. AWS Account

- Active AWS account with billing enabled
- AWS CLI installed locally (for initial setup)

### 2. System Requirements

- Docker Compose running (PostgreSQL container)
- Bash shell (macOS/Linux)
- ~500MB free disk space (temporary backup files)

### 3. Knowledge Requirements

- Basic AWS console navigation
- Command-line familiarity
- Understanding of environment variables

---

## AWS Setup

### Step 1: Create S3 Buckets

**Primary bucket (us-east-1):**

```bash
# Set your preferred region
REGION=us-east-1
BUCKET_NAME=philosophical-debates-backups

# Create bucket
aws s3 mb s3://$BUCKET_NAME --region $REGION

# Enable versioning (protects against accidental deletion)
aws s3api put-bucket-versioning \
  --bucket $BUCKET_NAME \
  --versioning-configuration Status=Enabled \
  --region $REGION

# Enable encryption by default
aws s3api put-bucket-encryption \
  --bucket $BUCKET_NAME \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }' \
  --region $REGION

# Block public access (security)
aws s3api put-public-access-block \
  --bucket $BUCKET_NAME \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" \
  --region $REGION
```

**Disaster recovery bucket (us-west-2) - OPTIONAL:**

```bash
DR_BUCKET_NAME=philosophical-debates-backups-dr
DR_REGION=us-west-2

# Create DR bucket
aws s3 mb s3://$DR_BUCKET_NAME --region $DR_REGION

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket $DR_BUCKET_NAME \
  --versioning-configuration Status=Enabled \
  --region $DR_REGION
```

### Step 2: Create IAM User for Backups

**Create IAM policy:**

```bash
cat > backup-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BackupToS3",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": [
        "arn:aws:s3:::philosophical-debates-backups/*",
        "arn:aws:s3:::philosophical-debates-backups"
      ]
    }
  ]
}
EOF

# Create policy
aws iam create-policy \
  --policy-name PhilosophicalDebatesBackupPolicy \
  --policy-document file://backup-policy.json
```

**Create IAM user:**

```bash
# Create user
aws iam create-user --user-name philosophical-debates-backup

# Attach policy (replace ACCOUNT_ID with your AWS account ID)
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws iam attach-user-policy \
  --user-name philosophical-debates-backup \
  --policy-arn arn:aws:iam::$ACCOUNT_ID:policy/PhilosophicalDebatesBackupPolicy

# Create access key
aws iam create-access-key --user-name philosophical-debates-backup

# Save the output! You'll need:
# - AccessKeyId
# - SecretAccessKey
```

**⚠️ IMPORTANT:** Save the access key credentials immediately. They won't be shown again.

### Step 3: Configure Cross-Region Replication (OPTIONAL)

```bash
# Create replication role
cat > replication-role-trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "s3.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF

aws iam create-role \
  --role-name s3-replication-role \
  --assume-role-policy-document file://replication-role-trust-policy.json

# Attach replication policy
cat > replication-role-permissions.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetReplicationConfiguration",
        "s3:ListBucket"
      ],
      "Resource": "arn:aws:s3:::philosophical-debates-backups"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObjectVersionForReplication",
        "s3:GetObjectVersionAcl"
      ],
      "Resource": "arn:aws:s3:::philosophical-debates-backups/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:ReplicateObject",
        "s3:ReplicateDelete"
      ],
      "Resource": "arn:aws:s3:::philosophical-debates-backups-dr/*"
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name s3-replication-role \
  --policy-name ReplicationPolicy \
  --policy-document file://replication-role-permissions.json

# Enable replication on primary bucket
ROLE_ARN=$(aws iam get-role --role-name s3-replication-role --query Role.Arn --output text)

cat > replication-config.json << EOF
{
  "Role": "$ROLE_ARN",
  "Rules": [
    {
      "Status": "Enabled",
      "Priority": 1,
      "DeleteMarkerReplication": {"Status": "Enabled"},
      "Filter": {},
      "Destination": {
        "Bucket": "arn:aws:s3:::philosophical-debates-backups-dr",
        "ReplicationTime": {
          "Status": "Enabled",
          "Time": {"Minutes": 15}
        },
        "Metrics": {
          "Status": "Enabled",
          "EventThreshold": {"Minutes": 15}
        }
      }
    }
  ]
}
EOF

aws s3api put-bucket-replication \
  --bucket philosophical-debates-backups \
  --replication-configuration file://replication-config.json \
  --region us-east-1
```

---

## Script Implementation

### Script 1: S3 Backup Script

**Create:** `backend/scripts/backup-to-s3.sh`

```bash
#!/usr/bin/env bash
#
# PostgreSQL Backup to AWS S3
# Production-grade backup with encryption and verification

set -e
set -o pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration from environment
DB_NAME="${DB_NAME:-debates}"
DB_USER="${DB_USER:-debatesuser}"
AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"
S3_BACKUP_BUCKET="${S3_BACKUP_BUCKET}"

# Validate configuration
if [ -z "$S3_BACKUP_BUCKET" ]; then
    echo -e "${RED}ERROR: S3_BACKUP_BUCKET not set in .env${NC}"
    exit 1
fi

if ! command -v aws &> /dev/null; then
    echo -e "${RED}ERROR: AWS CLI not installed${NC}"
    echo "Install: brew install awscli"
    exit 1
fi

# Parse arguments
MONTHLY=false
if [[ "$1" == "--monthly" ]]; then
    MONTHLY=true
fi

# Generate timestamps and paths
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DATE=$(date +"%Y-%m-%d")
MONTH=$(date +"%Y-%m")

if [ "$MONTHLY" = true ]; then
    BACKUP_TYPE="monthly"
    S3_PREFIX="monthly/${MONTH}"
else
    BACKUP_TYPE="daily"
    S3_PREFIX="daily/${DATE}"
fi

# Temporary directory
TEMP_DIR="/tmp/db_backup_$$"
mkdir -p "$TEMP_DIR"
BACKUP_FILE="$TEMP_DIR/${DB_NAME}_${BACKUP_TYPE}_${TIMESTAMP}.sql"
BACKUP_FILE_GZ="${BACKUP_FILE}.gz"

# Cleanup on exit
trap "rm -rf $TEMP_DIR" EXIT

echo "======================================="
echo "PostgreSQL Backup to AWS S3"
echo "======================================="
echo "Database: $DB_NAME"
echo "Backup type: $BACKUP_TYPE"
echo "S3 bucket: s3://$S3_BACKUP_BUCKET"
echo "S3 path: $S3_PREFIX"
echo "---------------------------------------"

# Step 1: Create database dump
echo -e "${YELLOW}[1/4] Creating database dump...${NC}"
if docker compose exec -T db pg_dump -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_FILE"; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo -e "${GREEN}✓ Database dump created ($BACKUP_SIZE)${NC}"
else
    echo -e "${RED}✗ Database dump failed${NC}"
    exit 1
fi

# Step 2: Compress backup
echo -e "${YELLOW}[2/4] Compressing backup...${NC}"
gzip "$BACKUP_FILE"
COMPRESSED_SIZE=$(du -h "$BACKUP_FILE_GZ" | cut -f1)
echo -e "${GREEN}✓ Compressed to $COMPRESSED_SIZE${NC}"

# Step 3: Upload to S3 with encryption
echo -e "${YELLOW}[3/4] Uploading to S3...${NC}"
S3_KEY="${S3_PREFIX}/$(basename $BACKUP_FILE_GZ)"

if aws s3 cp "$BACKUP_FILE_GZ" \
    "s3://$S3_BACKUP_BUCKET/$S3_KEY" \
    --server-side-encryption AES256 \
    --storage-class STANDARD \
    --metadata "backup-type=$BACKUP_TYPE,database=$DB_NAME,timestamp=$TIMESTAMP" \
    --region "$AWS_DEFAULT_REGION"; then
    echo -e "${GREEN}✓ Uploaded to s3://$S3_BACKUP_BUCKET/$S3_KEY${NC}"
else
    echo -e "${RED}✗ S3 upload failed${NC}"
    exit 1
fi

# Step 4: Verify upload integrity
echo -e "${YELLOW}[4/4] Verifying upload integrity...${NC}"
S3_SIZE=$(aws s3api head-object \
    --bucket "$S3_BACKUP_BUCKET" \
    --key "$S3_KEY" \
    --query ContentLength \
    --output text \
    --region "$AWS_DEFAULT_REGION")

LOCAL_SIZE=$(stat -f%z "$BACKUP_FILE_GZ" 2>/dev/null || stat -c%s "$BACKUP_FILE_GZ")

if [ "$S3_SIZE" -eq "$LOCAL_SIZE" ]; then
    echo -e "${GREEN}✓ Upload verified ($COMPRESSED_SIZE)${NC}"
else
    echo -e "${RED}✗ Size mismatch! Local: $LOCAL_SIZE bytes, S3: $S3_SIZE bytes${NC}"
    exit 1
fi

# Success summary
echo "======================================="
echo -e "${GREEN}✓ Backup completed successfully!${NC}"
echo "======================================="
echo "S3 location: s3://$S3_BACKUP_BUCKET/$S3_KEY"
echo "Backup size: $COMPRESSED_SIZE"
echo "Encryption: AES-256 (server-side)"
echo "Storage class: STANDARD"
echo "Completed at: $(date)"
echo "======================================="

# Apply retention policy for daily backups (delete backups older than 30 days)
if [ "$MONTHLY" = false ]; then
    echo ""
    echo "Applying retention policy (keep 30 days)..."

    # Calculate cutoff date (30 days ago)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        CUTOFF_DATE=$(date -v-30d +%Y-%m-%d)
    else
        # Linux
        CUTOFF_DATE=$(date -d '30 days ago' +%Y-%m-%d)
    fi

    echo "Deleting backups older than $CUTOFF_DATE..."

    # List and delete old daily backups
    aws s3 ls "s3://$S3_BACKUP_BUCKET/daily/" --recursive --region "$AWS_DEFAULT_REGION" \
        | awk '{print $4}' \
        | grep -E "daily/[0-9]{4}-[0-9]{2}-[0-9]{2}" \
        | while read key; do
            backup_date=$(echo $key | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' | head -1)
            if [[ "$backup_date" < "$CUTOFF_DATE" ]]; then
                aws s3 rm "s3://$S3_BACKUP_BUCKET/$key" --region "$AWS_DEFAULT_REGION"
                echo "  Deleted: $key"
            fi
        done || echo "  No old backups to delete"
fi

echo ""
echo "Done!"
```

**Make executable:**
```bash
chmod +x backend/scripts/backup-to-s3.sh
```

### Script 2: S3 Restore Script

**Create:** `backend/scripts/restore-from-s3.sh`

```bash
#!/usr/bin/env bash
#
# Restore PostgreSQL database from AWS S3 backup

set -e
set -o pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
DB_NAME="${DB_NAME:-debates}"
DB_USER="${DB_USER:-debatesuser}"
AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"
S3_BACKUP_BUCKET="${S3_BACKUP_BUCKET}"

# Validate
if [ -z "$S3_BACKUP_BUCKET" ]; then
    echo -e "${RED}ERROR: S3_BACKUP_BUCKET not set${NC}"
    exit 1
fi

echo "======================================="
echo "Restore Database from AWS S3"
echo "======================================="
echo ""

# List available backups
echo -e "${BLUE}Available backups:${NC}"
echo ""
echo "DAILY BACKUPS (last 7 days):"
aws s3 ls "s3://$S3_BACKUP_BUCKET/daily/" --recursive --region "$AWS_DEFAULT_REGION" \
    | tail -7 \
    | awk '{print "  " $1 " " $2 " - " $4}' || echo "  (none found)"

echo ""
echo "MONTHLY BACKUPS:"
aws s3 ls "s3://$S3_BACKUP_BUCKET/monthly/" --recursive --region "$AWS_DEFAULT_REGION" \
    | awk '{print "  " $1 " " $2 " - " $4}' || echo "  (none found)"

echo ""
echo "======================================="
echo -e "${YELLOW}Enter S3 key to restore (e.g., daily/2025-10-25/debates_daily_20251025_030000.sql.gz):${NC}"
read -r S3_KEY

if [ -z "$S3_KEY" ]; then
    echo -e "${RED}No key provided. Exiting.${NC}"
    exit 1
fi

# Confirm restoration
echo ""
echo -e "${YELLOW}⚠️  WARNING: This will REPLACE the current database!${NC}"
echo "Database: $DB_NAME"
echo "Backup: s3://$S3_BACKUP_BUCKET/$S3_KEY"
echo ""
read -p "Type 'YES' to confirm: " -r CONFIRM

if [[ ! "$CONFIRM" == "YES" ]]; then
    echo "Restore cancelled."
    exit 0
fi

# Temporary directory
TEMP_DIR="/tmp/db_restore_$$"
mkdir -p "$TEMP_DIR"
trap "rm -rf $TEMP_DIR" EXIT

BACKUP_FILE_GZ="$TEMP_DIR/restore.sql.gz"
BACKUP_FILE="$TEMP_DIR/restore.sql"

echo ""
echo "======================================="
echo "Starting Restore Process"
echo "======================================="

# Step 1: Download from S3
echo -e "${YELLOW}[1/3] Downloading from S3...${NC}"
aws s3 cp "s3://$S3_BACKUP_BUCKET/$S3_KEY" "$BACKUP_FILE_GZ" --region "$AWS_DEFAULT_REGION"
DOWNLOAD_SIZE=$(du -h "$BACKUP_FILE_GZ" | cut -f1)
echo -e "${GREEN}✓ Downloaded ($DOWNLOAD_SIZE)${NC}"

# Step 2: Decompress
echo -e "${YELLOW}[2/3] Decompressing...${NC}"
gunzip "$BACKUP_FILE_GZ"
DECOMPRESSED_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo -e "${GREEN}✓ Decompressed ($DECOMPRESSED_SIZE)${NC}"

# Step 3: Restore to database
echo -e "${YELLOW}[3/3] Restoring to database...${NC}"
cat "$BACKUP_FILE" | docker compose exec -T db psql -U "$DB_USER" -d "$DB_NAME"
echo -e "${GREEN}✓ Database restored${NC}"

# Verification
echo ""
echo "======================================="
echo "Verifying restore..."
echo "======================================="

PERSONA_COUNT=$(docker compose exec -T db psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM personas_persona;" | tr -d ' ')
USER_COUNT=$(docker compose exec -T db psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM users_user;" | tr -d ' ')

echo "Personas: $PERSONA_COUNT"
echo "Users: $USER_COUNT"

echo ""
echo "======================================="
echo -e "${GREEN}✓ Restore completed successfully!${NC}"
echo "======================================="
```

**Make executable:**
```bash
chmod +x backend/scripts/restore-from-s3.sh
```

### Script 3: Automated Restore Test

**Create:** `backend/scripts/test-backup-restore.sh`

```bash
#!/usr/bin/env bash
#
# Test backup integrity by restoring to temporary database

set -e
set -o pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

DB_USER="${DB_USER:-debatesuser}"
AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"
S3_BACKUP_BUCKET="${S3_BACKUP_BUCKET}"

echo "======================================="
echo "Automated Backup Integrity Test"
echo "======================================="

# Get latest daily backup
echo "Finding latest backup..."
LATEST_BACKUP=$(aws s3 ls "s3://$S3_BACKUP_BUCKET/daily/" --recursive --region "$AWS_DEFAULT_REGION" \
    | sort | tail -1 | awk '{print $4}')

if [ -z "$LATEST_BACKUP" ]; then
    echo -e "${RED}✗ No backups found${NC}"
    exit 1
fi

echo "Latest backup: $LATEST_BACKUP"

# Download and decompress
TEMP_DIR="/tmp/backup_test_$$"
mkdir -p "$TEMP_DIR"
trap "rm -rf $TEMP_DIR" EXIT

BACKUP_FILE_GZ="$TEMP_DIR/test.sql.gz"
BACKUP_FILE="$TEMP_DIR/test.sql"

echo "Downloading..."
aws s3 cp "s3://$S3_BACKUP_BUCKET/$LATEST_BACKUP" "$BACKUP_FILE_GZ" --region "$AWS_DEFAULT_REGION"

echo "Decompressing..."
gunzip "$BACKUP_FILE_GZ"

# Create test database
echo "Creating test database..."
docker compose exec -T db psql -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS test_restore;" || true
docker compose exec -T db psql -U "$DB_USER" -d postgres -c "CREATE DATABASE test_restore;"

# Restore to test database
echo "Restoring to test database..."
cat "$BACKUP_FILE" | docker compose exec -T db psql -U "$DB_USER" -d test_restore

# Verify data
echo "Verifying data..."
PERSONA_COUNT=$(docker compose exec -T db psql -U "$DB_USER" -d test_restore -t -c "SELECT COUNT(*) FROM personas_persona;" | tr -d ' ')

if [ "$PERSONA_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ Backup integrity verified${NC}"
    echo "  Personas found: $PERSONA_COUNT"
else
    echo -e "${RED}✗ Backup appears corrupt (no data)${NC}"
    exit 1
fi

# Cleanup test database
docker compose exec -T db psql -U "$DB_USER" -d postgres -c "DROP DATABASE test_restore;"

echo "======================================="
echo -e "${GREEN}✓ Backup test passed!${NC}"
echo "======================================="
```

**Make executable:**
```bash
chmod +x backend/scripts/test-backup-restore.sh
```

---

## Environment Configuration

### Update `.env` file

Add these variables to `backend/.env`:

```bash
# AWS S3 Backup Configuration
S3_BACKUP_BUCKET=philosophical-debates-backups
AWS_ACCESS_KEY_ID=AKIA...  # From IAM user creation step
AWS_SECRET_ACCESS_KEY=...   # From IAM user creation step
AWS_DEFAULT_REGION=us-east-1
```

**⚠️ SECURITY:**
- NEVER commit `.env` to git
- Ensure `.env` is in `.gitignore`
- Use different credentials for production vs. development

### Update Makefile

Add to `backend/Makefile`:

```makefile
# S3 Backup targets
backup-s3:
	@echo "Creating S3 backup..."
	./scripts/backup-to-s3.sh

backup-s3-monthly:
	@echo "Creating monthly S3 backup..."
	./scripts/backup-to-s3.sh --monthly

restore-s3:
	@echo "Restoring from S3..."
	./scripts/restore-from-s3.sh

test-backup:
	@echo "Testing backup integrity..."
	./scripts/test-backup-restore.sh

.PHONY: backup-s3 backup-s3-monthly restore-s3 test-backup
```

---

## Automation Setup

### Option 1: Cron (Development/Local Server)

**Edit crontab:**
```bash
crontab -e
```

**Add these lines:**
```cron
# Daily backup at 3 AM
0 3 * * * cd /Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/backend && ./scripts/backup-to-s3.sh >> logs/backup.log 2>&1

# Monthly backup on 1st of month at 4 AM
0 4 1 * * cd /Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/backend && ./scripts/backup-to-s3.sh --monthly >> logs/backup.log 2>&1

# Test backup integrity on 15th of month at 5 AM
0 5 15 * * cd /Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/backend && ./scripts/test-backup-restore.sh >> logs/backup-test.log 2>&1
```

**Verify cron setup:**
```bash
crontab -l
```

### Option 2: Systemd Timers (Linux Production)

**Create timer:** `/etc/systemd/system/backup-s3.timer`

```ini
[Unit]
Description=Daily PostgreSQL S3 Backup
Requires=backup-s3.service

[Timer]
OnCalendar=daily
OnCalendar=*-*-* 03:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

**Create service:** `/etc/systemd/system/backup-s3.service`

```ini
[Unit]
Description=PostgreSQL S3 Backup Service

[Service]
Type=oneshot
User=ubuntu
WorkingDirectory=/opt/philosophical-debates/backend
EnvironmentFile=/opt/philosophical-debates/backend/.env
ExecStart=/opt/philosophical-debates/backend/scripts/backup-to-s3.sh
```

**Enable timer:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable backup-s3.timer
sudo systemctl start backup-s3.timer
sudo systemctl status backup-s3.timer
```

### Option 3: AWS EventBridge (Fully Managed)

**For AWS Lightsail deployment:**

1. Create EventBridge rule
2. Trigger Lambda function
3. Lambda runs backup script on EC2 instance via SSM

**Advantages:**
- No cron management
- Automatic failure notifications
- CloudWatch logging built-in

---

## Testing & Verification

### Initial Test

**1. Test manual backup:**
```bash
cd backend
make backup-s3
```

**Expected output:**
```
=======================================
PostgreSQL Backup to AWS S3
=======================================
Database: debates
Backup type: daily
S3 bucket: s3://philosophical-debates-backups
S3 path: daily/2025-10-25
---------------------------------------
[1/4] Creating database dump...
✓ Database dump created (2.4M)
[2/4] Compressing backup...
✓ Compressed to 735K
[3/4] Uploading to S3...
✓ Uploaded to s3://philosophical-debates-backups/daily/2025-10-25/debates_daily_20251025_103000.sql.gz
[4/4] Verifying upload integrity...
✓ Upload verified (735K)
=======================================
✓ Backup completed successfully!
=======================================
```

**2. Verify in S3:**
```bash
aws s3 ls s3://philosophical-debates-backups/daily/ --recursive --human-readable
```

**3. Test restore:**
```bash
make restore-s3
```

**4. Test automated integrity check:**
```bash
make test-backup
```

### Verification Checklist

- [ ] Manual backup completes successfully
- [ ] File appears in S3 bucket
- [ ] File size matches local backup
- [ ] Encryption enabled (check S3 console)
- [ ] Versioning works (upload same file twice, check versions)
- [ ] Restore works correctly
- [ ] Automated test passes
- [ ] Cron job runs successfully (check logs next day)

---

## Monitoring

### CloudWatch Metrics

**Create CloudWatch alarm for backup failures:**

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name postgresql-backup-failure \
  --alarm-description "Alert when PostgreSQL backup fails" \
  --metric-name BackupFailure \
  --namespace CustomMetrics/Backups \
  --statistic Sum \
  --period 86400 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT_ID:backup-alerts
```

### SNS Notifications

**Create SNS topic for alerts:**

```bash
aws sns create-topic --name backup-alerts --region us-east-1

# Subscribe your email
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:ACCOUNT_ID:backup-alerts \
  --protocol email \
  --notification-endpoint your-email@example.com
```

### Log Monitoring

**Create CloudWatch Log Group:**

```bash
aws logs create-log-group --log-group-name /aws/backups/postgresql --region us-east-1

# Set retention (30 days)
aws logs put-retention-policy \
  --log-group-name /aws/backups/postgresql \
  --retention-in-days 30 \
  --region us-east-1
```

**Send logs to CloudWatch (modify backup script):**

Add to backup script:
```bash
# After successful backup
aws logs put-log-events \
  --log-group-name /aws/backups/postgresql \
  --log-stream-name $(date +%Y-%m-%d) \
  --log-events timestamp=$(date +%s000),message="Backup successful: $S3_KEY"
```

---

## Cost Breakdown

### Monthly Cost Estimate

**Assumptions:**
- Database size: 2 GB (uncompressed)
- Compressed backup: 750 MB
- Retention: 30 daily + 12 monthly backups

**S3 Storage Costs:**

| Item | Size | Cost/GB | Monthly Cost |
|------|------|---------|--------------|
| Daily backups (30 × 750 MB) | 22.5 GB | $0.023 | $0.52 |
| Monthly backups (12 × 750 MB) | 9 GB | $0.023 | $0.21 |
| **Total Storage** | **31.5 GB** | | **$0.73** |

**S3 Request Costs:**

| Request Type | Count/Month | Cost/1000 | Monthly Cost |
|--------------|-------------|-----------|--------------|
| PUT (daily backups) | 30 | $0.005 | $0.0002 |
| PUT (monthly backups) | 1 | $0.005 | $0.0000 |
| GET (restores) | 2 | $0.0004 | $0.0000 |
| LIST (retention cleanup) | 30 | $0.005 | $0.0002 |
| **Total Requests** | | | **$0.0004** |

**Data Transfer:**
- Upload to S3: FREE (within AWS)
- Download from S3: $0.09/GB (first 10 TB)
- Monthly restores (testing): 2 × 750 MB = $0.14

**Cross-Region Replication (OPTIONAL):**
- Data transfer: $0.02/GB × 31.5 GB = $0.63/month
- Storage in DR region: $0.73/month

**Total Monthly Cost:**
- **Without DR:** $0.88/month (~$11/year)
- **With DR:** $2.24/month (~$27/year)

**Cost-saving tips:**
- Use S3 Glacier for monthly backups older than 90 days (-60% cost)
- Reduce retention to 7 days if not needed
- Skip cross-region replication if not critical

---

## Disaster Recovery

### Recovery Scenarios

#### Scenario 1: Accidental Data Deletion

**Recovery Time:** 5-10 minutes

1. List recent backups
2. Download latest backup
3. Restore to database
4. Verify data

```bash
make restore-s3
```

#### Scenario 2: Database Corruption

**Recovery Time:** 10-15 minutes

1. Identify corruption time
2. Find backup from before corruption
3. Restore from that backup
4. Replay recent transactions if needed (manual)

#### Scenario 3: Regional Outage (AWS us-east-1 down)

**Recovery Time:** 30-60 minutes (with DR setup)

1. Switch to DR bucket (us-west-2)
2. Update `.env` with DR region
3. Restore from DR bucket
4. Update DNS to point to backup region

```bash
# Update .env
S3_BACKUP_BUCKET=philosophical-debates-backups-dr
AWS_DEFAULT_REGION=us-west-2

# Restore
make restore-s3
```

#### Scenario 4: Complete Data Loss

**Recovery Time:** 15-30 minutes

1. Provision new database
2. Restore latest monthly backup
3. Restore latest daily backup on top
4. Verify all data

### Recovery Testing Schedule

- **Weekly:** Verify backups exist in S3
- **Monthly:** Automated restore test (15th of month)
- **Quarterly:** Manual full disaster recovery drill
- **Annually:** Regional failover test (if using DR)

### Recovery SLAs

| Data Loss Scenario | RTO (Recovery Time) | RPO (Data Loss) |
|-------------------|---------------------|-----------------|
| Accidental deletion | 10 minutes | 0 (point-in-time) |
| Database corruption | 15 minutes | Up to 24 hours |
| Regional outage | 1 hour | Up to 24 hours |
| Complete data loss | 30 minutes | Up to 24 hours |

---

## Troubleshooting

### Issue 1: "AWS CLI not found"

**Symptoms:**
```
ERROR: AWS CLI not installed
```

**Solution:**
```bash
# macOS
brew install awscli

# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Verify
aws --version
```

### Issue 2: "Access Denied" when uploading

**Symptoms:**
```
✗ S3 upload failed
An error occurred (AccessDenied) when calling the PutObject operation
```

**Causes:**
- AWS credentials not set
- IAM policy insufficient permissions
- Bucket name typo

**Solution:**
```bash
# Verify credentials
aws sts get-caller-identity

# Check bucket exists
aws s3 ls s3://philosophical-debates-backups

# Test manual upload
aws s3 cp test.txt s3://philosophical-debates-backups/test.txt
```

### Issue 3: "Database dump failed"

**Symptoms:**
```
✗ Database dump failed
```

**Causes:**
- PostgreSQL container not running
- Wrong database credentials
- Database doesn't exist

**Solution:**
```bash
# Check containers
docker compose ps

# Test database connection
docker compose exec db psql -U debatesuser -d debates -c "SELECT 1;"

# Check database exists
docker compose exec db psql -U debatesuser -d postgres -c "\l"
```

### Issue 4: "Size mismatch" after upload

**Symptoms:**
```
✗ Size mismatch! Local: 771234, S3: 0
```

**Causes:**
- Upload interrupted
- Network issue
- S3 bucket policy blocking

**Solution:**
```bash
# Check S3 object directly
aws s3api head-object \
  --bucket philosophical-debates-backups \
  --key daily/2025-10-25/debates_daily_20251025_030000.sql.gz

# Re-run backup
make backup-s3
```

### Issue 5: Cron job not running

**Symptoms:**
- No new backups appearing in S3
- Log files not updating

**Solution:**
```bash
# Check cron is running
sudo service cron status  # Linux
launchctl list | grep cron  # macOS

# Check cron logs
grep CRON /var/log/syslog  # Linux
log show --predicate 'process == "cron"' --last 1h  # macOS

# Test cron syntax
# Add to crontab:
* * * * * echo "Test" >> /tmp/cron-test.log

# Wait 1 minute, check log
cat /tmp/cron-test.log
```

### Issue 6: "Backup test failed - no data"

**Symptoms:**
```
✗ Backup appears corrupt (no data)
```

**Causes:**
- Backup created from empty database
- Restore script error
- Database schema mismatch

**Solution:**
```bash
# Manually inspect backup
gunzip -c backups/debates_backup_20251025_030000.sql.gz | head -100

# Look for INSERT statements
gunzip -c backups/debates_backup_20251025_030000.sql.gz | grep "INSERT INTO personas_persona"

# If no INSERT statements, backup was from empty DB
```

---

## Security Best Practices

### 1. Credential Management

✅ **DO:**
- Store AWS credentials in `.env` (never commit)
- Use IAM user with minimal permissions
- Rotate access keys quarterly
- Enable MFA on AWS account

❌ **DON'T:**
- Hardcode credentials in scripts
- Share credentials between environments
- Use root AWS account credentials
- Commit `.env` to git

### 2. Encryption

✅ **Implemented:**
- Server-side encryption (AES-256)
- Encryption at rest in S3
- Encrypted data transfer (HTTPS)

🔐 **Optional (high security):**
- Client-side GPG encryption before upload
- AWS KMS for key management
- Encryption of backup files on disk

### 3. Access Control

✅ **Implemented:**
- IAM policy with least privilege
- S3 bucket public access blocked
- Versioning enabled (prevent deletion)

🔐 **Optional:**
- S3 bucket policy restricting access by IP
- MFA required for deletion
- AWS Organizations SCPs

### 4. Monitoring & Auditing

✅ **Should implement:**
- CloudWatch alarms for failures
- SNS notifications
- CloudWatch Logs for audit trail
- S3 access logging

🔐 **Advanced:**
- AWS CloudTrail for API auditing
- S3 Object Lock (compliance mode)
- AWS Config rules for compliance

---

## Maintenance

### Weekly Tasks

- [ ] Verify backups are running (check S3)
- [ ] Check cron logs for errors
- [ ] Monitor CloudWatch alarms

### Monthly Tasks

- [ ] Review S3 storage costs
- [ ] Run automated restore test
- [ ] Verify retention policy working
- [ ] Check AWS credential expiration

### Quarterly Tasks

- [ ] Rotate AWS access keys
- [ ] Review and update IAM policies
- [ ] Full disaster recovery drill
- [ ] Update documentation

### Annual Tasks

- [ ] Review backup retention policy
- [ ] Cost optimization review
- [ ] Regional failover test (if using DR)
- [ ] Security audit

---

## Next Steps

### Immediate (Implementation)

1. [ ] Complete AWS setup (30 minutes)
   - Create S3 buckets
   - Create IAM user
   - Configure credentials

2. [ ] Deploy scripts (10 minutes)
   - Create backup-to-s3.sh
   - Create restore-from-s3.sh
   - Create test script
   - Update Makefile

3. [ ] Test manually (15 minutes)
   - Run first backup
   - Verify in S3
   - Test restore
   - Test integrity check

4. [ ] Setup automation (15 minutes)
   - Configure cron jobs
   - Test cron execution
   - Setup CloudWatch (optional)

### Short-term (This Week)

5. [ ] Monitor first automated backup
6. [ ] Setup CloudWatch alarms
7. [ ] Document AWS credentials location
8. [ ] Create runbook for restore procedure

### Long-term (This Month)

9. [ ] Enable cross-region replication (optional)
10. [ ] Implement S3 Glacier transition for old monthlies
11. [ ] Setup automated restore testing
12. [ ] Create disaster recovery playbook

---

## Resources

### AWS Documentation

- [S3 Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/best-practices.html)
- [S3 Versioning](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html)
- [S3 Replication](https://docs.aws.amazon.com/AmazonS3/latest/userguide/replication.html)
- [IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)

### PostgreSQL Backup

- [pg_dump Documentation](https://www.postgresql.org/docs/current/app-pgdump.html)
- [Backup and Restore](https://www.postgresql.org/docs/current/backup.html)

### Tools

- [AWS CLI Reference](https://awscli.amazonaws.com/v2/documentation/api/latest/index.html)
- [S3 Pricing Calculator](https://calculator.aws/)

---

## Conclusion

This plan provides enterprise-grade PostgreSQL backups with:

✅ **Reliability:** 99.999999999% durability
✅ **Security:** AES-256 encryption, IAM access control
✅ **Cost-effective:** ~$1-5/month
✅ **Automated:** Daily backups, retention, testing
✅ **Disaster recovery:** Cross-region replication
✅ **Compliance:** SOC2, HIPAA, ISO 27001 certified storage

**Estimated implementation time:** 60-90 minutes
**Ongoing maintenance:** <30 minutes/month

After the catastrophic data loss incident on Oct 25, 2025, this system ensures your data is protected with industry-standard backup practices.

---

**Document Version:** 1.0
**Last Updated:** 2025-10-25
**Next Review:** After successful implementation
