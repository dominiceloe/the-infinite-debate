# Security Hardening Implementation

This document describes the security improvements implemented for production deployment.

## Changes Implemented

### 1. SECRET_KEY Hardening
**File:** `config/settings.py` (lines 32-38)

- **Removed** hardcoded SECRET_KEY fallback
- **Added** mandatory SECRET_KEY validation that fails fast on startup
- **Provides** helpful error message with key generation command

**Impact:** Prevents accidental deployment with insecure default key

### 2. HTTPS Enforcement (Production Only)
**File:** `config/settings.py` (lines 28-29, 45-59)

Added environment-aware security settings:
- `DJANGO_ENV` environment variable (default: 'development')
- Production-only HTTPS enforcement settings:
  - `SECURE_SSL_REDIRECT = True` - Force HTTPS redirects
  - `SESSION_COOKIE_SECURE = True` - HTTPS-only session cookies
  - `CSRF_COOKIE_SECURE = True` - HTTPS-only CSRF cookies
  - `SECURE_HSTS_SECONDS = 31536000` - 1 year HSTS
  - `SECURE_HSTS_INCLUDE_SUBDOMAINS = True` - HSTS for subdomains
  - `SECURE_HSTS_PRELOAD = True` - HSTS preload list eligibility
  - `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')` - Proxy support

**Impact:** Ensures encrypted communication in production while allowing local development

### 3. API Rate Limiting
**File:** `config/settings.py` (lines 181-189)

Added DRF throttling configuration:
- Anonymous users: 20 requests/hour
- Authenticated users: 100 requests/hour
- Debate generation: 10 requests/hour per user (custom scope)

**Files Created:**
- `debates/throttles.py` - Custom DebateGenerationThrottle class

**Files Modified:**
- `debates/views.py` (lines 12, 25-31) - Applied throttle to generate endpoint

**Impact:** Prevents abuse and manages API resource consumption

### 4. CORS Configuration from Environment
**File:** `config/settings.py` (lines 192-194)

- **Changed** from hardcoded CORS origins to environment variable
- **Format:** Comma-separated list in `CORS_ALLOWED_ORIGINS` env var
- **Default:** Development origins (localhost:3000, 127.0.0.1:3000)

**Impact:** Production deployments can specify allowed origins without code changes

### 5. Input Validation
**File:** `debates/models.py` (lines 3, 20-26)

Added validators to Debate.topic field:
- Minimum length: 10 characters
- Maximum length: 1000 characters
- Clear error messages

**Migration:** `debates/migrations/0003_add_topic_validators.py`

**Impact:** Prevents malformed or excessively large topic inputs

### 6. Celery Import Fix
**File:** `config/__init__.py` (lines 5-10)

- **Wrapped** celery import in try-except
- **Prevents** ImportError when celery not installed

**Impact:** Allows Django to start without celery (optional dependency)

## Environment Variables Required

### Development (.env file)
```bash
SECRET_KEY=<generate-with-django-command>
DEBUG=True
DJANGO_ENV=development
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### Production
```bash
SECRET_KEY=<strong-random-key>
DEBUG=False
DJANGO_ENV=production
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

## Generate SECRET_KEY

Run this command to generate a secure secret key:
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

## Testing Security Settings

### 1. Test SECRET_KEY Validation
```bash
# Remove SECRET_KEY from .env and try to start Django
# Expected: ValueError with helpful message
```

### 2. Test Rate Limiting
```bash
# Make >10 requests to /api/debates/{slug}/generate/ within an hour
# Expected: 429 Too Many Requests after 10th request
```

### 3. Test HTTPS Enforcement (Production)
```bash
# Set DJANGO_ENV=production
# Access site via HTTP
# Expected: Redirect to HTTPS
```

### 4. Test Topic Validation
```bash
# Try to create debate with topic < 10 chars
# Expected: Validation error
# Try to create debate with topic > 1000 chars
# Expected: Validation error
```

## Rate Limit Scopes

| Scope | Rate | Applies To |
|-------|------|------------|
| `anon` | 20/hour | Unauthenticated requests |
| `user` | 100/hour | General authenticated API requests |
| `debate_generation` | 10/hour | POST /api/debates/{slug}/generate/ |

## Production Deployment Checklist

- [ ] Set `SECRET_KEY` to strong random value
- [ ] Set `DEBUG=False`
- [ ] Set `DJANGO_ENV=production`
- [ ] Set `ALLOWED_HOSTS` to production domains
- [ ] Set `CORS_ALLOWED_ORIGINS` to production frontend URLs
- [ ] Configure SSL/TLS certificate
- [ ] Configure reverse proxy to set `X-Forwarded-Proto` header
- [ ] Run database migrations: `python manage.py migrate`
- [ ] Test HTTPS redirect works
- [ ] Test rate limiting is active
- [ ] Monitor for security alerts

## Security Best Practices

1. **Never commit .env files** - Add to .gitignore
2. **Rotate SECRET_KEY** if compromised
3. **Use strong passwords** for database and admin accounts
4. **Keep dependencies updated** - Run `pip list --outdated` regularly
5. **Monitor rate limit violations** - Check logs for abuse patterns
6. **Use database backups** - Regular automated backups
7. **Enable Django security middleware** - Already configured
8. **Use parameterized queries** - Django ORM handles this
9. **Validate all user input** - Added for debate topics
10. **Use HTTPS everywhere** - Enforced in production

## Files Modified

1. `config/settings.py` - Security settings, rate limits, CORS
2. `config/__init__.py` - Celery import error handling
3. `debates/models.py` - Topic field validators
4. `debates/views.py` - Throttle import and configuration
5. `debates/throttles.py` - Custom throttle class (new file)
6. `debates/migrations/0003_add_topic_validators.py` - Migration (new file)
7. `SECURITY_HARDENING.md` - This document (new file)
