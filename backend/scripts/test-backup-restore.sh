#!/usr/bin/env bash
#
# Test backup integrity by restoring to temporary database

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
