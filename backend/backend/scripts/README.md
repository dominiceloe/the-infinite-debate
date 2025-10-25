# Database Backup and Restore Scripts

## Overview

Automated backup scripts for the PostgreSQL database with 7-day retention.

## Manual Backup

Create a backup manually:

```bash
# From backend directory
make backup

# Or run script directly
./scripts/backup-database.sh
```

Backups are saved to `backend/backups/` with format: `debates_backup_YYYYMMDD_HHMMSS.sql.gz`

## Manual Restore

Restore from a backup:

```bash
# From backend directory
make restore

# Or run script directly
./scripts/restore-database.sh backups/debates_backup_20251025_120000.sql.gz
```

## Automated Daily Backups

### Setup Cron Job (macOS/Linux)

1. Open crontab editor:
   ```bash
   crontab -e
   ```

2. Add this line to run daily at 3 AM:
   ```bash
   0 3 * * * ./scripts/backup-database.sh >> logs/backup.log 2>&1
   ```

3. Save and exit. Verify with:
   ```bash
   crontab -l
   ```

### Backup Retention

- Backups are automatically deleted after 7 days
- Change retention by setting `RETENTION_DAYS` environment variable
- Example: `RETENTION_DAYS=30 ./scripts/backup-database.sh`

## Configuration

Environment variables (optional):

- `BACKUP_DIR` - Backup directory (default: `./backups`)
- `DB_NAME` - Database name (default: `debates`)
- `DB_USER` - Database user (default: `debatesuser`)
- `DB_HOST` - Database host (default: `db`)
- `RETENTION_DAYS` - Backup retention in days (default: `7`)

## Backup to External Drive

Backup to an external drive:

```bash
BACKUP_DIR=/Volumes/MyDrive/debates_backups ./scripts/backup-database.sh
```

## Testing the Backup System

1. Create a backup:
   ```bash
   make backup
   ```

2. Make some database changes

3. Restore from backup:
   ```bash
   make restore
   ```

4. Verify data is restored correctly

## Security Notes

- Backups are **NOT encrypted** by default
- Store backups on encrypted drives if they contain sensitive data
- Limit access to backup directory: `chmod 700 backups/`
- For production, consider:
  - Encrypting backups with `gpg`
  - Storing backups off-site (AWS S3, etc.)
  - Implementing backup monitoring

## Troubleshooting

**"Backup failed"**
- Ensure Docker containers are running: `docker compose ps`
- Check database is accessible: `make db-shell`

**"Permission denied"**
- Make scripts executable: `chmod +x scripts/*.sh`

**"No space left on device"**
- Clean old backups manually: `rm backups/debates_backup_*.sql.gz`
- Reduce `RETENTION_DAYS`
