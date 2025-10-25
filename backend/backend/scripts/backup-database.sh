#!/bin/bash
set -e

# PostgreSQL Database Backup Script
# Creates timestamped backups and maintains 7-day retention

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
DB_NAME="${DB_NAME:-debates}"
DB_USER="${DB_USER:-debatesuser}"
DB_HOST="${DB_HOST:-db}"
RETENTION_DAYS=${RETENTION_DAYS:-7}

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Generate timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/debates_backup_$TIMESTAMP.sql"

echo "==================================="
echo "PostgreSQL Database Backup"
echo "==================================="
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo "Host: $DB_HOST"
echo "Backup file: $BACKUP_FILE"
echo "-----------------------------------"

# Create backup using pg_dump
echo "Creating backup..."
docker compose exec -T db pg_dump -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    # Compress the backup
    echo "Compressing backup..."
    gzip "$BACKUP_FILE"
    BACKUP_FILE="$BACKUP_FILE.gz"

    # Get file size
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)

    echo "✅ Backup created successfully!"
    echo "   File: $BACKUP_FILE"
    echo "   Size: $SIZE"
else
    echo "❌ Backup failed!"
    exit 1
fi

# Clean up old backups (keep last RETENTION_DAYS days)
echo "-----------------------------------"
echo "Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "debates_backup_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete

# List remaining backups
echo "-----------------------------------"
echo "Current backups:"
ls -lh "$BACKUP_DIR"/debates_backup_*.sql.gz 2>/dev/null || echo "  (no backups found)"

echo "==================================="
echo "Backup completed at $(date)"
echo "==================================="
