# Prompt the Past - Development Makefile
# Usage: make [target]
# Run 'make help' to see all available commands

.PHONY: help

# Colors for terminal output
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

# Directories
BACKEND_DIR := backend
FRONTEND_DIR := frontend

# Port configuration (override with: make start FRONTEND_PORT=3002)
FRONTEND_PORT ?= 3001

help: ## Show this help message
	@echo "$(BLUE)Prompt the Past - Development Commands$(RESET)"
	@echo ""
	@echo "$(GREEN)Usage:$(RESET) make [target]"
	@echo ""
	@echo "$(YELLOW)Available targets:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-25s$(RESET) %s\n", $$1, $$2}'
	@echo ""

# ============================================================================
# 🚀 Quick Start
# ============================================================================

.PHONY: start stop restart status

start: ## Start all services (backend + frontend)
	@echo "$(GREEN)Starting all services...$(RESET)"
	@$(MAKE) backend-start
	@echo "$(GREEN)Waiting for backend to be ready...$(RESET)"
	@sleep 5
	@$(MAKE) frontend-dev &
	@echo "$(GREEN)✓ All services started!$(RESET)"
	@echo "$(BLUE)Backend:$(RESET)  http://localhost"
	@echo "$(BLUE)Frontend:$(RESET) http://localhost:$(FRONTEND_PORT)"
	@echo "$(BLUE)Flower:$(RESET)   http://localhost:5555"

stop: ## Stop all services
	@echo "$(YELLOW)Stopping all services...$(RESET)"
	@$(MAKE) backend-stop
	@$(MAKE) frontend-stop
	@echo "$(GREEN)✓ All services stopped$(RESET)"

restart: ## Restart all services
	@echo "$(YELLOW)Restarting all services...$(RESET)"
	@$(MAKE) stop
	@sleep 2
	@$(MAKE) start

status: ## Check status of all services
	@echo "$(BLUE)Backend Services:$(RESET)"
	@cd $(BACKEND_DIR) && docker compose ps
	@echo ""
	@echo "$(BLUE)Frontend Status (port $(FRONTEND_PORT)):$(RESET)"
	@lsof -ti:$(FRONTEND_PORT) > /dev/null 2>&1 && echo "$(GREEN)✓ Running on port $(FRONTEND_PORT)$(RESET)" || echo "$(RED)✗ Not running$(RESET)"

# ============================================================================
# 🐳 Backend (Django + Docker)
# ============================================================================

.PHONY: backend-build backend-start backend-stop backend-restart backend-logs backend-shell backend-exec

backend-build: ## Build backend Docker images
	@echo "$(BLUE)Building backend Docker images...$(RESET)"
	@cd $(BACKEND_DIR) && docker compose build
	@echo "$(GREEN)✓ Backend built successfully$(RESET)"

backend-start: ## Start backend services
	@echo "$(BLUE)Starting backend services...$(RESET)"
	@cd $(BACKEND_DIR) && docker compose up -d
	@echo "$(GREEN)✓ Backend started$(RESET)"

backend-stop: ## Stop backend services
	@echo "$(YELLOW)Stopping backend services...$(RESET)"
	@cd $(BACKEND_DIR) && docker compose down
	@echo "$(GREEN)✓ Backend stopped$(RESET)"

backend-restart: ## Restart backend services
	@echo "$(YELLOW)Restarting backend...$(RESET)"
	@cd $(BACKEND_DIR) && docker compose restart
	@echo "$(GREEN)✓ Backend restarted$(RESET)"

backend-logs: ## View backend logs (use 'make backend-logs s=web' for specific service)
	@cd $(BACKEND_DIR) && docker compose logs -f $(s)

backend-shell: ## Open Django shell
	@cd $(BACKEND_DIR) && docker compose exec web python manage.py shell_plus

backend-exec: ## Execute command in web container (use: make backend-exec cmd="your command")
	@cd $(BACKEND_DIR) && docker compose exec web $(cmd)

# ============================================================================
# 💾 Database Operations
# ============================================================================

.PHONY: db-migrate db-makemigrations db-shell db-backup db-restore db-reset

db-migrate: ## Run database migrations
	@echo "$(BLUE)Running migrations...$(RESET)"
	@cd $(BACKEND_DIR) && docker compose exec web python manage.py migrate
	@echo "$(GREEN)✓ Migrations complete$(RESET)"

db-makemigrations: ## Create new migrations
	@echo "$(BLUE)Creating migrations...$(RESET)"
	@cd $(BACKEND_DIR) && docker compose exec web python manage.py makemigrations
	@echo "$(GREEN)✓ Migrations created$(RESET)"

db-shell: ## Open PostgreSQL shell
	@cd $(BACKEND_DIR) && docker compose exec db psql -U debatesuser -d debates

db-backup: ## Backup database to file
	@echo "$(BLUE)Backing up database...$(RESET)"
	@cd $(BACKEND_DIR) && docker compose exec db pg_dump -U debatesuser debates > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✓ Database backed up$(RESET)"

db-restore: ## Restore database from backup (use: make db-restore file=backup.sql)
	@echo "$(YELLOW)Restoring database from $(file)...$(RESET)"
	@cd $(BACKEND_DIR) && docker compose exec -T db psql -U debatesuser -d debates < $(file)
	@echo "$(GREEN)✓ Database restored$(RESET)"

db-reset: ## Reset database (WARNING: Deletes all data!)
	@echo "$(RED)⚠️  WARNING: This will delete all data!$(RESET)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		cd $(BACKEND_DIR) && docker compose down -v && docker compose up -d db && sleep 3 && docker compose exec web python manage.py migrate; \
		echo "$(GREEN)✓ Database reset complete$(RESET)"; \
	else \
		echo "$(YELLOW)Cancelled$(RESET)"; \
	fi

# ============================================================================
# 🧪 Testing
# ============================================================================

.PHONY: test test-backend test-frontend test-coverage test-backend-coverage test-frontend-coverage

test: ## Run all tests (backend + frontend)
	@echo "$(BLUE)Running all tests...$(RESET)"
	@$(MAKE) test-backend
	@$(MAKE) test-frontend
	@echo "$(GREEN)✓ All tests complete$(RESET)"

test-backend: ## Run backend tests
	@echo "$(BLUE)Running backend tests...$(RESET)"
	@cd $(BACKEND_DIR) && docker compose exec web pytest -q
	@echo "$(GREEN)✓ Backend tests complete$(RESET)"

test-frontend: ## Run frontend tests
	@echo "$(BLUE)Running frontend tests...$(RESET)"
	@cd $(FRONTEND_DIR) && npm test -- --run
	@echo "$(GREEN)✓ Frontend tests complete$(RESET)"

test-coverage: ## Run all tests with coverage
	@$(MAKE) test-backend-coverage
	@$(MAKE) test-frontend-coverage

test-backend-coverage: ## Run backend tests with coverage report
	@echo "$(BLUE)Running backend tests with coverage...$(RESET)"
	@cd $(BACKEND_DIR) && docker compose exec web pytest --cov --cov-report=term --cov-report=html
	@echo "$(GREEN)✓ Coverage report generated at backend/htmlcov/index.html$(RESET)"

test-frontend-coverage: ## Run frontend tests with coverage report
	@echo "$(BLUE)Running frontend tests with coverage...$(RESET)"
	@cd $(FRONTEND_DIR) && npm run test:coverage
	@echo "$(GREEN)✓ Coverage report generated at frontend/coverage/index.html$(RESET)"

test-watch: ## Run backend tests in watch mode
	@cd $(BACKEND_DIR) && docker compose exec web pytest --watch

# ============================================================================
# 🎨 Code Quality
# ============================================================================

.PHONY: lint lint-backend lint-frontend format format-backend format-frontend

lint: ## Run linters on all code
	@$(MAKE) lint-backend
	@$(MAKE) lint-frontend

lint-backend: ## Lint backend Python code
	@echo "$(BLUE)Linting backend...$(RESET)"
	@cd $(BACKEND_DIR) && docker compose exec web flake8 . || true
	@echo "$(GREEN)✓ Backend linting complete$(RESET)"

lint-frontend: ## Lint frontend TypeScript code
	@echo "$(BLUE)Linting frontend...$(RESET)"
	@cd $(FRONTEND_DIR) && npm run lint
	@echo "$(GREEN)✓ Frontend linting complete$(RESET)"

format-backend: ## Format backend Python code (if Black is installed)
	@echo "$(BLUE)Formatting backend code...$(RESET)"
	@cd $(BACKEND_DIR) && docker compose exec web black . || echo "$(YELLOW)Black not installed - skipping$(RESET)"

format-frontend: ## Format frontend TypeScript code
	@echo "$(BLUE)Formatting frontend code...$(RESET)"
	@cd $(FRONTEND_DIR) && npm run format || echo "$(YELLOW)Format script not configured$(RESET)"

# ============================================================================
# 📦 Frontend Operations
# ============================================================================

.PHONY: frontend-dev frontend-stop frontend-build frontend-install frontend-clean

frontend-dev: ## Start frontend development server
	@echo "$(BLUE)Starting frontend dev server on port $(FRONTEND_PORT)...$(RESET)"
	@cd $(FRONTEND_DIR) && npx next dev --turbopack -p $(FRONTEND_PORT)

frontend-stop: ## Stop frontend development server
	@echo "$(YELLOW)Stopping frontend on port $(FRONTEND_PORT)...$(RESET)"
	@lsof -ti:$(FRONTEND_PORT) | xargs kill -9 2>/dev/null || echo "$(YELLOW)No process found on port $(FRONTEND_PORT)$(RESET)"
	@echo "$(GREEN)✓ Frontend stopped$(RESET)"

frontend-build: ## Build frontend for production
	@echo "$(BLUE)Building frontend...$(RESET)"
	@cd $(FRONTEND_DIR) && npm run build
	@echo "$(GREEN)✓ Frontend built$(RESET)"

frontend-install: ## Install frontend dependencies
	@echo "$(BLUE)Installing frontend dependencies...$(RESET)"
	@cd $(FRONTEND_DIR) && npm install
	@echo "$(GREEN)✓ Dependencies installed$(RESET)"

frontend-clean: ## Clean frontend build artifacts
	@echo "$(YELLOW)Cleaning frontend...$(RESET)"
	@cd $(FRONTEND_DIR) && rm -rf .next node_modules/.cache
	@echo "$(GREEN)✓ Frontend cleaned$(RESET)"

# ============================================================================
# 🧹 Cleanup
# ============================================================================

.PHONY: clean clean-backend clean-frontend clean-all clean-docker

clean: ## Clean build artifacts (backend + frontend)
	@$(MAKE) clean-backend
	@$(MAKE) clean-frontend

clean-backend: ## Clean backend build artifacts
	@echo "$(YELLOW)Cleaning backend...$(RESET)"
	@cd $(BACKEND_DIR) && find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@cd $(BACKEND_DIR) && find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@cd $(BACKEND_DIR) && rm -rf .pytest_cache htmlcov .coverage coverage.xml 2>/dev/null || true
	@echo "$(GREEN)✓ Backend cleaned$(RESET)"

clean-frontend: ## Clean frontend build artifacts
	@echo "$(YELLOW)Cleaning frontend...$(RESET)"
	@cd $(FRONTEND_DIR) && rm -rf .next node_modules/.cache coverage 2>/dev/null || true
	@echo "$(GREEN)✓ Frontend cleaned$(RESET)"

clean-all: ## Clean everything including Docker volumes
	@echo "$(RED)⚠️  WARNING: This will delete all Docker volumes!$(RESET)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(MAKE) clean; \
		cd $(BACKEND_DIR) && docker compose down -v; \
		echo "$(GREEN)✓ Everything cleaned$(RESET)"; \
	else \
		echo "$(YELLOW)Cancelled$(RESET)"; \
	fi

clean-docker: ## Remove all stopped containers and unused images
	@echo "$(YELLOW)Cleaning Docker resources...$(RESET)"
	@docker system prune -f
	@echo "$(GREEN)✓ Docker cleaned$(RESET)"

# ============================================================================
# 🔧 Development Utilities
# ============================================================================

.PHONY: health create-superuser load-fixtures shell-plus

health: ## Check health of all services
	@echo "$(BLUE)Backend Health:$(RESET)"
	@curl -s http://localhost/health/ | jq . || echo "$(RED)Backend not responding$(RESET)"
	@echo ""
	@echo "$(BLUE)Backend Ready:$(RESET)"
	@curl -s http://localhost/ready/ | jq . || echo "$(RED)Backend not ready$(RESET)"

create-superuser: ## Create Django superuser
	@cd $(BACKEND_DIR) && docker compose exec web python manage.py createsuperuser

load-fixtures: ## Load persona fixtures
	@echo "$(BLUE)Loading persona fixtures...$(RESET)"
	@cd $(BACKEND_DIR) && docker compose exec web python manage.py load_personas
	@echo "$(GREEN)✓ Fixtures loaded$(RESET)"

shell-plus: ## Open enhanced Django shell with all models loaded
	@cd $(BACKEND_DIR) && docker compose exec web python manage.py shell_plus

# ============================================================================
# 📊 Monitoring
# ============================================================================

.PHONY: flower celery-logs redis-cli

flower: ## Open Celery Flower monitoring UI
	@echo "$(BLUE)Opening Flower at http://localhost:5555$(RESET)"
	@open http://localhost:5555 || xdg-open http://localhost:5555 || echo "Open http://localhost:5555 in your browser"

celery-logs: ## View Celery worker logs
	@cd $(BACKEND_DIR) && docker compose logs -f celery

redis-cli: ## Open Redis CLI
	@cd $(BACKEND_DIR) && docker compose exec redis redis-cli

# ============================================================================
# 🚢 Production Build
# ============================================================================

.PHONY: build-prod deploy-check

build-prod: ## Build for production (no cache)
	@echo "$(BLUE)Building production images...$(RESET)"
	@cd $(BACKEND_DIR) && docker compose build --no-cache
	@cd $(FRONTEND_DIR) && npm run build
	@echo "$(GREEN)✓ Production build complete$(RESET)"

deploy-check: ## Run pre-deployment checks
	@echo "$(BLUE)Running deployment checks...$(RESET)"
	@echo "$(BLUE)1. Testing backend...$(RESET)"
	@cd $(BACKEND_DIR) && docker compose exec web pytest -q --tb=no
	@echo "$(BLUE)2. Checking migrations...$(RESET)"
	@cd $(BACKEND_DIR) && docker compose exec web python manage.py showmigrations | grep "\[ \]" && echo "$(RED)⚠️ Unapplied migrations found$(RESET)" || echo "$(GREEN)✓ All migrations applied$(RESET)"
	@echo "$(BLUE)3. Checking security...$(RESET)"
	@cd $(BACKEND_DIR) && docker compose exec web python manage.py check --deploy || true
	@echo "$(GREEN)✓ Deployment checks complete$(RESET)"

# ============================================================================
# 📝 Documentation
# ============================================================================

.PHONY: docs coverage-report

docs: ## Open project documentation
	@echo "$(BLUE)Opening documentation...$(RESET)"
	@open README.md || echo "See README.md for documentation"

coverage-report: ## Open coverage reports in browser
	@echo "$(BLUE)Opening coverage reports...$(RESET)"
	@open backend/htmlcov/index.html || echo "Run 'make test-backend-coverage' first"
	@open frontend/coverage/index.html || echo "Run 'make test-frontend-coverage' first"
