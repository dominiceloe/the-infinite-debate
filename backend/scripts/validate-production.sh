#!/usr/bin/env bash
#
# Production Deployment Validation Script
# ========================================
#
# Run this script BEFORE deploying to production to catch misconfigurations.
# This prevents common deployment issues and ensures production-readiness.
#
# Usage:
#   bash scripts/validate-production.sh
#
# Exit Codes:
#   0 - All validations passed, safe to deploy
#   1 - Critical failure, DO NOT deploy
#
# What this script checks:
# - Environment variables are set correctly
# - DEBUG mode is disabled
# - Secret keys are production-grade
# - Database connectivity
# - Redis connectivity
# - SSL certificates are valid
# - Required files exist
# - Docker images are built
# - Migrations are ready

set -e  # Exit on any error

# Color output for readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track validation status
ERRORS=0
WARNINGS=0

# Helper functions
error() {
    echo -e "${RED}❌ ERROR: $1${NC}"
    ERRORS=$((ERRORS + 1))
}

warning() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
    WARNINGS=$((WARNINGS + 1))
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Main validation script
main() {
    header "🚀 Production Deployment Validation"
    info "Starting pre-deployment checks..."
    echo ""

    # 1. Check environment file exists
    header "1️⃣  Environment Configuration"
    if [ ! -f ".env" ]; then
        error ".env file not found. Copy .env.example and configure for production."
        return 1
    fi
    success ".env file exists"

    # Load environment variables
    set -a
    source .env
    set +a

    # 2. Validate DEBUG is False
    header "2️⃣  Debug Mode Check"
    if [ "${DEBUG:-True}" = "True" ] || [ "${DEBUG:-True}" = "true" ]; then
        error "DEBUG=True detected! This MUST be False in production."
        error "Security risk: Exposes sensitive information and stack traces."
    else
        success "DEBUG=False (production mode enabled)"
    fi

    # 3. Validate Django secret key
    header "3️⃣  Secret Key Validation"
    if [ -z "${SECRET_KEY}" ]; then
        error "SECRET_KEY not set in .env"
    elif [ "${SECRET_KEY}" = "django-insecure-dev-key-change-in-production" ]; then
        error "SECRET_KEY is using default development value! Generate a new one."
        info "Generate with: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'"
    elif [ ${#SECRET_KEY} -lt 50 ]; then
        warning "SECRET_KEY is too short (${#SECRET_KEY} chars). Recommended: 50+ chars."
    else
        success "SECRET_KEY is set and looks secure (${#SECRET_KEY} chars)"
    fi

    # 4. Validate ALLOWED_HOSTS
    header "4️⃣  Allowed Hosts Configuration"
    if [ -z "${ALLOWED_HOSTS}" ]; then
        error "ALLOWED_HOSTS not set. Django will reject all requests."
        info "Set to your domain: ALLOWED_HOSTS=api.theinfinitedebate.com"
    elif [[ "${ALLOWED_HOSTS}" == *"localhost"* ]] && [[ "${ALLOWED_HOSTS}" != *".com"* ]]; then
        warning "ALLOWED_HOSTS contains only localhost. Add production domain."
    else
        success "ALLOWED_HOSTS configured: ${ALLOWED_HOSTS}"
    fi

    # 5. Validate database settings
    header "5️⃣  Database Configuration"
    if [ -z "${DB_NAME}" ] || [ -z "${DB_USER}" ] || [ -z "${DB_PASSWORD}" ]; then
        error "Database credentials incomplete (DB_NAME, DB_USER, DB_PASSWORD required)"
    else
        success "Database credentials configured"
    fi

    # Test database connectivity
    info "Testing database connection..."
    if docker compose -f docker-compose.yml ps db | grep -q "Up"; then
        if docker compose -f docker-compose.yml exec -T db pg_isready -U "${DB_USER}" > /dev/null 2>&1; then
            success "Database is reachable and ready"
        else
            error "Database is running but not accepting connections"
        fi
    else
        warning "Database container not running (start with docker compose up -d)"
    fi

    # 6. Validate Redis
    header "6️⃣  Redis Configuration"
    if [ -z "${REDIS_URL}" ]; then
        error "REDIS_URL not set"
    else
        success "REDIS_URL configured: ${REDIS_URL}"
    fi

    # Test Redis connectivity
    info "Testing Redis connection..."
    if docker compose -f docker-compose.yml ps redis | grep -q "Up"; then
        if docker compose -f docker-compose.yml exec -T redis redis-cli ping > /dev/null 2>&1; then
            success "Redis is reachable and responding"
        else
            error "Redis is running but not responding to ping"
        fi
    else
        warning "Redis container not running (start with docker compose up -d)"
    fi

    # 7. Validate API keys
    header "7️⃣  API Keys Validation"

    # Anthropic API
    if [ -z "${ANTHROPIC_API_KEY}" ]; then
        error "ANTHROPIC_API_KEY not set (required for debate generation)"
    elif [ "${ANTHROPIC_API_KEY}" = "sk-ant-your-key-here" ]; then
        error "ANTHROPIC_API_KEY is placeholder value. Set real API key."
    else
        success "ANTHROPIC_API_KEY configured"
    fi

    # Stripe keys
    if [ -z "${STRIPE_SECRET_KEY}" ]; then
        error "STRIPE_SECRET_KEY not set (required for payments)"
    elif [[ "${STRIPE_SECRET_KEY}" == sk_test_* ]]; then
        warning "STRIPE_SECRET_KEY is test key (sk_test_*). Use live key (sk_live_*) for production."
    else
        success "STRIPE_SECRET_KEY configured (live mode)"
    fi

    if [ -z "${STRIPE_WEBHOOK_SECRET}" ]; then
        error "STRIPE_WEBHOOK_SECRET not set (required for webhook validation)"
    else
        success "STRIPE_WEBHOOK_SECRET configured"
    fi

    # 8. Validate CORS settings
    header "8️⃣  CORS Configuration"
    if [ -z "${CORS_ALLOWED_ORIGINS}" ]; then
        warning "CORS_ALLOWED_ORIGINS not set. Frontend may not be able to connect."
        info "Set to: CORS_ALLOWED_ORIGINS=https://theinfinitedebate.com"
    elif [[ "${CORS_ALLOWED_ORIGINS}" == *"localhost"* ]]; then
        warning "CORS_ALLOWED_ORIGINS includes localhost. Remove for production."
    else
        success "CORS_ALLOWED_ORIGINS configured for production"
    fi

    # 9. Check SSL certificates (if using HTTPS)
    header "9️⃣  SSL Certificate Check"
    if [ -d "certbot_conf/live" ] && [ -n "$(ls -A certbot_conf/live 2>/dev/null)" ]; then
        success "SSL certificates found in certbot_conf/live/"

        # Check certificate expiry
        CERT_PATH=$(find certbot_conf/live -name "cert.pem" | head -n 1)
        if [ -n "${CERT_PATH}" ]; then
            EXPIRY=$(openssl x509 -enddate -noout -in "${CERT_PATH}" 2>/dev/null | cut -d= -f2)
            if [ -n "${EXPIRY}" ]; then
                info "Certificate expires: ${EXPIRY}"

                # Warn if expiring soon (within 30 days)
                EXPIRY_EPOCH=$(date -d "${EXPIRY}" +%s 2>/dev/null || date -j -f "%b %d %T %Y %Z" "${EXPIRY}" +%s 2>/dev/null)
                NOW_EPOCH=$(date +%s)
                DAYS_UNTIL_EXPIRY=$(( (EXPIRY_EPOCH - NOW_EPOCH) / 86400 ))

                if [ ${DAYS_UNTIL_EXPIRY} -lt 30 ]; then
                    warning "SSL certificate expires in ${DAYS_UNTIL_EXPIRY} days. Renew soon!"
                else
                    success "SSL certificate valid for ${DAYS_UNTIL_EXPIRY} more days"
                fi
            fi
        fi
    else
        warning "No SSL certificates found. HTTPS will not work."
        info "Generate with: docker compose run --rm certbot certonly --webroot -w /var/www/certbot -d yourdomain.com"
    fi

    # 10. Validate required files
    header "🔟 Required Files Check"
    REQUIRED_FILES=(
        "docker-compose.yml"
        "docker-compose.prod.yml"
        "Dockerfile"
        "requirements.txt"
        "nginx.conf"
        "manage.py"
    )

    for file in "${REQUIRED_FILES[@]}"; do
        if [ -f "${file}" ]; then
            success "${file} exists"
        else
            error "${file} not found"
        fi
    done

    # 11. Check Docker images are built
    header "1️⃣1️⃣  Docker Images Check"
    if docker compose -f docker-compose.yml -f docker-compose.prod.yml config > /dev/null 2>&1; then
        success "Docker Compose configuration is valid"
    else
        error "Docker Compose configuration has errors"
        info "Run: docker compose -f docker-compose.yml -f docker-compose.prod.yml config"
    fi

    # Check if images are built
    if docker images | grep -q "philosophical-debates"; then
        success "Docker images exist (may need rebuild for latest changes)"
        info "Rebuild with: docker compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache"
    else
        warning "No Docker images found. Build before deploying."
        info "Build with: docker compose -f docker-compose.yml -f docker-compose.prod.yml build"
    fi

    # 12. Check migrations
    header "1️⃣2️⃣  Database Migrations Check"
    if docker compose -f docker-compose.yml ps web | grep -q "Up"; then
        info "Checking for pending migrations..."
        PENDING=$(docker compose -f docker-compose.yml exec -T web python manage.py showmigrations --plan | grep "\[ \]" | wc -l)
        if [ ${PENDING} -gt 0 ]; then
            warning "${PENDING} pending migrations detected"
            info "Apply with: docker compose -f docker-compose.yml -f docker-compose.prod.yml exec web python manage.py migrate"
        else
            success "All migrations applied"
        fi
    else
        warning "Web container not running (cannot check migrations)"
    fi

    # 13. Validate Sentry configuration (optional but recommended)
    header "1️⃣3️⃣  Monitoring Configuration"
    if [ -n "${SENTRY_DSN}" ]; then
        success "Sentry DSN configured (error tracking enabled)"
    else
        warning "SENTRY_DSN not set. No error tracking in production."
        info "Highly recommended: Set up Sentry for production error monitoring"
    fi

    # 14. Check docker-compose.override.yml warning
    header "1️⃣4️⃣  Development Override Check"
    if [ -f "docker-compose.override.yml" ]; then
        warning "docker-compose.override.yml exists and will AUTO-MERGE unless you use explicit -f flags"
        warning "CRITICAL: In production, ALWAYS use: docker compose -f docker-compose.yml -f docker-compose.prod.yml"
        info "The override file mounts source code and uses runserver (NOT suitable for production)"
    else
        success "No docker-compose.override.yml found (safe)"
    fi

    # 15. Summary
    header "📊 Validation Summary"
    echo ""
    if [ ${ERRORS} -eq 0 ] && [ ${WARNINGS} -eq 0 ]; then
        echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║  ✅ ALL CHECKS PASSED - SAFE TO DEPLOY ✅  ║${NC}"
        echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
        echo ""
        success "Deployment validated successfully!"
        echo ""
        info "Deploy with:"
        echo "  docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build"
        echo ""
        return 0
    elif [ ${ERRORS} -eq 0 ]; then
        echo -e "${YELLOW}╔═════════════════════════════════════════════════╗${NC}"
        echo -e "${YELLOW}║  ⚠️  ${WARNINGS} WARNING(S) - REVIEW BEFORE DEPLOY ⚠️   ║${NC}"
        echo -e "${YELLOW}╚═════════════════════════════════════════════════╝${NC}"
        echo ""
        warning "${WARNINGS} warning(s) detected. Review and fix if critical."
        echo ""
        return 0
    else
        echo -e "${RED}╔═══════════════════════════════════════════════╗${NC}"
        echo -e "${RED}║  ❌ ${ERRORS} ERROR(S) - DO NOT DEPLOY ❌           ║${NC}"
        echo -e "${RED}╚═══════════════════════════════════════════════╝${NC}"
        echo ""
        error "${ERRORS} critical error(s) must be fixed before deployment!"
        echo ""
        return 1
    fi
}

# Run validation
main "$@"
