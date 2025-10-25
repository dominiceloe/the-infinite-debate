# The Infinite Debate

**AI-powered debates between historical thinkers with full-text primary source integration.**

Bringing 196 philosophers, theologians, and scientists to life through authentic debates powered by Claude AI, backed by 300+ primary texts from Project Gutenberg.

**Current Status:** B+ (87/100) - Production-ready with 5 critical fixes needed
**Last Updated:** October 25, 2025

---

## 🎯 Quick Start

```bash
# Clone and start with Docker (recommended)
git clone <repository-url>
cd philosophical-debates

# Start all services (backend + frontend + database + redis + celery)
make start

# Visit http://localhost:3001
```

**That's it!** See [QUICKSTART.md](QUICKSTART.md) for detailed setup or [MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md) for all available commands.

---

## 🏗️ Architecture

**Production-grade full-stack application** with modern async patterns, real-time streaming, and comprehensive test coverage.

### Tech Stack

**Backend**
- Django 5.2 + Django REST Framework 3.16
- PostgreSQL (primary database)
- Redis (caching + pub/sub for SSE)
- Celery (async task queue for debate generation)
- Anthropic Claude API (Sonnet 3.5/4.0)
- Stripe (subscription payments)

**Frontend**
- Next.js 15 (App Router) + TypeScript 5
- Material-UI v7 (design system)
- TanStack Query v5 (state management)
- Server-Sent Events (real-time updates)

**Infrastructure**
- Docker Compose (7 services: web, nginx, postgres, redis, celery-worker, celery-beat, flower)
- Nginx (reverse proxy)
- Sentry (error tracking)
- JWT + HttpOnly cookies (authentication)

---

## ✨ Features

### 📚 Comprehensive Persona Library
- **196 historical figures** across 29 categories
  - 73 Theologians (Christianity, Islam, Judaism, Buddhism, Hinduism, Daoism)
  - 73 Philosophers (Ancient Greek, Modern Western, Eastern, Existentialist)
  - 50 Scientists (Physics, Biology, Chemistry, Mathematics)
- **4-tier access system:** Free (30) → Starter (60) → Pro (90) → Enterprise (196)
- Detailed persona profiles with debate strategies, key concepts, historical context

### 🎭 AI-Powered Debates
- **Multi-participant debates** (2-15 historical figures)
- **Real-time generation** with Server-Sent Events (no polling!)
- **Theater mode:** Split-screen persona cards with typewriter animation
- **Transcript mode:** Full markdown transcript with citations
- **Chronological turn order** based on historical birth years
- **Configurable parameters:** depth level, max rounds, participant selection

### 📖 Primary Text Library
- **300+ philosophical/theological/scientific texts** from Project Gutenberg
- **145+ authors** with primary works linked to their personas
- **Full-text reading interface** with section navigation
- **Advanced filtering:** category, era, author, publication year, difficulty
- **Rich metadata:** word count, section count, translator info, source links

### 🔗 Citation System
- **Automatic citation extraction** from debate messages using regex patterns
- **Confidence scoring** (0.0-1.0) for citation quality
- **Clickable citation badges** in theater and transcript modes
- **Direct links** from debate messages to full primary texts
- **Backend API** with slug-based text routing

### 💳 Subscription & Payments
- **Credit-based system:** Debates cost credits based on participants/rounds/depth
- **Trial period:** 7 days, 15 credits auto-granted on registration
- **Stripe integration:** Student ($10/mo), Scholar ($25/mo), Enterprise (custom)
- **Usage tracking:** View credit history, most-used personas, debate statistics

### 🎨 User Experience
- **Responsive design:** Mobile-friendly Material-UI components
- **Real-time updates:** SSE for live debate generation (95% fewer HTTP requests vs polling)
- **Loading states:** Skeleton screens, progress indicators, optimistic UI
- **Error handling:** Graceful degradation, image fallbacks, retry logic
- **Account management:** Subscription status, credit balance, payment history

---

## 📊 Project Stats

| Metric | Value | Quality |
|--------|-------|---------|
| **Overall Grade** | B+ (87/100) | Production-ready |
| **Backend Test Coverage** | 84% (564 tests) | Excellent |
| **Frontend Test Coverage** | 94% (218 tests) | Outstanding |
| **Debate Quality** | 8.9/10 average | High |
| **Personas** | 196 across 29 categories | Comprehensive |
| **Primary Texts** | 300-600+ texts | Extensive |
| **API Endpoints** | 45+ documented | Complete |

See [STATUS.md](STATUS.md) for detailed development history and [Comprehensive_Project_Review_10_25_2025.md](Comprehensive_Project_Review_10_25_2025.md) for full architectural assessment.

---

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose (recommended)
- OR: Python 3.10+, Node.js 18+, PostgreSQL, Redis (manual setup)

### Option 1: Docker Setup (Recommended)

```bash
# Clone repository
git clone <repository-url>
cd philosophical-debates

# Start all services
make start

# Load personas into database (REQUIRED - only once)
make load-personas

# Visit the app
open http://localhost:3001
```

**URLs:**
- Frontend: http://localhost:3001
- Backend API: http://localhost:8001/api/ (via nginx on port 80 inside Docker)
- Django Admin: http://localhost:8001/admin/
- API Docs (Swagger): http://localhost:8001/api/docs/
- Flower (Celery monitoring): http://localhost:5555

### Option 2: Manual Setup

See [QUICKSTART.md](QUICKSTART.md) for detailed manual setup instructions.

**Critical Step:** After setup, run `python manage.py load_personas` to import all 196 personas from markdown files into PostgreSQL. The app won't have any personas until you run this command.

---

## 📚 Key Documents

| Document | Purpose |
|----------|---------|
| [QUICKSTART.md](QUICKSTART.md) | Detailed setup guide (Docker + manual) |
| [GITHUB_SETUP.md](GITHUB_SETUP.md) | GitHub repository setup, CI/CD, workflows, templates |
| [CLAUDE.md](CLAUDE.md) | AI assistant project guide (comprehensive) |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design, ADRs, dual debate system |
| [STATUS.md](STATUS.md) | Current state, recent changes, metrics |
| [NEXT_STEPS.md](NEXT_STEPS.md) | 5 critical production blockers (9 hours) |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Production deployment to AWS Lightsail + Vercel |
| [MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md) | 40+ development commands reference |
| [Comprehensive_Project_Review_10_25_2025.md](Comprehensive_Project_Review_10_25_2025.md) | Full architectural assessment |

---

## 🔌 API Endpoints

### Authentication
```
POST   /api/auth/register/              # Register new user (auto-starts 7-day trial)
POST   /api/auth/login/                 # Login (returns JWT + sets HttpOnly cookie)
POST   /api/auth/refresh/               # Refresh access token
POST   /api/auth/logout/                # Logout (clears cookie)
GET    /api/auth/user/                  # Get current user info with credits
```

### Personas
```
GET    /api/personas/                   # List all personas (paginated, filterable)
GET    /api/personas/by_category/       # Personas grouped by category
GET    /api/personas/{slug}/            # Persona details with primary texts
POST   /api/persona-requests/           # Request new persona addition
```

### Debates
```
GET    /api/debates/                    # List user's debates
POST   /api/debates/                    # Create debate (deducts credits)
GET    /api/debates/{slug}/             # Debate details with all messages
POST   /api/debates/{slug}/generate/    # Trigger async generation (Celery task)
GET    /api/debates/{slug}/stream/      # SSE endpoint for real-time updates
GET    /api/debates/{slug}/export/      # Export as PDF with citations
```

### Primary Texts
```
GET    /api/texts/                      # List texts (filters: category, era, author)
GET    /api/texts/{slug}/               # Full text with all sections
GET    /api/texts/{slug}/sections/      # Get sections only
GET    /api/texts/{slug}/citations/     # Citations referencing this text
GET    /api/sections/{id}/              # Single section detail
```

### Payments (Stripe)
```
POST   /api/payments/create-checkout/   # Create Stripe checkout session
POST   /api/payments/webhook/           # Stripe webhook handler
GET    /api/payments/subscription/      # Current subscription status
POST   /api/payments/cancel/            # Cancel subscription
GET    /api/payments/history/           # Payment history
```

Full API documentation with examples: http://localhost:8001/api/docs/

---

## 🛠️ Development

### Common Commands

```bash
# Service management
make start              # Start all services (Docker)
make stop               # Stop all services
make restart            # Restart all services
make status             # Check service status

# Testing
make test               # Run all tests (backend + frontend)
make test-coverage      # Run tests with coverage report
make test-backend       # Backend tests only
make test-frontend      # Frontend tests only

# Database
make db-migrate         # Run Django migrations
make db-reset           # Reset database (WARNING: destroys data)
make load-personas      # Load 196 personas from markdown → PostgreSQL

# Logs
make logs               # All service logs
make backend-logs       # Backend logs only
make frontend-logs      # Frontend logs only
make celery-logs        # Celery worker logs
```

See [MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md) for 40+ available commands.

### Project Structure

```
philosophical-debates/
├── backend/                    # Django REST Framework API
│   ├── debates/                # Debate generation, SSE streaming
│   ├── personas/               # 196 persona definitions + API
│   ├── texts/                  # Primary text library + citations
│   ├── users/                  # Authentication, subscriptions
│   ├── payments/               # Stripe integration
│   ├── health/                 # Kubernetes health checks
│   └── config/                 # Django settings, Celery config
├── frontend/                   # Next.js 15 + TypeScript
│   ├── app/                    # App Router pages
│   ├── components/             # React components
│   ├── lib/                    # API client, hooks, utilities
│   └── __tests__/              # Vitest + React Testing Library
├── docker-compose.yml          # Base Docker config
├── docker-compose.override.yml # Development overrides (auto-merges)
├── docker-compose.prod.yml     # Production configuration
├── Makefile                    # Development commands (start here!)
└── archive/                    # Historical docs and logs
```

---

## 🔐 Security Features

- **HttpOnly cookies** for auth tokens (XSS protection)
- **Input sanitization** with bleach library (3-layer defense)
- **CSRF protection** via Django middleware
- **JWT authentication** with automatic refresh
- **SQL injection protection** via Django ORM
- **Stripe webhook signature verification** (⚠️ needs verification - see NEXT_STEPS.md)
- **Rate limiting** on debate generation
- **Atomic credit transactions** (⚠️ race condition fix needed - see NEXT_STEPS.md)

93 security tests implemented and passing.

---

## 📈 Production Readiness

**Current Grade:** B+ (87/100)
**Target:** A- (91/100) after 5 critical fixes (9 hours)

### Production Blockers (See [NEXT_STEPS.md](NEXT_STEPS.md))
1. ⚠️ **Credit race condition** (2h) - Users can double-spend credits
2. ⚠️ **Citation integration** (3h) - citation_markup.py not called in generator
3. ⚠️ **Celery task timeouts** (1h) - Tasks can hang indefinitely
4. ⚠️ **Stripe webhook verification** (0-2h) - Needs confirmation
5. ⚠️ **Deployment config** (1h) - docker-compose.override.yml risk

### Deployment
- **Backend:** AWS Lightsail (Docker Compose)
- **Frontend:** Vercel (auto-deploy from git)
- **Database:** PostgreSQL on Lightsail
- **Domain:** theinfinitedebate.com (ICDSoft)

See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment guide.

---

## 🧪 Testing

**Backend:** pytest-django with 564 tests, 84% coverage
```bash
cd backend
docker compose exec web pytest --cov
```

**Frontend:** Vitest + React Testing Library with 218 tests, 94% coverage
```bash
cd frontend
npm test
```

**Combined:**
```bash
make test-coverage
```

---

## 🤝 Contributing

This is currently a personal project. For questions or collaboration inquiries, see the GitHub repository.

---

## 📄 License

TBD

---

## 🔗 Additional Resources

- **Architecture Deep Dive:** [ARCHITECTURE.md](ARCHITECTURE.md) - 1,225 lines, 22 sections
- **Comprehensive Review:** [Comprehensive_Project_Review_10_25_2025.md](Comprehensive_Project_Review_10_25_2025.md)
- **Persona System:** See CLAUDE.md for dual markdown/database architecture
- **Development Status:** [STATUS.md](STATUS.md) for weekly progress updates

---

**Built with** Django • Next.js • PostgreSQL • Redis • Celery • Docker • Anthropic Claude API • Stripe
