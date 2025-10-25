#!/usr/bin/env bash
#
# Restore PostgreSQL database from AWS S3 backup

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
