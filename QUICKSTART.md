# The Infinite Debate - Quick Start Guide

**Last Updated:** 2025-10-20
**Status:** ✅ Production-ready with 84% test coverage

## 🎯 What You're Getting

A **production-ready** full-stack debate platform featuring:
- 🧑‍🏫 **196 historical personas** (philosophers, scientists, theologians, economists, artists)
- 🤖 **AI-powered debates** using Claude Sonnet 4
- 💳 **Stripe subscriptions** (4 tiers: Free/Trial/Starter/Pro/Enterprise)
- 📚 **100 primary texts** with citation extraction
- 🎭 **Theater mode** real-time debate visualization
- 📄 **PDF export** with full citations
- ✅ **84% backend test coverage** (564 passing tests)
- ✅ **94% frontend test coverage** (218 passing tests)

---

## 🚀 Quick Start (3 Commands)

### 1. Start All Services
```bash
make start
```

This launches:
- ✅ PostgreSQL database
- ✅ Redis cache
- ✅ Django REST API (port 8001)
- ✅ Celery worker + Flower monitor
- ✅ Next.js frontend (port 3001)

**Access Points:**
- 🌐 Frontend: http://localhost:3001
- 🔌 Backend API: http://localhost:8001/api/
- 👨‍💼 Django Admin: http://localhost:8001/admin/
- 📊 Celery Flower: http://localhost:5555

### 2. Check Health
```bash
make health
```

Verifies all services are running correctly.

### 3. Stop Services
```bash
make stop
```

---

## ⚠️ IMPORTANT: Dual System Architecture

**This project has TWO debate systems:**

1. **CLI Debate System** (`.claude/commands/debate.md`)
   - **Purpose:** Testing, prototyping, persona validation only
   - **Storage:** Filesystem (`debates/*.md` directory)
   - **Personas:** 31 hardcoded figures
   - **Usage:** `/debate` slash command in Claude Code
   - **⚠️ DO NOT USE FOR PRODUCTION**

2. **Web Debate System** (Django + Next.js)
   - **Purpose:** Production user-facing platform
   - **Storage:** PostgreSQL database
   - **Personas:** 196 figures from database
   - **Usage:** Web UI at http://localhost:3001
   - **✅ USE THIS FOR ALL REAL WORK**

**🚨 Critical Warning:** These systems DO NOT sync with each other. Debates created via CLI won't appear in the web UI and vice versa.

**When to use CLI:** Only for quick persona testing during development.
**When to use Web:** For everything else (creating debates, user accounts, subscriptions).

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed explanation of this design decision.

---

## 📋 First-Time Setup

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for frontend)
- Make (comes with macOS/Linux)

### Initial Configuration

**1. Backend Environment**
Create `backend/.env`:
```bash
# Required
ANTHROPIC_API_KEY=sk-ant-your-key-here
STRIPE_SECRET_KEY=sk_test_your-key-here
STRIPE_WEBHOOK_SECRET=whsec_your-secret-here

# Optional (defaults work for local dev)
DEBUG=True
SECRET_KEY=django-insecure-dev-key-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1
```

**2. Frontend Environment**
Create `frontend/.env.local`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8001/api
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your-key-here
```

**3. Install Frontend Dependencies**
```bash
make frontend-install
```

**4. Start Services**
```bash
make start
```

**5. Run Migrations**
```bash
make db-migrate
```

**6. Load Personas (REQUIRED)**
```bash
make load-fixtures
```

⚠️ **This step is critical!** It imports all 196 personas from markdown files into the database. Without this, you'll have zero personas and won't be able to create any debates.

**📚 Understanding Persona Sync:**

Personas use a **dual-storage architecture**:
- **Source of Truth:** Markdown files in `backend/personas/fixtures/{category}/{slug}.md`
- **Runtime Database:** PostgreSQL `personas_persona` table (used by web app)

The `load-fixtures` command syncs markdown → database. You must run it:
- ✅ During initial setup (database starts empty!)
- ✅ After editing persona markdown files
- ✅ After adding new personas
- ✅ After pulling updates with persona changes

**⚠️ If you don't run this command:**
- Web app will show zero personas
- API will return empty results
- You won't be able to create debates
- Database will be out of sync with markdown files

See [ARCHITECTURE.md - Persona System](./ARCHITECTURE.md#persona-system) for detailed explanation.

**7. Create Admin User**
```bash
make create-superuser
```

✅ **Done!** Visit http://localhost:3001

---

## 🛠️ Common Commands

### Development

```bash
make help                 # Show all available commands
make status              # Check service status
make restart             # Restart all services

make backend-logs        # View all backend logs
make backend-logs s=web  # View specific service logs
make celery-logs         # View Celery worker logs
```

### Database Operations

```bash
make db-shell            # Open PostgreSQL shell
make db-migrate          # Run migrations
make db-makemigrations   # Create new migrations
make db-backup           # Backup database to file
make db-reset            # Reset database (⚠️ deletes all data!)
```

### Testing

```bash
make test                    # Run all tests (backend + frontend)
make test-coverage           # Run all tests with coverage reports
make test-backend            # Backend tests only
make test-frontend           # Frontend tests only
make test-backend-coverage   # Backend with coverage (opens htmlcov/index.html)
make test-frontend-coverage  # Frontend with coverage
make test-watch              # Run backend tests in watch mode
make coverage-report         # Open coverage reports in browser
```

### Code Quality

```bash
make lint                # Lint all code
make lint-backend        # Lint backend Python
make lint-frontend       # Lint frontend TypeScript
make format-backend      # Format backend Python code (Black)
make format-frontend     # Format frontend TypeScript code
```

### Development Tools

```bash
make shell-plus          # Django shell with all models loaded
make backend-shell       # Same as shell-plus
make backend-exec        # Execute command in container (use: make backend-exec cmd="command")
make redis-cli           # Open Redis CLI
make flower              # Open Celery Flower (http://localhost:5555)
```

### Frontend Operations

```bash
make frontend-dev        # Start frontend development server
make frontend-build      # Build frontend for production
make frontend-install    # Install frontend dependencies
make frontend-clean      # Clean frontend build artifacts
```

### Cleanup

```bash
make clean               # Clean build artifacts (backend + frontend)
make clean-backend       # Clean backend build artifacts
make clean-frontend      # Clean frontend build artifacts
make clean-all           # Clean everything including Docker volumes (⚠️ destructive!)
make clean-docker        # Remove all stopped containers and unused images
```

### Production

```bash
make build-prod          # Build for production (no cache)
make deploy-check        # Run pre-deployment checks
```

### Documentation

```bash
make docs                # Open project documentation
```

---

## 📡 API Endpoints

### Authentication
```
POST   /api/auth/register/              # Register new user
POST   /api/auth/login/                 # Login (returns JWT tokens)
POST   /api/auth/refresh/               # Refresh access token
GET    /api/auth/user/                  # Get current user
POST   /api/auth/verify-email/          # Verify email
POST   /api/auth/password-reset/        # Request password reset
```

### Personas
```
GET    /api/personas/                   # List all personas (paginated)
GET    /api/personas/by_category/       # Grouped by category
GET    /api/personas/{slug}/            # Get persona details
GET    /api/personas/{slug}/stats/      # Get persona debate stats
```

### Debates
```
POST   /api/debates/                    # Create new debate
GET    /api/debates/                    # List user's debates
GET    /api/debates/{slug}/             # Get debate details
POST   /api/debates/{slug}/generate/    # Generate debate (async with Celery)
GET    /api/debates/{slug}/export/      # Export debate as PDF
DELETE /api/debates/{slug}/             # Delete debate
```

### Primary Texts
```
GET    /api/texts/                      # List primary texts
GET    /api/texts/{slug}/               # Get text details
GET    /api/texts/{slug}/citations/     # Get all citations to this text
```

### Payments (Stripe)
```
POST   /api/payments/create-checkout/   # Create Stripe checkout session
GET    /api/payments/subscription/      # Get current subscription
POST   /api/payments/cancel/            # Cancel subscription
GET    /api/payments/history/           # Payment history
POST   /api/payments/webhook/           # Stripe webhook handler
```

### Health Checks
```
GET    /health/                         # Liveness probe
GET    /ready/                          # Readiness probe (checks DB + Redis)
```

---

## 🧪 Test the API (cURL Examples)

### Get All Personas
```bash
curl http://localhost:8001/api/personas/by_category/ | jq .
```

### Register a User
```bash
curl -X POST http://localhost:8001/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "securepass123"
  }' | jq .
```

### Login
```bash
curl -X POST http://localhost:8001/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "securepass123"
  }' | jq .
```

### Create a Debate (requires auth token)
```bash
curl -X POST http://localhost:8001/api/debates/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "title": "Nature of Reality Debate",
    "topic": "What is the fundamental nature of reality?",
    "participant_ids": [1, 5, 12],
    "depth_level": "intermediate",
    "max_rounds": 3
  }' | jq .
```

---

## 🏗️ Architecture Overview

```
philosophical-debates/
├── backend/                          # Django REST API (Docker)
│   ├── config/                      # Django settings
│   ├── debates/                     # Debate generation & management
│   ├── personas/                    # Historical figures
│   ├── texts/                       # Primary text library
│   ├── users/                       # Auth & subscriptions
│   ├── payments/                    # Stripe integration
│   ├── health/                      # Health check endpoints
│   ├── docker-compose.yml           # Docker services config
│   └── manage.py
├── frontend/                        # Next.js 15 + TypeScript
│   ├── app/                         # App Router pages
│   │   ├── page.tsx                # Home (persona grid)
│   │   ├── debates/
│   │   │   ├── new/                # Debate creation form
│   │   │   └── [slug]/             # Debate viewer (theater mode)
│   │   ├── personas/[slug]/        # Persona detail pages
│   │   ├── texts/                  # Primary text library
│   │   ├── account/                # User account management
│   │   ├── pricing/                # Subscription tiers
│   │   ├── login/                  # Auth pages
│   │   └── register/
│   ├── components/                  # React components
│   ├── lib/                         # API client, utilities
│   └── types/                       # TypeScript types
├── Makefile                         # Development commands
├── STATUS.md                        # Current project status
├── NEXT_STEPS.md                    # Roadmap
└── .reports/                        # Test & quality reports
```

---

## 🔧 Technology Stack

### Backend
- **Framework:** Django 5.2 + Django REST Framework 3.16
- **Database:** PostgreSQL 16
- **Cache:** Redis 7
- **Task Queue:** Celery 5.3 + Flower
- **AI:** Anthropic Claude API (Sonnet 4.5)
- **Payments:** Stripe
- **Testing:** pytest-django (564 tests, 84% coverage)
- **Monitoring:** Sentry error tracking

### Frontend
- **Framework:** Next.js 15 (App Router)
- **Language:** TypeScript 5 (strict mode)
- **UI:** Material-UI v7 + Emotion
- **State:** React Query (TanStack Query v5)
- **Testing:** Vitest + React Testing Library (218 tests, 94% coverage)
- **HTTP:** Axios

### Infrastructure
- **Containerization:** Docker Compose (7 services)
- **Web Server:** Nginx (reverse proxy)
- **SSL:** Certbot (Let's Encrypt)
- **Monitoring:** Structured logging + rotation

---

## 📊 What's Working Right Now

### Core Features ✅
- ✅ Complete authentication system (JWT + trial accounts)
- ✅ Stripe payment integration (4 subscription tiers)
- ✅ AI debate generation with Claude Sonnet 4
- ✅ Real-time theater mode visualization
- ✅ PDF export with citations
- ✅ Primary text library (300-600+ texts)
- ✅ Citation extraction system
- ✅ Account management & subscription controls
- ✅ Admin dashboard (Django Admin)
- ✅ Celery background task processing
- ✅ Health check endpoints for K8s

### Quality Metrics ✅
- ✅ **8.9/10 debate quality** (comprehensive audit complete)
- ✅ **84% backend test coverage** (564 passing tests)
- ✅ **94% frontend test coverage** (218 passing tests)
- ✅ **Zero failing tests** (production-ready)
- ✅ **100% pass rate** on quality audits

---

## 🐛 Troubleshooting

### Services won't start
```bash
make status              # Check what's running
make stop                # Stop all services
docker system prune -f   # Clean Docker
make backend-build       # Rebuild images
make start               # Start fresh
```

### Database connection errors
```bash
make backend-logs s=db   # Check database logs
make db-migrate          # Ensure migrations are applied
```

### Frontend can't reach API
- Check `frontend/.env.local` has correct `NEXT_PUBLIC_API_URL`
- Verify backend is running: `curl http://localhost:8001/health/`
- Check CORS settings in `backend/config/settings.py`

### Tests failing
```bash
make test-backend        # See which tests are failing
make clean-backend       # Clean artifacts
make backend-restart     # Restart services
make test-backend        # Try again
```

### Port already in use
```bash
# Find process using port 8001
lsof -i :8001
# Kill it
kill -9 <PID>

# Or use different ports in docker-compose.yml
```

### Personas not loading

⚠️ **Most Common Issue:** Forgot to run `make load-fixtures` during setup!

Personas only exist as markdown files until you explicitly load them into the database. If you see:
- Empty persona list in frontend
- "No personas available" message
- Cannot create debates

**Solution:**
```bash
make load-fixtures       # Load/reload all personas
make backend-logs s=web  # Check for errors if above fails
```

This should output:
```
Created: 196
Updated: 0
```

---

## 📚 Additional Resources

### Documentation
- **Project Status:** `STATUS.md`
- **Roadmap:** `NEXT_STEPS.md`
- **Makefile Guide:** `MAKEFILE_GUIDE.md`
- **Test Reports:** `.reports/test-coverage/`
- **Quality Audits:** `.reports/debate-quality/`

### Development URLs
- **Frontend:** http://localhost:3001
- **Backend API:** http://localhost:8001/api/
- **Django Admin:** http://localhost:8001/admin/
- **Celery Flower:** http://localhost:5555
- **API Documentation:** http://localhost:8001/api/schema/swagger/

### Deployment Resources
- **Domain:** theinfinitedebate.com (ICDSoft)
- **Target:** AWS Lightsail (backend) + Vercel (frontend)
- **Deployment Guide:** See `NEXT_STEPS.md` → Deployment section

---

## 🚀 What's Next?

The platform is **production-ready**! Next priorities:

1. ✅ **Test Coverage** - COMPLETED (84% backend, 94% frontend)
2. 🎯 **Minimum 2-round enforcement** - Prevent single-round debates
3. 🎯 **Topic-persona matching guidance** - Help users choose topics
4. 🎯 **Citation markup integration** - Auto-add {Title} syntax
5. 🎯 **Deploy to production** - AWS Lightsail + Vercel

See `NEXT_STEPS.md` for detailed roadmap.

---

## 💡 Pro Tips

**1. Use Makefile for everything:**
```bash
make help  # See all commands
```

**2. Monitor in real-time:**
```bash
make backend-logs        # Terminal 1: Backend logs
make celery-logs         # Terminal 2: Celery logs
make frontend-dev        # Terminal 3: Frontend
```

**3. Quick iteration:**
```bash
make restart             # Restart all services
make test-coverage       # Run tests + coverage
make health             # Verify everything works
```

**4. Database inspection:**
```bash
make db-shell           # PostgreSQL shell
make shell-plus         # Django shell with models
```

**5. Clean slate:**
```bash
make clean              # Clean build artifacts
make db-reset           # Reset database (⚠️ deletes data!)
```

---

**Ready to start?** Run `make start` and visit http://localhost:3001! 🎉
