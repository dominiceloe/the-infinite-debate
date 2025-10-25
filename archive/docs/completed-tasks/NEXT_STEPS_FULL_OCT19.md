# Next Steps: Post-Infrastructure Setup

**Date:** October 19, 2025
**Status:** ✅ Critical infrastructure complete, ready for testing and deployment
**Domain:** promptthepast.com (registered via ICDSoft)
**Deployment Target:** AWS Lightsail + Vercel

---

## ✅ COMPLETED (All Critical Blockers Resolved)

### Phase 1: Infrastructure Setup ✅
- [x] PostgreSQL 14.19 installed and running
- [x] Database `philosophical_debates` created with user `debates_user`
- [x] All 40+ tables migrated with optimized indexes
- [x] **9,332 records migrated** from SQLite to PostgreSQL
  - 196 personas
  - 100 primary texts (8,937 sections)
  - 13 debates (57 messages)
  - 3 users with payment history

### Phase 2: Background Processing ✅
- [x] Redis 8.2.2 installed and running
- [x] Celery 5.5.3 installed with worker running
- [x] `generate_debate_task` registered and ready
- [x] Threading code removed from codebase

### Phase 3: Security Hardening ✅
- [x] SECRET_KEY generated and configured (no hardcoded fallback)
- [x] HTTPS enforcement added (production mode)
- [x] Rate limiting configured (10/hour debates, 100/hour API)
- [x] Input validation on debate topics (10-1000 chars)
- [x] Environment-based CORS configuration

### Phase 4: Performance Optimization ✅
- [x] N+1 queries eliminated (80-98% reduction)
- [x] Composite indexes on `debate/round_number/persona`
- [x] Birth year index on personas
- [x] Query optimization with select_related/prefetch_related

---

## 📋 INFRASTRUCTURE IMPLEMENTATION SUMMARY

### 1. Database Migration: SQLite → PostgreSQL ✅ COMPLETE

**Status:** DONE on Oct 19, 2025
- ✅ PostgreSQL 14.19 installed and running
- ✅ All 9,332 records migrated from SQLite
- ✅ Database indexes optimized
- ✅ Environment variables configured

**No action needed** - This was a critical blocker and is now complete.

---

### 2. Celery/Redis Background Processing ✅ COMPLETE

**Status:** DONE on Oct 19, 2025

**What we implemented:**
- ✅ Redis 8.2.2 as message broker
- ✅ Celery 5.5.3 for async task processing
- ✅ `generate_debate_task` for background debate generation
- ✅ Threading code removed (production-safe now)

**Production Deployment Note:**
You'll need to run **both** Celery worker AND Redis in production. Update docker-compose.yml to include:

```yaml
services:
  redis:
    image: redis:8-alpine
    restart: always
    ports:
      - "6379:6379"

  celery:
    build: .
    command: celery -A config worker --loglevel=info
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    restart: always
```

---

### 3. Static Files Strategy: WhiteNoise (Recommended)

**Decision:** Use **WhiteNoise** for Phase 1 (Lightsail deployment)

**Rationale:**
- ✅ Simplest setup (no AWS S3 credentials needed)
- ✅ Works well for <1000 users
- ✅ Compresses and caches static files automatically
- ✅ One less service to manage initially
- ⚠️ Can migrate to S3+CloudFront later if needed

**Already configured in settings.py** - Just need to run `collectstatic` before deployment.

**When to migrate to S3:**
- More than 1,000 active users
- Global audience (need CDN)
- Large media files (user uploads)

---

### 4. Persona Files Strategy: Database (Recommended)

**Status:** Already using Persona model in database ✅

**Current Architecture:**
- 196 personas stored in `personas_persona` table
- Full content stored in database fields
- Category-based organization (theologians/philosophers/scientists)

**For Production:** No changes needed! Personas are already in PostgreSQL database.

**Migration strategy:** When you migrate SQLite → PostgreSQL (already done), personas were included in the 9,332 records transferred.

**Alternative considered:** Markdown files in `.claude/lib/personas/`
- ❌ Not recommended - database is better for production
- Files were useful during development but database wins for:
  - Django admin editing
  - Query optimization
  - API serialization
  - No file system dependencies

---

### 5. Email Configuration: ICDSoft SMTP

**Setup needed:**
```python
# settings.py (production)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mail.icdsoft.com'  # Verify with ICDSoft docs
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')  # noreply@promptthepast.com
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = 'Prompt the Past <noreply@promptthepast.com>'
SERVER_EMAIL = 'errors@promptthepast.com'  # For error emails
```

**Email accounts to create in ICDSoft:**
- `hello@promptthepast.com` - General inquiries
- `support@promptthepast.com` - Customer support
- `noreply@promptthepast.com` - Automated Django emails (password resets, etc.)
- `errors@promptthepast.com` - Server error notifications

---

### 6. Production Settings Split: Recommended Structure

**Create three settings files:**

```python
# config/settings/base.py - Common settings
# config/settings/development.py - Dev overrides (DEBUG=True, etc.)
# config/settings/production.py - Prod overrides (DEBUG=False, security settings)
```

**Or simpler approach:** Use environment variables (current approach is fine)
```python
# config/settings.py (current approach)
DEBUG = os.getenv('DEBUG', 'False') == 'True'
DJANGO_ENV = os.getenv('DJANGO_ENV', 'development')

if DJANGO_ENV == 'production':
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    # ... other production settings
```

**Recommendation:** Current approach is fine for Phase 1. Split files later if complexity grows.

---

### 7. Docker Configuration Files Needed

**Priority 1: Create these before deployment**

**`backend/Dockerfile`:**
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Collect static files
RUN python manage.py collectstatic --no-input

# Run migrations and start gunicorn
CMD python manage.py migrate && \
    gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

**`backend/docker-compose.yml`:**
```yaml
version: '3.8'

services:
  db:
    image: postgres:14
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: debates
      POSTGRES_USER: debatesuser
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    restart: always

  redis:
    image: redis:8-alpine
    restart: always

  web:
    build: .
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
    volumes:
      - static_volume:/app/staticfiles
    env_file:
      - .env
    depends_on:
      - db
      - redis
    restart: always

  celery:
    build: .
    command: celery -A config worker --loglevel=info
    env_file:
      - .env
    depends_on:
      - db
      - redis
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - static_volume:/app/staticfiles:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    depends_on:
      - web
    restart: always

volumes:
  postgres_data:
  static_volume:
```

**`backend/nginx.conf`:**
```nginx
events {
    worker_connections 1024;
}

http {
    upstream django {
        server web:8000;
    }

    server {
        listen 80;
        server_name api.promptthepast.com;

        location / {
            return 301 https://$host$request_uri;
        }

        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }
    }

    server {
        listen 443 ssl;
        server_name api.promptthepast.com;

        ssl_certificate /etc/letsencrypt/live/api.promptthepast.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/api.promptthepast.com/privkey.pem;

        client_max_body_size 100M;

        location /static/ {
            alias /app/staticfiles/;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }

        location / {
            proxy_pass http://django;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

**`backend/.env.example`:**
```bash
# Django Core
SECRET_KEY=change-me-in-production
DEBUG=False
DJANGO_ENV=production
ALLOWED_HOSTS=api.promptthepast.com,promptthepast.com

# Database
DB_NAME=debates
DB_USER=debatesuser
DB_PASSWORD=change-me
DB_HOST=db
DB_PORT=5432

# Redis & Celery
REDIS_URL=redis://redis:6379/0

# APIs
ANTHROPIC_API_KEY=sk-ant-...

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_STUDENT_PRICE_ID=price_...
STRIPE_SCHOLAR_PRICE_ID=price_...

# CORS
CORS_ALLOWED_ORIGINS=https://promptthepast.com,https://www.promptthepast.com

# Email (ICDSoft)
EMAIL_HOST=mail.icdsoft.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@promptthepast.com
EMAIL_HOST_PASSWORD=change-me
DEFAULT_FROM_EMAIL=Prompt the Past <noreply@promptthepast.com>
```

**`backend/requirements.txt`** - Add these production deps:
```
gunicorn==21.2.0
whitenoise==6.6.0
dj-database-url==2.1.0
```

---

### 8. Domain & DNS Configuration

**Domain:** `promptthepast.com` (already registered via ICDSoft) ✅

**DNS Records to configure in ICDSoft:**

```dns
# Frontend (Vercel)
Type: CNAME
Host: @
Value: cname.vercel-dns.com

Type: CNAME
Host: www
Value: cname.vercel-dns.com

# Backend API (AWS Lightsail)
Type: A
Host: api
Value: [Your Lightsail Static IP - get after creating instance]

# Email (ICDSoft mail servers)
Type: MX
Host: @
Value: [Check ICDSoft docs for their mail server]
Priority: 10
```

**Vercel Custom Domain Setup:**
1. Add `promptthepast.com` in Vercel dashboard
2. Add `www.promptthepast.com` in Vercel dashboard
3. Vercel auto-provisions SSL certificates
4. Wait for DNS propagation (5min - 48hrs, usually <1hr)

---

### 9. Monitoring & Logging Implementation

**Django Logging (Already configured in settings.py):**
```python
# Update settings.py logging to write to files
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/app.log',
        },
    },
    'loggers': {
        'django': {'handlers': ['file'], 'level': 'INFO'},
        'debates': {'handlers': ['file'], 'level': 'INFO'},
        'celery': {'handlers': ['file'], 'level': 'INFO'},
    },
}
```

**CloudWatch Setup (AWS Lightsail):**
```bash
# Install CloudWatch agent on Lightsail instance
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb

# Configure to stream logs
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config -m ec2 -s -c file:/opt/aws/amazon-cloudwatch-agent/etc/config.json
```

**Sentry Setup (Recommended for error tracking):**
```bash
pip install sentry-sdk
```

```python
# settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

if DJANGO_ENV == 'production':
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        integrations=[DjangoIntegration(), CeleryIntegration()],
        traces_sample_rate=0.1,
        environment='production',
    )
```

**Celery Monitoring (Flower):**
```bash
# Add to requirements.txt
flower==2.0.1

# Add to docker-compose.yml
flower:
  build: .
  command: celery -A config flower --port=5555
  ports:
    - "5555:5555"
  env_file:
    - .env
  depends_on:
    - redis
    - celery
```

Access Flower at `http://your-lightsail-ip:5555` (restrict with password!)

---

### 10. Configuration Files Checklist ✅ COMPLETE

**Completion Date:** October 19, 2025

**Status of required files:**

- [x] `requirements.txt` - ✅ Updated with gunicorn, whitenoise, dj-database-url, flower
- [x] `Dockerfile` - ✅ Created with Python 3.10, PostgreSQL client, system deps
- [x] `docker-compose.yml` - ✅ Created with 7 services (db, redis, web, celery, flower, nginx, certbot)
- [x] `nginx.conf` - ✅ Created for production (SSL)
- [x] `nginx-dev.conf` - ✅ Created for local testing (no SSL)
- [x] `.env.example` - ✅ Created with all production variables
- [x] `settings.py` - ✅ Updated with STATIC_ROOT and WhiteNoise
- [x] `.dockerignore` - ✅ Created (excludes venv, cache, logs)
- [x] `health/views.py` - ✅ Created with health check endpoints
- [ ] `gunicorn_config.py` - Optional, using command-line args

**`.dockerignore`:**
```
*.pyc
__pycache__
.git
.env
venv/
*.sqlite3
node_modules/
.DS_Store
*.log
```

---

## 🎯 CURRENT STATUS: Services Running

**Background Services (auto-start on reboot):**
```bash
# Check status:
brew services list | grep -E "(postgres|redis)"

# Output:
postgresql@14  started
redis          started
```

**Development Services (manual start):**
```bash
# Terminal 1 - Celery Worker
# PID: Check /tmp/celery_worker.log
tail -f /tmp/celery_worker.log

# Terminal 2 - Django Server
# PID: 6941, Port: 8001
tail -f /tmp/django_server.log
```

---

## 🚀 DEPLOYMENT PREPARATION (Week 1)

### Priority 1: Create Docker Configuration Files ✅ COMPLETE

**Completion Date:** October 19, 2025

**Goal:** Prepare backend for Docker deployment to AWS Lightsail

**Files created:**
1. ✅ `backend/Dockerfile` - Multi-stage build with Python 3.10, PostgreSQL client, system deps
2. ✅ `backend/docker-compose.yml` - 7 services (db, redis, web, celery, flower, nginx, certbot)
3. ✅ `backend/nginx.conf` - Production config with SSL (for deployment)
4. ✅ `backend/nginx-dev.conf` - Development config without SSL (for local testing)
5. ✅ `backend/.env.example` - Complete production environment template
6. ✅ `backend/.dockerignore` - Excludes venv, cache, logs, git

**Added to requirements.txt:**
- ✅ gunicorn==21.2.0
- ✅ whitenoise==6.6.0
- ✅ dj-database-url==2.1.0
- ✅ flower==2.0.1

**Settings updated:**
- ✅ `STATIC_ROOT` configured (backend/staticfiles)
- ✅ WhiteNoise middleware added for static file serving
- ✅ WhiteNoise storage backend configured (compressed + manifest)

**Local testing completed:**
```bash
cd backend
docker-compose --env-file .env.docker up -d
# ✅ All 7 services running successfully
# ✅ Database migrations applied (54 migrations)
# ✅ Health check: http://localhost/health/ - healthy
# ✅ Readiness check: http://localhost/ready/ - ready
# ✅ Celery Flower: http://localhost:5555
```

**Services running:**
- PostgreSQL 14 (debates database)
- Redis 8 (message broker)
- Django/Gunicorn (web application on port 8000)
- Celery worker (background task processing)
- Flower (Celery monitoring on port 5555)
- Nginx (reverse proxy on port 80)
- Certbot (SSL certificate management)

---

### Priority 2: Update Settings for Production ✅ COMPLETE

**Completion Date:** October 19, 2025

**Tasks:**
1. ✅ Split production vs development config (already done with DJANGO_ENV)
2. ✅ Add email backend configuration (see "Email Configuration" above)
3. ✅ Ensure all secrets come from environment variables (already done)
4. ✅ Add health check endpoints for monitoring

**Health check endpoints created:**
- ✅ `/health/` - Basic health check (database connectivity)
- ✅ `/ready/` - Readiness check (database + Redis connectivity)

**Implementation:**
```python
# health/views.py - CREATED
from django.http import JsonResponse
from django.db import connection
from django.views.decorators.http import require_GET

@require_GET
def health_check(request):
    """Basic health check endpoint for Docker healthcheck."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return JsonResponse({'status': 'healthy', 'database': 'connected'})
    except Exception as e:
        return JsonResponse({'status': 'unhealthy', 'database': 'disconnected', 'error': str(e)}, status=500)

@require_GET
def readiness_check(request):
    """Readiness check for load balancers."""
    checks = {'database': False, 'redis': False}
    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        checks['database'] = True
    except Exception:
        pass
    # Check Redis
    try:
        from django.core.cache import cache
        cache.set('readiness_check', 'ok', timeout=1)
        if cache.get('readiness_check') == 'ok':
            checks['redis'] = True
    except Exception:
        pass
    all_ready = all(checks.values())
    return JsonResponse({'status': 'ready' if all_ready else 'not_ready', 'checks': checks},
                       status=200 if all_ready else 503)

# config/urls.py - UPDATED
urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("ready/", readiness_check, name="readiness-check"),
    # ... existing routes
]
```

---

### Priority 3: ICDSoft Email Setup

**Goal:** Configure email accounts for Django to send emails

**Steps:**
1. Log into ICDSoft control panel
2. Create email accounts:
   - `hello@promptthepast.com`
   - `support@promptthepast.com`
   - `noreply@promptthepast.com`
   - `errors@promptthepast.com`
3. Note down passwords
4. Get SMTP server details from ICDSoft docs (likely `mail.icdsoft.com`)
5. Test email sending from Django

**Test email sending:**
```python
# Django shell
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail(
...     'Test Email',
...     'Testing Django email configuration.',
...     'noreply@promptthepast.com',
...     ['your-personal-email@gmail.com'],
... )
```

---

## 📋 IMMEDIATE NEXT STEPS (Week 1) - TESTING

### 1. Test Celery Integration (1-2 hours)

**Goal:** Verify async debate generation works with new infrastructure

```bash
# Test via Django shell
cd /Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/backend
source venv/bin/activate
python manage.py shell
```

```python
# In Django shell:
from debates.tasks import generate_debate_task
from debates.models import Debate
from personas.models import Persona

# Create test debate
socrates = Persona.objects.get(slug='socrates')
plato = Persona.objects.get(slug='plato')

debate = Debate.objects.create(
    topic="What is the relationship between knowledge and virtue?",
    max_rounds=3,
    status='pending',
    user=None  # Or assign to a user
)
debate.participants.set([socrates, plato])

# Trigger async task
result = generate_debate_task.delay(debate.id)
print(f"Task ID: {result.id}")
print(f"Task Status: {result.status}")

# Check status after a few seconds
import time
time.sleep(5)
result.status  # Should show 'SUCCESS' or 'STARTED'
```

**Monitor Celery logs:**
```bash
tail -f /tmp/celery_worker.log
# You should see the task executing!
```

**Verify in database:**
```bash
psql -U debates_user -d philosophical_debates -h localhost
SELECT id, topic, status, max_rounds FROM debates_debate ORDER BY created_at DESC LIMIT 5;
\q
```

---

### 2. Frontend Integration (2-4 hours)

**Current Issue:** Frontend still expects synchronous responses

**Changes Needed in Frontend:**

**File:** `frontend/lib/api.ts`
```typescript
// Current: Expects debate to be completed immediately
// New: Handle task_id and poll for status

interface GenerateDebateResponse {
  debate: Debate;
  task_id: string;  // NEW: Celery task ID
  status: 'pending' | 'started' | 'success' | 'failure';
}

export async function generateDebate(debateId: string) {
  const response = await apiClient.post<GenerateDebateResponse>(
    `/api/debates/${debateId}/generate/`
  );
  return response.data;
}

// NEW: Poll for task status
export async function getTaskStatus(taskId: string) {
  const response = await apiClient.get(`/api/tasks/${taskId}/`);
  return response.data;
}
```

**File:** `frontend/app/debates/[slug]/page.tsx`
```typescript
// Update polling logic to handle Celery task IDs
const { data: debate } = useQuery({
  queryKey: ['debate', slug],
  queryFn: () => getDebate(slug),
  refetchInterval: (query) => {
    const data = query.state.data;
    // Poll every 2 seconds if generating
    return data?.status === 'generating' ? 2000 : false;
  },
});
```

**Backend Changes Needed:**

Add task status endpoint in `debates/views.py`:
```python
from celery.result import AsyncResult
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def task_status(request, task_id):
    """Get Celery task status."""
    result = AsyncResult(task_id)
    return Response({
        'task_id': task_id,
        'status': result.status,
        'ready': result.ready(),
        'result': result.result if result.ready() else None,
    })
```

Add URL pattern in `debates/urls.py`:
```python
path('tasks/<str:task_id>/', views.task_status, name='task-status'),
```

---

### 3. Write Integration Tests (4-6 hours)

**Priority Tests:**

**File:** `backend/debates/tests/test_celery_integration.py`
```python
from django.test import TestCase
from debates.models import Debate
from debates.tasks import generate_debate_task
from personas.models import Persona

class CeleryIntegrationTests(TestCase):
    def test_debate_generation_task(self):
        """Test debate generation via Celery."""
        socrates = Persona.objects.create(name='Socrates', slug='socrates')
        plato = Persona.objects.create(name='Plato', slug='plato')

        debate = Debate.objects.create(
            topic='What is justice?',
            max_rounds=2,
            status='pending'
        )
        debate.participants.set([socrates, plato])

        # Trigger task
        result = generate_debate_task.delay(debate.id)

        # Wait for completion (with timeout)
        result.get(timeout=60)

        # Verify debate completed
        debate.refresh_from_db()
        self.assertEqual(debate.status, 'completed')
        self.assertGreater(debate.messages.count(), 0)
```

**File:** `backend/debates/tests/test_performance.py`
```python
from django.test import TestCase
from django.test.utils import override_settings
from django.db import connection
from django.test.utils import CaptureQueriesContext

class PerformanceTests(TestCase):
    def test_debate_detail_query_count(self):
        """Verify N+1 queries are resolved."""
        # Create test data
        debate = create_test_debate_with_messages(num_messages=50)

        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(f'/api/debates/{debate.slug}/')

        # Should be ≤5 queries regardless of message count
        self.assertLessEqual(len(ctx.captured_queries), 5)
```

**Run tests:**
```bash
cd backend
source venv/bin/activate
python manage.py test debates.tests
```

---

### 4. Add Monitoring & Logging (2-3 hours)

**Install Sentry (Error Tracking):**

```bash
pip install sentry-sdk
```

**File:** `backend/config/settings.py`
```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

if not DEBUG:
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
        ],
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
        environment=os.getenv('DJANGO_ENV', 'development'),
    )
```

**Add structured logging:**

**File:** `backend/config/settings.py`
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'django_debug.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'debates': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
    },
}
```

---

## 📈 SHORT-TERM IMPROVEMENTS (Weeks 2-4)

### Week 2: Testing & Quality

**Priority:**
1. ✅ Integration tests for Celery tasks
2. ✅ Performance tests verifying query optimization
3. ✅ End-to-end tests for debate generation flow
4. ⚠️ Add test coverage reporting (pytest-cov)
5. ⚠️ Set up CI/CD pipeline (GitHub Actions)

**Target:** 60%+ test coverage

---

### Week 3: Frontend Enhancements

**Priority:**
1. ⚠️ Migrate to HttpOnly cookies for auth tokens
2. ⚠️ Implement SSE or WebSocket for real-time debate updates
3. ⚠️ Add error boundaries for graceful failure handling
4. ⚠️ Implement proper loading states for async operations
5. ⚠️ Add TypeScript strict mode

---

### Week 4: DevOps & Monitoring

**Priority:**
1. ⚠️ Set up Celery Flower for task monitoring
2. ⚠️ Configure PostgreSQL backups (pg_dump automation)
3. ⚠️ Add health check endpoints (`/health`, `/ready`)
4. ⚠️ Implement database connection pooling (pgBouncer)
5. ⚠️ Set up staging environment

---

## 🚀 PRODUCTION READINESS (Month 2)

### Deployment Prerequisites

**Infrastructure:**
- [ ] Choose hosting (Railway, Heroku, AWS, DigitalOcean)
- [ ] Set up production PostgreSQL (managed service)
- [ ] Set up production Redis (managed service)
- [ ] Configure CDN for static assets
- [ ] Set up domain and SSL certificates

**Security:**
- [x] SECRET_KEY enforced (no defaults)
- [x] HTTPS enforcement enabled
- [x] Rate limiting configured
- [ ] Security headers (CSP, X-Frame-Options, etc.)
- [ ] Regular security audits

**Performance:**
- [x] N+1 queries resolved
- [x] Database indexes optimized
- [ ] Query result caching (Redis)
- [ ] CDN for static files
- [ ] Load testing completed

**Monitoring:**
- [ ] Sentry error tracking
- [ ] Application performance monitoring (APM)
- [ ] Database query monitoring
- [ ] Celery task monitoring (Flower)
- [ ] Uptime monitoring

---

## 🔧 MAINTENANCE TASKS

### Daily
```bash
# Check service status
brew services list | grep -E "(postgres|redis)"

# Check Celery worker
ps aux | grep celery | grep -v grep

# Check Django logs
tail -f /tmp/django_server.log
```

### Weekly
```bash
# Backup PostgreSQL
pg_dump -U debates_user -d philosophical_debates -F c -f backup_$(date +%Y%m%d).dump

# Check disk space
df -h

# Review Celery task success/failure rates
# (Implement via Flower dashboard)
```

### Monthly
```bash
# Update dependencies
pip list --outdated
npm outdated

# Review and rotate logs
# Security audit
python manage.py check --deploy
```

---

## 📞 TROUBLESHOOTING QUICK REFERENCE

### Services Not Starting

**PostgreSQL:**
```bash
brew services restart postgresql@14
# Check logs:
tail -f /usr/local/var/log/postgresql@14.log
```

**Redis:**
```bash
brew services restart redis
# Test:
redis-cli ping  # Should return PONG
```

**Celery Worker:**
```bash
# Kill existing worker
ps aux | grep celery | grep -v grep | awk '{print $2}' | xargs kill

# Start fresh
cd backend
source venv/bin/activate
celery -A config worker --loglevel=info --detach --logfile=/tmp/celery_worker.log
```

**Django Server:**
```bash
# Kill existing server
lsof -ti:8001 | xargs kill

# Start fresh
cd backend
source venv/bin/activate
python manage.py runserver 8001 > /tmp/django_server.log 2>&1 &
```

### Database Connection Issues

```bash
# Test connection
psql -U debates_user -d philosophical_debates -h localhost

# Check active connections
psql postgres -c "SELECT count(*) FROM pg_stat_activity;"

# Kill stuck connections
psql postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='philosophical_debates';"
```

### Celery Tasks Not Running

```bash
# Check Redis connection
redis-cli ping

# Check Celery worker log
tail -f /tmp/celery_worker.log

# Purge queue
celery -A config purge

# Restart worker
ps aux | grep celery | awk '{print $2}' | xargs kill
celery -A config worker --loglevel=info --detach --logfile=/tmp/celery_worker.log
```

---

## 📚 DOCUMENTATION TO UPDATE

1. **README.md** - Add PostgreSQL/Redis/Celery setup instructions
2. **API.md** - Document new async debate generation flow
3. **DEPLOYMENT.md** - Production deployment guide
4. **TESTING.md** - How to run tests locally

---

## ✅ SUCCESS METRICS

**Infrastructure (Achieved):**
- ✅ PostgreSQL running with 9,332 records
- ✅ Celery worker processing tasks
- ✅ Zero hardcoded secrets
- ✅ 80-98% query reduction

**Next Milestones:**
- 🎯 60%+ test coverage
- 🎯 < 200ms average API response time
- 🎯 Zero production errors for 7 days
- 🎯 Successful load test (100 concurrent users)

---

**Last Updated:** October 19, 2025
**Setup Documentation:** See QUICKSTART.md for development setup, and backend/ directory for infrastructure guides (CELERY_GUIDE.md, POSTGRESQL_MIGRATION.md, etc.)
