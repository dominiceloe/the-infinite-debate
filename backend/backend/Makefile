.PHONY: help backup restore test start stop status logs

help:
	@echo "Available commands:"
	@echo "  make start          - Start all Docker containers"
	@echo "  make stop           - Stop all Docker containers"
	@echo "  make restart        - Restart all Docker containers"
	@echo "  make status         - Show container status"
	@echo "  make logs           - Show container logs"
	@echo "  make test           - Run pytest tests"
	@echo "  make test-coverage  - Run tests with coverage report"
	@echo "  make backup         - Create database backup"
	@echo "  make restore        - Restore database from backup"
	@echo "  make db-migrate     - Run database migrations"
	@echo "  make db-shell       - Open PostgreSQL shell"
	@echo "  make shell          - Open Django shell"
	@echo "  make load-personas  - Load persona fixtures to database"

# Docker management
start:
	docker compose up -d

stop:
	docker compose stop

restart: stop start

status:
	docker compose ps

logs:
	docker compose logs -f

# Database operations
backup:
	@echo "Creating database backup..."
	./scripts/backup-database.sh

restore:
	@echo "Available backups:"
	@ls -lh backups/debates_backup_*.sql.gz 2>/dev/null || echo "  (no backups found)"
	@echo ""
	@read -p "Enter backup filename: " filename; \
	./scripts/restore-database.sh $$filename

db-migrate:
	docker compose exec web python manage.py migrate

db-shell:
	docker compose exec db psql -U debatesuser -d debates

shell:
	docker compose exec web python manage.py shell_plus

# Testing
test:
	docker compose exec web pytest -v

test-coverage:
	docker compose exec web pytest --cov --cov-report=term-missing --cov-report=html

# Persona management
load-personas:
	docker compose exec web python manage.py load_personas
