#!/bin/bash
set -e

# PostgreSQL Database Restore Script
# Restores database from a backup file

# Check if backup file is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    echo ""
    echo "Available backups:"
    ls -lh backups/debates_backup_*.sql.gz 2>/dev/null || echo "  (no backups found)"
    exit 1
fi

BACKUP_FILE="$1"

# Check if file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Configuration
DB_NAME="${DB_NAME:-debates}"
DB_USER="${DB_USER:-debatesuser}"
DB_HOST="${DB_HOST:-db}"

echo "==================================="
echo "PostgreSQL Database Restore"
echo "==================================="
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo "Host: $DB_HOST"
echo "Backup file: $BACKUP_FILE"
echo "-----------------------------------"

# Confirm restoration
read -p "⚠️  WARNING: This will REPLACE the current database. Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled."
    exit 0
fi

# Decompress if needed
if [[ $BACKUP_FILE == *.gz ]]; then
    echo "Decompressing backup..."
    TEMP_FILE=$(mktemp)
    gunzip -c "$BACKUP_FILE" > "$TEMP_FILE"
    SQL_FILE="$TEMP_FILE"
else
    SQL_FILE="$BACKUP_FILE"
fi

# Restore database
echo "Restoring database..."
cat "$SQL_FILE" | docker compose exec -T db psql -U "$DB_USER" -d "$DB_NAME"

if [ $? -eq 0 ]; then
    echo "✅ Database restored successfully!"
else
    echo "❌ Restore failed!"
    exit 1
fi

# Clean up temp file
if [ -n "$TEMP_FILE" ]; then
    rm -f "$TEMP_FILE"
fi

echo "==================================="
echo "Restore completed at $(date)"
echo "==================================="
