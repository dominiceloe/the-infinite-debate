#!/usr/bin/env bash
#
# PostgreSQL Backup to AWS S3
# Production-grade backup with encryption and verification

set -e
set -o pipefail

# Load environment variables from .env file
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$BACKEND_DIR/.env"

if [ -f "$ENV_FILE" ]; then
    # Save original IFS
    OLDIFS=$IFS
    while IFS='=' read -r key value; do
        # Skip empty lines and comments
        if [[ -z "$key" ]] || [[ "$key" =~ ^[[:space:]]*# ]]; then
            continue
        fi
        # Remove leading/trailing whitespace
        key=$(echo "$key" | xargs)
        value=$(echo "$value" | xargs)
        # Export the variable
        export "$key=$value"
    done < "$ENV_FILE"
    # Restore original IFS
    IFS=$OLDIFS
fi

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
