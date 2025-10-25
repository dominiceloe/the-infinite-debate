# Makefile Quick Reference

This project includes a comprehensive Makefile to simplify common development tasks.

## Quick Start

```bash
make help              # Show all available commands
make start             # Start backend + frontend
make test-coverage     # Run all tests with coverage
make status            # Check service status
```

## 🚀 Common Commands

### Start/Stop Services

```bash
make start             # Start all services (backend + frontend)
make stop              # Stop all services
make restart           # Restart all services
make status            # Check status of running services
```

### Backend Operations

```bash
make backend-build     # Build Docker images
make backend-start     # Start backend only
make backend-stop      # Stop backend
make backend-restart   # Restart backend
make backend-logs      # View all logs
make backend-logs s=web      # View specific service logs
make backend-logs s=celery   # View Celery logs
```

### Database Operations

```bash
make db-migrate              # Run migrations
make db-makemigrations       # Create new migrations
make db-shell                # Open PostgreSQL shell
make db-backup               # Backup database (timestamped)
make db-restore file=backup.sql   # Restore from backup
make db-reset                # Reset database (with confirmation)
```

### Testing

```bash
make test                    # Run all tests
make test-backend            # Backend tests only
make test-frontend           # Frontend tests only
make test-coverage           # All tests with coverage
make test-backend-coverage   # Backend coverage + HTML report
make test-frontend-coverage  # Frontend coverage + HTML report
make test-watch              # Watch mode for backend tests
```

### Code Quality

```bash
make lint                    # Lint all code
make lint-backend            # Lint Python code
make lint-frontend           # Lint TypeScript code
make format-backend          # Format Python with Black
make format-frontend         # Format TypeScript
```

### Frontend Operations

```bash
make frontend-dev            # Start dev server
make frontend-stop           # Stop frontend dev server
make frontend-build          # Build for production
make frontend-install        # Install dependencies
make frontend-clean          # Clean build artifacts
```

### Cleanup

```bash
make clean                   # Clean build artifacts
make clean-backend           # Clean backend only
make clean-frontend          # Clean frontend only
make clean-all               # Clean everything (with confirmation)
make clean-docker            # Prune Docker resources
```

### Development Utilities

```bash
make health                  # Check API health endpoints
make create-superuser        # Create Django admin user
make load-fixtures           # Load persona fixtures
make shell-plus              # Django shell with models loaded
make backend-shell           # Standard Django shell
```

### Monitoring

```bash
make flower                  # Open Celery Flower UI
make celery-logs             # View Celery worker logs
make redis-cli               # Open Redis CLI
```

### Production

```bash
make build-prod              # Build production images (no cache)
make deploy-check            # Run pre-deployment checks
```

### Documentation

```bash
make docs                    # Open project documentation
make coverage-report         # Open coverage reports in browser
```

## 📝 Advanced Usage

### Execute Custom Commands

```bash
# Run arbitrary command in web container
make backend-exec cmd="python manage.py shell"
make backend-exec cmd="pytest debates/tests/test_models.py -v"
```

### View Specific Service Logs

```bash
make backend-logs s=web      # Web container
make backend-logs s=celery   # Celery worker
make backend-logs s=db       # PostgreSQL
make backend-logs s=redis    # Redis
```

### Database Backup & Restore

```bash
# Backup with timestamp
make db-backup
# Creates: backup_20251019_123456.sql

# Restore from specific backup
make db-restore file=backup_20251019_123456.sql
```

## 🎯 Common Workflows

### Daily Development

```bash
# Morning startup
make start

# Check everything is running
make status

# View logs if needed
make backend-logs

# Run tests before committing
make test

# End of day
make stop
```

### After Pulling Changes

```bash
# Rebuild containers (if Dockerfile changed)
make backend-build

# Run new migrations
make db-migrate

# Restart services
make restart

# Verify with tests
make test
```

### Testing Workflow

```bash
# Quick test run
make test-backend

# Full coverage report
make test-coverage

# Open coverage reports in browser
make coverage-report

# Watch mode for TDD
make test-watch
```

### Database Management

```bash
# Create migration after model changes
make db-makemigrations

# Apply migrations
make db-migrate

# Backup before risky operations
make db-backup

# Reset if things go wrong
make db-reset
```

### Pre-Deployment

```bash
# Clean everything
make clean

# Build production images
make build-prod

# Run deployment checks
make deploy-check

# Run full test suite
make test-coverage
```

## 🔍 Troubleshooting

### Services Won't Start

```bash
# Check status
make status

# View logs
make backend-logs

# Clean and restart
make clean-all
make start
```

### Database Issues

```bash
# Check database connection
make db-shell

# Reset database (nuclear option)
make db-reset
```

### Docker Issues

```bash
# Rebuild images
make backend-build

# Clean Docker resources
make clean-docker

# Full restart
docker compose down -v
make start
```

### Tests Failing

```bash
# Clean test artifacts
make clean-backend

# Rebuild and test
make backend-build
make test-backend
```

## 💡 Tips

1. **Use tab completion**: Type `make` and press Tab twice to see all targets
2. **Chain commands**: `make clean && make test`
3. **Background processes**: `make frontend-dev &` to run in background
4. **Check help**: `make help` shows all commands with descriptions
5. **Service-specific logs**: `make backend-logs s=SERVICE_NAME`

## 🎨 Color Output

The Makefile uses colored output for better readability:
- 🔵 **Blue**: Information and commands
- 🟢 **Green**: Success messages
- 🟡 **Yellow**: Warnings
- 🔴 **Red**: Errors and destructive operations

## 📚 Related Documentation

- `README.md` - Project overview
- `NEXT_STEPS.md` - Development roadmap
- `backend/STATUS.md` - Backend status and testing
- `backend/TESTING.md` - Testing guide
