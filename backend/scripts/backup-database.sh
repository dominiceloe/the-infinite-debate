#!/usr/bin/env bash
#
# Database Backup Script
# ======================
#
# Automated PostgreSQL backup with rotation and compression.
#
# Usage:
#   bash scripts/backup-database.sh [options]
#
# Options:
#   --output-dir DIR    Directory to store backups (default: ./backups)
#   --retention DAYS    Keep backups for N days (default: 7)
#   --monthly           Create monthly archive (never deleted)
#   --s3-bucket BUCKET  Upload to S3 bucket (optional)
#   --encrypt           Encrypt backup with GPG (requires GPG_KEY env var)
#   --verify            Verify backup integrity after creation
#   --quiet             Suppress output (for cron jobs)
#
# Environment Variables:
#   DB_NAME             Database name (required, loaded from .env)
#   DB_USER             Database user (required, loaded from .env)
#   DB_PASSWORD         Database password (required, loaded from .env)
#   GPG_KEY             GPG key ID for encryption (optional)
#   AWS_ACCESS_KEY_ID   AWS access key for S3 upload (optional)
#   AWS_SECRET_ACCESS_KEY AWS secret key for S3 upload (optional)
#
# Examples:
#   # Basic backup with 7-day retention
#   bash scripts/backup-database.sh
#
#   # Create monthly archive that never expires
#   bash scripts/backup-database.sh --monthly
#
#   # Upload to S3 and encrypt
#   bash scripts/backup-database.sh --s3-bucket my-backups --encrypt
#
#   # Run in cron (silent mode)
#   bash scripts/backup-database.sh --quiet
#
# Cron Setup (daily at 2 AM):
#   0 2 * * * cd /opt/app && bash scripts/backup-database.sh --quiet
#
# Monthly archive (1st of month at 3 AM):
#   0 3 1 * * cd /opt/app && bash scripts/backup-database.sh --monthly --quiet

set -e  # Exit on any error

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Default configuration
OUTPUT_DIR="./backups"
RETENTION_DAYS=7
MONTHLY=false
S3_BUCKET=""
ENCRYPT=false
VERIFY=false
QUIET=false

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --retention)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        --monthly)
            MONTHLY=true
            shift
            ;;
        --s3-bucket)
            S3_BUCKET="$2"
            shift 2
            ;;
        --encrypt)
            ENCRYPT=true
            shift
            ;;
        --verify)
            VERIFY=true
            shift
            ;;
        --quiet)
            QUIET=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Helper functions
log() {
    if [ "$QUIET" = false ]; then
        echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
    fi
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" >&2
}

success() {
    if [ "$QUIET" = false ]; then
        echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅ $1${NC}"
    fi
}

warning() {
    if [ "$QUIET" = false ]; then
        echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}"
    fi
}

# Load environment variables
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
else
    error ".env file not found"
    exit 1
fi

# Validate required environment variables
if [ -z "${DB_NAME}" ] || [ -z "${DB_USER}" ] || [ -z "${DB_PASSWORD}" ]; then
    error "Missing database credentials (DB_NAME, DB_USER, DB_PASSWORD)"
    exit 1
fi

# Create backup directory
mkdir -p "${OUTPUT_DIR}"

# Generate backup filename
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
if [ "$MONTHLY" = true ]; then
    BACKUP_NAME="debates_monthly_$(date +"%Y_%m").sql"
    BACKUP_FILE="${OUTPUT_DIR}/${BACKUP_NAME}"
else
    BACKUP_NAME="debates_${TIMESTAMP}.sql"
    BACKUP_FILE="${OUTPUT_DIR}/${BACKUP_NAME}"
fi

log "Starting database backup..."
log "Database: ${DB_NAME}"
log "Output: ${BACKUP_FILE}"

# Export password for pg_dump
export PGPASSWORD="${DB_PASSWORD}"

# Perform backup using docker compose exec
log "Running pg_dump..."
if docker compose -f docker-compose.yml ps db | grep -q "Up"; then
    docker compose -f docker-compose.yml exec -T db pg_dump \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        --format=plain \
        --no-owner \
        --no-acl \
        --clean \
        --if-exists \
        > "${BACKUP_FILE}"
else
    error "Database container is not running"
    exit 1
fi

# Check backup file size
BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
if [ ! -s "${BACKUP_FILE}" ]; then
    error "Backup file is empty"
    exit 1
fi

success "Backup created: ${BACKUP_FILE} (${BACKUP_SIZE})"

# Compress backup
log "Compressing backup..."
gzip -f "${BACKUP_FILE}"
COMPRESSED_FILE="${BACKUP_FILE}.gz"
COMPRESSED_SIZE=$(du -h "${COMPRESSED_FILE}" | cut -f1)
success "Compressed: ${COMPRESSED_FILE} (${COMPRESSED_SIZE})"

# Encrypt if requested
if [ "$ENCRYPT" = true ]; then
    if [ -z "${GPG_KEY}" ]; then
        warning "GPG_KEY not set, skipping encryption"
    else
        log "Encrypting backup with GPG..."
        gpg --encrypt --recipient "${GPG_KEY}" --output "${COMPRESSED_FILE}.gpg" "${COMPRESSED_FILE}"
        rm "${COMPRESSED_FILE}"
        FINAL_FILE="${COMPRESSED_FILE}.gpg"
        success "Encrypted: ${FINAL_FILE}"
    fi
else
    FINAL_FILE="${COMPRESSED_FILE}"
fi

# Verify backup integrity
if [ "$VERIFY" = true ]; then
    log "Verifying backup integrity..."
    if [ "$ENCRYPT" = true ] && [ -n "${GPG_KEY}" ]; then
        # Decrypt and verify
        gpg --decrypt "${FINAL_FILE}" | gunzip | head -n 10 > /dev/null 2>&1
    else
        # Verify compressed file
        gunzip -t "${FINAL_FILE}" 2>&1
    fi
    success "Backup integrity verified"
fi

# Upload to S3 if requested
if [ -n "${S3_BUCKET}" ]; then
    if command -v aws &> /dev/null; then
        log "Uploading to S3 bucket: ${S3_BUCKET}..."
        aws s3 cp "${FINAL_FILE}" "s3://${S3_BUCKET}/backups/$(basename ${FINAL_FILE})"
        success "Uploaded to S3"
    else
        warning "AWS CLI not installed, skipping S3 upload"
    fi
fi

# Rotate old backups (skip for monthly archives)
if [ "$MONTHLY" = false ]; then
    log "Rotating old backups (keeping last ${RETENTION_DAYS} days)..."
    DELETED_COUNT=0
    while IFS= read -r old_backup; do
        rm -f "${old_backup}"
        DELETED_COUNT=$((DELETED_COUNT + 1))
    done < <(find "${OUTPUT_DIR}" -name "debates_*.sql.gz*" -type f -mtime +${RETENTION_DAYS})

    if [ ${DELETED_COUNT} -gt 0 ]; then
        success "Deleted ${DELETED_COUNT} old backup(s)"
    else
        log "No old backups to delete"
    fi
fi

# Summary
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
success "Backup completed successfully!"
log "File: ${FINAL_FILE}"
log "Size: $(du -h ${FINAL_FILE} | cut -f1)"
log "Type: $([ "$MONTHLY" = true ] && echo "Monthly archive" || echo "Daily backup")"
log "Retention: $([ "$MONTHLY" = true ] && echo "Permanent" || echo "${RETENTION_DAYS} days")"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# List all backups
if [ "$QUIET" = false ]; then
    echo ""
    log "Available backups:"
    ls -lh "${OUTPUT_DIR}"/debates_*.sql.gz* 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
fi

exit 0
