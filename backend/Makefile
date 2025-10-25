.PHONY: help backup-s3 backup-s3-monthly restore-s3 test-backup

help:
	@echo "Available commands:"
	@echo "  make backup-s3          - Create daily S3 backup"
	@echo "  make backup-s3-monthly  - Create monthly S3 backup"
	@echo "  make restore-s3         - Restore from S3 backup (interactive)"
	@echo "  make test-backup        - Test backup integrity"

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
