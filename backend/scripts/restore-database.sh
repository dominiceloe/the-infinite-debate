#!/usr/bin/env bash
#
# Database Restore Script
# =======================
#
# Restore PostgreSQL database from backup with safety checks.
#
# Usage:
#   bash scripts/restore-database.sh [options] BACKUP_FILE
#
# Options:
#   --force             Skip confirmation prompt (dangerous!)
#   --verify            Verify database after restore
#   --from-s3           Download backup from S3 before restoring
#   --decrypt           Decrypt GPG-encrypted backup
#   --no-backup         Skip creating safety backup (not recommended)
#
# Arguments:
#   BACKUP_FILE         Path to backup file (.sql.gz or .sql.gz.gpg)
#                       Or S3 key if using --from-s3
#
# Environment Variables:
#   DB_NAME             Database name (loaded from .env)
#   DB_USER             Database user (loaded from .env)
#   DB_PASSWORD         Database password (loaded from .env)
#   GPG_PASSPHRASE      GPG passphrase for decryption (if encrypted)
#   AWS_ACCESS_KEY_ID   AWS access key for S3 download
#   AWS_SECRET_ACCESS_KEY AWS secret key for S3 download
#
# Examples:
#   # Restore from local backup (with confirmation)
#   bash scripts/restore-database.sh backups/debates_20251020_120000.sql.gz
#
#   # Restore from S3
#   bash scripts/restore-database.sh --from-s3 backups/debates_20251020_120000.sql.gz
#
#   # Restore encrypted backup
#   bash scripts/restore-database.sh --decrypt backups/debates_20251020_120000.sql.gz.gpg
#
#   # Force restore without confirmation (use in scripts only!)
#   bash scripts/restore-database.sh --force backups/debates_20251020_120000.sql.gz
#
#   # Restore and verify
#   bash scripts/restore-database.sh --verify backups/debates_20251020_120000.sql.gz
#
# Safety Features:
#   - Creates automatic backup before restore (unless --no-backup)
#   - Requires explicit confirmation (unless --force)
#   - Verifies backup file integrity before restore
#   - Validates database connection before restore
#   - Provides rollback instructions if restore fails

set -e  # Exit on any error

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
FORCE=false
VERIFY=false
FROM_S3=false
DECRYPT=false
NO_BACKUP=false
BACKUP_FILE=""
S3_BUCKET=""
TEMP_DIR="/tmp/debates_restore_$$"

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE=true
            shift
            ;;
        --verify)
            VERIFY=true
            shift
            ;;
        --from-s3)
            FROM_S3=true
            shift
            ;;
        --s3-bucket)
            S3_BUCKET="$2"
            shift 2
            ;;
        --decrypt)
            DECRYPT=true
            shift
            ;;
        --no-backup)
            NO_BACKUP=true
            shift
            ;;
        *)
            if [ -z "${BACKUP_FILE}" ]; then
                BACKUP_FILE="$1"
            else
                echo "Unknown option: $1"
                exit 1
            fi
            shift
            ;;
    esac
done

# Helper functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" >&2
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}"
}

cleanup() {
    if [ -d "${TEMP_DIR}" ]; then
        rm -rf "${TEMP_DIR}"
    fi
}

trap cleanup EXIT

# Validate backup file argument
if [ -z "${BACKUP_FILE}" ]; then
    error "Missing backup file argument"
    echo "Usage: bash scripts/restore-database.sh [options] BACKUP_FILE"
    exit 1
fi

# Load environment variables
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
else
    error ".env file not found"
    exit 1
fi

# Validate database credentials
if [ -z "${DB_NAME}" ] || [ -z "${DB_USER}" ] || [ -z "${DB_PASSWORD}" ]; then
    error "Missing database credentials (DB_NAME, DB_USER, DB_PASSWORD)"
    exit 1
fi

# Create temp directory
mkdir -p "${TEMP_DIR}"

# Download from S3 if requested
if [ "$FROM_S3" = true ]; then
    if [ -z "${S3_BUCKET}" ]; then
        error "S3_BUCKET not specified (use --s3-bucket BUCKET)"
        exit 1
    fi

    if ! command -v aws &> /dev/null; then
        error "AWS CLI not installed"
        exit 1
    fi

    log "Downloading backup from S3..."
    LOCAL_FILE="${TEMP_DIR}/$(basename ${BACKUP_FILE})"
    aws s3 cp "s3://${S3_BUCKET}/${BACKUP_FILE}" "${LOCAL_FILE}"
    BACKUP_FILE="${LOCAL_FILE}"
    success "Downloaded from S3"
fi

# Check backup file exists
if [ ! -f "${BACKUP_FILE}" ]; then
    error "Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

log "Backup file: ${BACKUP_FILE}"
log "Size: $(du -h ${BACKUP_FILE} | cut -f1)"

# Decrypt if encrypted
if [ "$DECRYPT" = true ] || [[ "${BACKUP_FILE}" == *.gpg ]]; then
    log "Decrypting backup..."
    DECRYPTED_FILE="${TEMP_DIR}/decrypted.sql.gz"
    if [ -n "${GPG_PASSPHRASE}" ]; then
        echo "${GPG_PASSPHRASE}" | gpg --batch --yes --passphrase-fd 0 --output "${DECRYPTED_FILE}" --decrypt "${BACKUP_FILE}"
    else
        gpg --output "${DECRYPTED_FILE}" --decrypt "${BACKUP_FILE}"
    fi
    BACKUP_FILE="${DECRYPTED_FILE}"
    success "Decrypted backup"
fi

# Verify backup integrity
log "Verifying backup integrity..."
if [[ "${BACKUP_FILE}" == *.gz ]]; then
    if ! gunzip -t "${BACKUP_FILE}" 2>&1; then
        error "Backup file is corrupted"
        exit 1
    fi
else
    if ! head -n 10 "${BACKUP_FILE}" > /dev/null 2>&1; then
        error "Backup file is corrupted"
        exit 1
    fi
fi
success "Backup integrity verified"

# Check database connection
log "Checking database connection..."
export PGPASSWORD="${DB_PASSWORD}"
if ! docker compose -f docker-compose.yml ps db | grep -q "Up"; then
    error "Database container is not running"
    error "Start with: docker compose up -d db"
    exit 1
fi

if ! docker compose -f docker-compose.yml exec -T db pg_isready -U "${DB_USER}" > /dev/null 2>&1; then
    error "Database is not accepting connections"
    exit 1
fi
success "Database connection verified"

# Count current records
log "Checking current database state..."
CURRENT_DEBATES=$(docker compose -f docker-compose.yml exec -T db psql -U "${DB_USER}" -d "${DB_NAME}" -t -c "SELECT COUNT(*) FROM debates_debate;" 2>/dev/null | xargs || echo "0")
CURRENT_PERSONAS=$(docker compose -f docker-compose.yml exec -T db psql -U "${DB_USER}" -d "${DB_NAME}" -t -c "SELECT COUNT(*) FROM personas_persona;" 2>/dev/null | xargs || echo "0")
CURRENT_USERS=$(docker compose -f docker-compose.yml exec -T db psql -U "${DB_USER}" -d "${DB_NAME}" -t -c "SELECT COUNT(*) FROM users_user;" 2>/dev/null | xargs || echo "0")

log "Current database contents:"
log "  - Debates: ${CURRENT_DEBATES}"
log "  - Personas: ${CURRENT_PERSONAS}"
log "  - Users: ${CURRENT_USERS}"

# Warning and confirmation
echo ""
warning "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
warning "⚠️  DATABASE RESTORE WARNING ⚠️"
warning "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
warning ""
warning "This will REPLACE the current database with backup data!"
warning ""
warning "Current database: ${DB_NAME}"
warning "Backup file: ${BACKUP_FILE}"
warning ""
warning "⚠️  ALL CURRENT DATA WILL BE LOST ⚠️"
warning "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Create safety backup before restore (unless disabled)
if [ "$NO_BACKUP" = false ]; then
    log "Creating safety backup before restore..."
    SAFETY_BACKUP="${TEMP_DIR}/pre_restore_backup_$(date +%Y%m%d_%H%M%S).sql.gz"

    docker compose -f docker-compose.yml exec -T db pg_dump \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        --format=plain \
        --no-owner \
        --no-acl \
        | gzip > "${SAFETY_BACKUP}"

    # Move safety backup to backups directory
    mkdir -p ./backups
    mv "${SAFETY_BACKUP}" ./backups/
    SAFETY_BACKUP="./backups/$(basename ${SAFETY_BACKUP})"

    success "Safety backup created: ${SAFETY_BACKUP}"
    log "You can rollback with: bash scripts/restore-database.sh --force ${SAFETY_BACKUP}"
    echo ""
fi

# Confirmation prompt (unless forced)
if [ "$FORCE" = false ]; then
    read -p "Type 'yes' to continue with restore: " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        log "Restore cancelled by user"
        exit 0
    fi
fi

# Perform restore
log "Starting database restore..."
log "This may take a few minutes..."

# Stop web and celery containers to prevent connections during restore
log "Stopping web and celery containers..."
docker compose -f docker-compose.yml stop web celery 2>/dev/null || true

# Terminate existing connections
log "Terminating existing database connections..."
docker compose -f docker-compose.yml exec -T db psql -U postgres -d postgres -c "
    SELECT pg_terminate_backend(pid)
    FROM pg_stat_activity
    WHERE datname = '${DB_NAME}' AND pid <> pg_backend_pid();
" > /dev/null 2>&1 || true

# Drop and recreate database
log "Dropping existing database..."
docker compose -f docker-compose.yml exec -T db psql -U postgres -d postgres -c "DROP DATABASE IF EXISTS ${DB_NAME};" > /dev/null 2>&1

log "Creating fresh database..."
docker compose -f docker-compose.yml exec -T db psql -U postgres -d postgres -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};" > /dev/null 2>&1

# Restore from backup
log "Restoring from backup..."
if [[ "${BACKUP_FILE}" == *.gz ]]; then
    gunzip -c "${BACKUP_FILE}" | docker compose -f docker-compose.yml exec -T db psql -U "${DB_USER}" -d "${DB_NAME}" > /dev/null 2>&1
else
    docker compose -f docker-compose.yml exec -T db psql -U "${DB_USER}" -d "${DB_NAME}" < "${BACKUP_FILE}" > /dev/null 2>&1
fi

success "Database restored successfully!"

# Restart web and celery
log "Restarting web and celery containers..."
docker compose -f docker-compose.yml start web celery

# Verify restore
if [ "$VERIFY" = true ]; then
    log "Verifying restored database..."

    # Wait for database to be ready
    sleep 5

    RESTORED_DEBATES=$(docker compose -f docker-compose.yml exec -T db psql -U "${DB_USER}" -d "${DB_NAME}" -t -c "SELECT COUNT(*) FROM debates_debate;" 2>/dev/null | xargs || echo "0")
    RESTORED_PERSONAS=$(docker compose -f docker-compose.yml exec -T db psql -U "${DB_USER}" -d "${DB_NAME}" -t -c "SELECT COUNT(*) FROM personas_persona;" 2>/dev/null | xargs || echo "0")
    RESTORED_USERS=$(docker compose -f docker-compose.yml exec -T db psql -U "${DB_USER}" -d "${DB_NAME}" -t -c "SELECT COUNT(*) FROM users_user;" 2>/dev/null | xargs || echo "0")

    log "Restored database contents:"
    log "  - Debates: ${RESTORED_DEBATES}"
    log "  - Personas: ${RESTORED_PERSONAS}"
    log "  - Users: ${RESTORED_USERS}"

    if [ ${RESTORED_DEBATES} -eq 0 ] && [ ${RESTORED_PERSONAS} -eq 0 ] && [ ${RESTORED_USERS} -eq 0 ]; then
        warning "Restored database appears empty. Backup may have been empty."
    else
        success "Database verification passed"
    fi
fi

# Summary
echo ""
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
success "Restore completed successfully!"
log "Database: ${DB_NAME}"
log "Restored from: ${BACKUP_FILE}"
if [ "$NO_BACKUP" = false ]; then
    log "Safety backup: ${SAFETY_BACKUP}"
fi
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test database health
log "Testing database health..."
if curl -f http://localhost:8001/health/ > /dev/null 2>&1; then
    success "Application is healthy"
else
    warning "Application health check failed (may need a few seconds to start)"
fi

log "Restore process complete!"

exit 0
