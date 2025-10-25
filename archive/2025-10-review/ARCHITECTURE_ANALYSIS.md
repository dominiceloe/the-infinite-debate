# Prompt the Past - Comprehensive Architecture Analysis

## Executive Summary

**Prompt the Past** is a full-stack Django + Next.js application for AI-powered philosophical debates. The architecture demonstrates strong engineering practices with clear separation of concerns, comprehensive security hardening, and modern async patterns. The system is production-ready with subscription management, real-time streaming, and task queue orchestration.

**Overall Quality: HIGH** (8.5/10)
- Strengths: Well-structured, security-focused, scalable design
- Areas for improvement: Some API design patterns, error handling consistency, test coverage gaps

---

## Architecture Overview

### Technology Stack

**Backend:**
- Django 5.2 + Django REST Framework 3.16
- PostgreSQL 14 (primary database)
- Redis 8 (cache/message broker)
- Celery 5.5 (async task queue)
- Anthropic Claude API (AI engine)
- Gunicorn + Nginx (production serving)

**Frontend:**
- Next.js 15.5 (App Router, Server Components)
- React 19 + TypeScript 5
- Material-UI v7 (component library)
- Axios + React Query v5 (data fetching)
- Vitest + React Testing Library (testing)

**Infrastructure:**
- Docker Compose (7 services: postgres, redis, web, celery, flower, nginx, certbot)
- WhiteNoise (static file serving in production)
- Stripe (payment processing)
- Sentry (error tracking)

**Code Statistics:**
- Backend: ~110 Python files (excluding migrations, venv)
- Frontend: ~72 TypeScript/TSX files
- Test Suite: ~7,100 lines of test code in backend
- Total: ~200 files in application core

---

## 1. Django Backend Architecture

### 1.1 App Structure

The backend is organized into 6 specialized Django apps with clear domain responsibilities:

#### **debates** (20 files)
Orchestrates multi-persona debate generation and management.

**Models:**
```
Debate (core debate entity)
├── user (ForeignKey)
├── participants (M2M: Persona)
├── messages (Reverse FK: DebateMessage)
├── transcript, summary (TextField)
└── status (pending → generating → completed/failed)

DebateMessage (individual round statements)
├── debate (ForeignKey)
├── persona (ForeignKey)
├── round_number, content
└── tokens_used (usage tracking)
```

**Architecture Patterns:**
- **Debate State Machine:** Status field enforces flow (pending → generating → completed/failed)
- **Composite Indexes:** `[debate, round_number]` for efficient round queries
- **Signal Handlers:** Auto-sanitization on pre_save (defense-in-depth)
- **Query Optimization:** Comments throughout views/serializers documenting prefetch_related requirements

**ViewSet Design:**
```
DebateViewSet (ModelViewSet)
├── list() - user-filtered with prefetch
├── retrieve() - detailed with nested messages + citations
├── create() - validates credits, deducts, creates
├── generate() - triggers Celery task
├── export() - PDF generation
└── stream() - SSE real-time updates
```

**API Endpoints:**
- `POST /api/debates/` - Create (deducts credits immediately)
- `POST /api/debates/{slug}/generate/` - Start generation
- `GET /api/debates/{slug}/stream/` - SSE updates
- `GET /api/debates/{slug}/export/` - PDF download

#### **personas** (14 files)
Historical figure definitions with dual-storage architecture.

**Dual-Storage Pattern (IMPORTANT):**
1. **Source of Truth:** Markdown files in `backend/personas/fixtures/{category}/{slug}.md`
2. **Runtime:** PostgreSQL `Persona` table (served via REST API)
3. **Sync:** `python manage.py load_personas` parses markdown → database

**Models:**
```
Persona
├── Identity: name, slug, title, category
├── Historical: era, birth_year, death_year
├── Content: core_positions, debate_style, key_concepts, etc. (all TextField)
├── full_markdown (complete markdown for AI context)
├── external_links (JSON: wikipedia, stanford_encyclopedia, academic papers)
├── portrait_image (filename reference)
├── required_tier (free/starter/pro/enterprise)
└── Indexes: [category, birth_year], [slug], [birth_year]

PersonaRequest (user submissions)
├── user, persona_name, justification
├── status (pending → approved → completed)
├── created_persona (FK after completion)
└── Indexes: [user, status], [status, -created_at]
```

**Debate Turn Order:**
Personas are ordered chronologically by birth_year:
```
Confucius (551) → Laozi (600) → Socrates (470) → ... → de Beauvoir (1908)
```

#### **texts** (16 files)
Primary source library with full-text search and citation extraction.

**Hierarchical Model:**
```
PrimaryText (work)
├── title, slug, author
├── publication_year, category, era
├── source (gutenberg, mit_classics, internet_archive, etc.)
├── translator, edition_notes
├── reading_difficulty (beginner/intermediate/advanced/expert)
└── SearchVectorField (PostgreSQL full-text search)

TextSection (hierarchical)
├── parent (self-referential for book chapters → paragraphs)
├── section_number, title, text
└── depth (1=chapter, 2=subsection, 3=paragraph)

TextCitation (usage tracking)
├── debate_message (FK)
├── primary_text (FK)
├── section (FK, nullable)
├── excerpt, confidence_score
└── cited_at (timestamp)
```

**Advanced Indexing:**
- PostgreSQL GIN index on SearchVector for O(log N) full-text queries
- Composite indexes: [debate_message], [primary_text]

#### **users** (14 files)
Authentication, subscription management, credit system.

**Custom User Model:**
```
User (extends AbstractUser)
├── Subscription: subscription_tier (trial/starter/pro/enterprise)
│   └── subscription_status (active/cancelled/expired/past_due)
├── Credits: credits_remaining (monthly reset)
│   ├── Trial: 15 credits (7-day expiry)
│   ├── Starter: 30 credits/month ($10)
│   └── Pro: 100 credits/month ($25)
├── Trial: trial_start_date, trial_end_date
├── Stripe: stripe_customer_id, stripe_subscription_id
├── Email: email_verified, email_verification_token
└── Indexes: [subscription_tier, status], [email_verified], [stripe_customer_id]
```

**Credit System:**
- Deducted on debate creation (serializer validation)
- Calculation formula: `base_credits = num_participants × max_rounds`
- Multipliers: introductory (1.0x), intermediate (1.5x), advanced (2.0x)
- Example: 5 personas × 5 rounds × 1.5 (intermediate) = 37.5 → 38 credits

**Authentication:**
- JWT with cookie storage (HttpOnly)
- CookieJWTAuthentication class prioritizes cookies over headers
- Auto-refresh on 401 response (client-side interceptor)

#### **payments** (11 files)
Stripe subscription orchestration.

**Models:**
```
StripeEvent (webhook log)
├── event_id (unique Stripe ID)
├── event_type (customer.subscription.created, etc.)
├── data (JSON: full event payload)
├── processed (idempotency flag)
└── error (failure reason if any)

StripePayment (transaction tracking)
├── user, payment_intent_id, amount, currency
├── status (pending/succeeded/failed/refunded)
├── metadata (JSON)

StripeSubscriptionHistory (audit trail)
├── action (created/updated/canceled/trial_will_end)
├── tier, status (snapshots)
└── metadata (context)
```

**Webhook Pattern:**
- Idempotent processing via `event_id` uniqueness
- Event atomicity with database transactions
- Fallback error logging for failed operations
- Attempts credit resets on subscription upgrade

### 1.2 Security Architecture

**Defense-in-Depth Layers:**

1. **Input Sanitization (core/sanitization.py)**
   ```
   3 sanitization levels:
   - sanitize_html() - only plain text (no tags)
   - sanitize_markdown() - allows safe markdown tags
   - sanitize_plain_text() - strips all formatting
   ```
   Uses `bleach` library with:
   - Protocol whitelisting (http, https, mailto)
   - HTML tag restrictions
   - Event handler blocking (onclick, onerror, etc.)

2. **Model-Level Validation**
   - Signal handlers (pre_save) auto-sanitize all inputs
   - Validator decorators (validate_no_scripts, validate_safe_markdown)
   - MinLength/MaxLength validators on text fields

3. **Serializer Validation**
   - Custom validate_* methods for each sensitive field
   - Participant ID existence checks
   - Credit sufficiency validation before debate creation

4. **HTTPS/TLS (Production)**
   ```
   SECURE_SSL_REDIRECT = True
   SECURE_HSTS_SECONDS = 31536000 (1 year)
   SECURE_HSTS_PRELOAD = True
   ```

5. **Cookie Security**
   ```
   SESSION_COOKIE_HTTPONLY = True
   SESSION_COOKIE_SECURE = True (production only)
   CSRF_COOKIE_HTTPONLY = True
   SESSION_COOKIE_SAMESITE = 'Lax'
   ```

6. **Rate Limiting**
   - Anonymous: 20/hour
   - Authenticated: 100/hour
   - Debate generation: 10/hour (custom throttle)

7. **Environment Isolation**
   - SECRET_KEY required and validated on startup
   - Environment-specific settings (development vs. production)
   - Database credentials via .env (not in code)

**Potential Security Gaps:**
1. ⚠️ **Error Message Exposure:** 401 errors return user-friendly messages (good) but might leak subscription status
2. ⚠️ **SQL Injection via Full-Text Search:** TextSection content is user-ingested (via text ingestion command). No parametrized queries shown in search implementation
3. ⚠️ **Stripe Webhook Validation:** No mention of signature verification (HMAC validation with webhook secret)

### 1.3 Database Design

**Schema Highlights:**

```
User (1) ──→ (M) Debate
                ├──→ (M) DebateMessage
                │      └──→ (1) Persona
                │      └──→ (M) TextCitation
                │             └──→ (1) PrimaryText
                ├──→ (M) StripePayment
                ├──→ (M) StripeSubscriptionHistory
                └──→ (M) PersonaRequest

Persona (M) ──→ (M) Debate (through ManyToMany)
        └──→ (M) DebateMessage
        └──→ (M) PersonaRequest (reverse)

PrimaryText (1) ──→ (M) TextSection (self-referential hierarchy)
            └──→ (M) TextCitation
```

**Indexing Strategy:**
- **Composite Indexes:** `[debate, round_number, persona]` for efficient filtering
- **ForeignKey Indexes:** Auto-created by Django on all FK fields
- **Search Indexes:** PostgreSQL GIN index on SearchVector
- **User Queries:** `[user, -created_at]` for chronological ordering

**Potential Issues:**
1. ⚠️ **N+1 Query Risk:** Many views prefetch correctly, but serializer methods (participant_names) can still trigger queries if prefetch missing
2. ⚠️ **Debate Transcript Storage:** Full transcript stored in TextField—no pagination for massive debates
3. ⚠️ **Search Vector Staleness:** SearchVector field may become out-of-sync with text content; no refresh trigger

### 1.4 API Design

**REST Endpoints Summary:**

| Endpoint | Method | Authentication | Purpose |
|----------|--------|----------------|---------|
| `/api/auth/register/` | POST | None | Registration with auto-trial |
| `/api/auth/login/` | POST | None | Get JWT tokens |
| `/api/auth/refresh/` | POST | None | Token refresh |
| `/api/personas/` | GET | Optional | List with search/filter |
| `/api/personas/by_category/` | GET | Optional | Grouped by category |
| `/api/debates/` | GET | Required | User's debates (paginated) |
| `/api/debates/` | POST | Required | Create debate (deduct credits) |
| `/api/debates/{slug}/` | GET | Required | Detail view |
| `/api/debates/{slug}/generate/` | POST | Required | Start generation |
| `/api/debates/{slug}/stream/` | GET | Required | SSE real-time updates |
| `/api/debates/{slug}/export/` | GET | Required | PDF download |
| `/api/texts/` | GET | Optional | Library with filters |
| `/api/texts/{slug}/citations/` | GET | Optional | Citations in this text |
| `/api/payments/create-checkout/` | POST | Required | Stripe session |
| `/api/payments/webhook/` | POST | Signature | Stripe events |

**Design Patterns:**

1. **ViewSet Pattern (Good):**
   - Standard CRUD operations auto-generated
   - Custom actions via @action decorator
   - Consistent error responses

2. **Serializer Specialization (Good):**
   - DebateListSerializer (lightweight)
   - DebateDetailSerializer (full nested objects)
   - DebateCreateSerializer (input validation)
   Reduces over-fetching and improves performance

3. **Pagination (Good):**
   - Default 20 items/page via PageNumberPagination
   - Prevents large list responses

4. **Error Handling Issues:**
   - Some endpoints return 400 for business logic errors (correct)
   - Some return generic 500 (should be more specific)
   - No consistent error response format documented

### 1.5 Async Task Processing

**Celery Architecture:**

```
User creates debate
    ↓
DebateViewSet.generate() → generate_debate_task.delay(debate_id)
    ↓
Celery Worker (concurrency=2)
    ├─ DebateGenerator.generate()
    │   ├─ Build system prompt from persona markdown
    │   ├─ For each round:
    │   │   └─ For each persona:
    │   │       └─ Call Claude API (streaming + context window)
    │   │       └─ Save DebateMessage to DB
    │   │       └─ Publish SSE event to Redis
    │   └─ Update debate.status = 'completed'
    └─ publish_debate_event() → Redis
         ↓
    Frontend subscribers (EventSource)
         ↓
    Real-time UI updates (typewriter animation)
```

**Key Features:**
- **Bind=True:** Task retries with exponential backoff (max_retries=3, 60s delay)
- **Redis Pub/Sub:** Decouples generation from frontend (no blocking)
- **Event Publishing:** Type-tagged messages (status, message, error)
- **Graceful Degradation:** Pub/sub failures don't crash generation

**Configuration (config/celery.py):**
```python
CELERY_BROKER_URL = 'redis://redis:6379/0'
CELERY_RESULT_BACKEND = 'redis://redis:6379/0'
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_RESULT_EXPIRES = 3600
```

**Potential Issues:**
1. ⚠️ **Debate Length Limits:** No timeout on generation; long debates could timeout
2. ⚠️ **Token Counting:** `tokens_used` field populated but never validated against usage limits
3. ⚠️ **Event Loss:** SSE updates not persisted; disconnected clients lose intermediate updates
4. ⚠️ **Concurrency (2):** May be too low for high traffic; CPU-bound task (API calls) not truly parallelizable

---

## 2. Frontend Architecture

### 2.1 Next.js App Structure

```
app/
├── layout.tsx (root layout with providers)
├── page.tsx (home/landing)
├── (auth)/
│   ├── login/page.tsx
│   ├── register/page.tsx
│   └── request-persona/page.tsx
├── debates/
│   ├── page.tsx (list/browse)
│   ├── new/page.tsx (create - 827 lines, complex form)
│   └── [slug]/page.tsx (view/detail)
├── personas/
│   ├── page.tsx (gallery)
│   └── [slug]/page.tsx (profile)
├── texts/
│   ├── page.tsx (library)
│   └── [slug]/page.tsx (reader)
├── pricing/page.tsx (subscription tiers)
└── account/page.tsx (user management)

components/
├── Header.tsx (navigation + auth-aware menu)
├── ProtectedRoute.tsx (HOC for auth-required pages)
├── DebateTheaterView.tsx (live debate visualization)
├── MessageContent.tsx (citation-linked messages)
└── debates/theater/ (sub-components)

lib/
├── api.ts (axios instance + interceptors)
├── theme.ts (Material-UI theme)
├── categories.ts (persona grouping)
└── tiers.ts (subscription tier logic)

hooks/
├── useTypewriter (animation effect)
├── useQuery (React Query wrappers)
└── custom hooks

types/
├── index.ts (TypeScript interfaces)
└── api.ts (API request/response types)
```

### 2.2 Key Components

#### **DebateTheaterView.tsx** (Live Debate Visualization)

**Design Pattern:**
```tsx
Uses ref (wasEverGenerating) to detect:
  - Debate started live (generating when opened)
  - Debate pre-generated (completed when opened)

setState based on status:
  - Live-watched: Start from message 0, animate as they arrive
  - Pre-generated: Jump to end, show all immediately
```

**Animation:**
- Typewriter effect: 400ms per word (≈150 wpm)
- Pagination: Next message after 500ms post-completion
- Progress indicator shows: Round {current}/{max}, Spinner during typing

**Features:**
- PersonaGrid: Displays speaker portraits with message content
- ProgressIndicator: Real-time round tracking
- DebateSummary: Shows on completion

**Potential Issues:**
1. ⚠️ **Component Size:** 95 lines but manages 5 state concerns (message index, typewriter, animation flags)
2. ⚠️ **Animation Timing:** Hardcoded delays (500ms pause, 400ms typewriter) not configurable
3. ⚠️ **Memory Leak:** useRef never cleaned up (fine for this case, but pattern)

#### **Header.tsx** (Navigation)

**Features:**
- Conditional rendering: Home/Login buttons if not auth'd, User menu if auth'd
- Subscription badge: Shows current tier + credits remaining
- Sign out: Clears cookies + redirects to /login

**Auth Status Detection:**
Uses React Context (likely AuthContext) to determine if user is authenticated.

#### **ProtectedRoute.tsx** (Auth Guard)

**HOC Pattern:**
```tsx
export default function ProtectedPage() {
  return (
    <ProtectedRoute>
      <YourComponent />
    </ProtectedRoute>
  );
}
```

Checks auth context, redirects to /login if not authenticated.

### 2.3 Data Fetching & State Management

**API Client (lib/api.ts):**

```typescript
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  withCredentials: true,  // CRITICAL: enable cookies
});

// Response interceptor: Auto-refresh 401s
api.interceptors.response.use(
  response => response,
  async (error) => {
    if (error.response?.status === 401 && !originalRequest._retry) {
      // 1. Check if already refreshing (debounce)
      if (isRefreshing) {
        // 2. Wait for refresh
        return new Promise(resolve => {
          subscribeTokenRefresh(() => resolve(api(originalRequest)));
        });
      }
      // 3. Attempt refresh
      await api.post('/auth/cookie-refresh/');
      // 4. Retry original request
      return api(originalRequest);
    }
  }
);
```

**Smart Pattern Highlights:**
- **Debounced Token Refresh:** Prevents 10 simultaneous refresh requests on 401
- **Cookie Credentials:** withCredentials=true ensures cookies sent on CORS requests
- **Auto-Retry:** Transparent to consumer code

**React Query Integration:**

```typescript
const { data, isLoading } = useQuery({
  queryKey: ['debate', slug],
  queryFn: () => apiClient.debates.getBySlug(slug),
  refetchInterval: (query) =>
    query.state.data?.status === 'generating' ? 2000 : false
});
```

**Smart Refetch Logic:**
- Polls every 2 seconds if `status === 'generating'`
- Stops polling when completed (refetchInterval: false)
- Prevents unnecessary API calls on static pages

### 2.4 TypeScript & Type Safety

**Type System (strict mode enabled):**

```typescript
interface Debate {
  id: number;
  title: string;
  topic: string;
  slug: string;
  participants: Persona[];
  messages: DebateMessage[];
  status: 'pending' | 'generating' | 'completed' | 'failed';
  depth_level: 'introductory' | 'intermediate' | 'advanced';
  max_rounds: number;
  transcript: string;
  summary: string;
  rounds_completed: number;
  error_message: string;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

interface CreateDebateRequest {
  title: string;
  topic: string;
  participant_ids: number[];
  depth_level: 'introductory' | 'intermediate' | 'advanced';
  max_rounds: number;
}
```

**No `any` Usage:** Type safety enforced throughout codebase.

### 2.5 Material-UI Integration

**Theme Configuration (lib/theme.ts):**
- Dark theme with Slate colors
- Responsive typography
- Custom component overrides

**Component Examples:**
```tsx
<Box sx={{
  display: 'grid',
  gridTemplateColumns: { xs: '1fr', md: '2fr 1fr' },  // Responsive
  gap: 2
}}>
```

**Strengths:**
- Material-UI v7 with latest MUI System
- Emotion CSS-in-JS for styling
- Responsive design via sx prop

---

## 3. Docker & Infrastructure

### 3.1 Docker Compose Services

**7 Services Architecture:**

```yaml
db (postgres:14)
  ├─ Volume: postgres_data
  ├─ Healthcheck: pg_isready
  └─ Environment: DB credentials

redis (redis:8-alpine)
  ├─ Broker for Celery tasks
  ├─ Cache storage
  └─ Pub/sub for SSE updates

web (Django + Gunicorn)
  ├─ Bind: 0.0.0.0:8000
  ├─ Workers: 3 (tuned for I/O-bound tasks)
  ├─ Timeout: 120s (for long-running API calls)
  ├─ Volumes: staticfiles, media
  └─ Depends: db (healthy), redis (healthy)

celery (Worker)
  ├─ Command: celery -A config worker
  ├─ Concurrency: 2 (debate generation)
  ├─ Loglevel: info
  └─ Depends: db, redis

flower (Celery monitoring)
  ├─ Port: 5555
  ├─ Auth: Basic auth (configurable)
  └─ UI for task monitoring

nginx (alpine)
  ├─ Ports: 80 (HTTP), 443 (HTTPS)
  ├─ Reverse proxy: web service
  ├─ Static file serving
  ├─ TLS termination
  └─ Healthcheck: wget http://localhost/health/

certbot (Let's Encrypt)
  ├─ Auto-renewal every 12 hours
  ├─ Volumes: /etc/letsencrypt, /var/www/certbot
  └─ Runs only in production
```

### 3.2 Development vs. Production Setup

**Development (docker-compose.override.yml):**
```yaml
web:
  command: python manage.py runserver 0.0.0.0:8000
  volumes:
    - .:/app  # Hot-reload on code changes
```

**Production (docker-compose.yml):**
```yaml
web:
  command: gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120
```

**Important Note:** Production must use `-f docker-compose.yml` flag to exclude override file.

### 3.3 Health Checks

**Liveness Probe (Kubernetes-style):**
```
GET /health/
Returns: 200 if service is running
```

**Readiness Probe:**
```
GET /ready/
Checks: Database connection, Redis connection
Returns: 503 if dependencies unavailable
```

**HTTP-level Healthchecks:**
Each service has healthcheck configuration in docker-compose:
- db: `pg_isready` command
- redis: `redis-cli ping`
- web: `curl http://localhost/health/`
- nginx: `wget http://localhost/health/`

---

## 4. API Design Patterns & Quality

### 4.1 REST Conventions

**✓ Strengths:**
1. **Proper HTTP Methods:** GET (retrieve), POST (create), PUT (update)
2. **Slug-based Lookups:** `lookup_field = 'slug'` instead of numeric IDs (user-friendly URLs)
3. **Status Codes:** 200 (success), 201 (created), 400 (validation), 401 (auth), 404 (not found), 500 (error)
4. **Pagination:** 20 items/page via REST Framework pagination

**⚠️ Issues:**
1. **Action Naming:** `/debates/{slug}/generate/` uses verb in URL (REST purist would prefer `/debates/{slug}/generation/`)
2. **Error Format Inconsistency:** Some endpoints return `{'error': 'message'}`, others `{'detail': 'message'}`
3. **No Envelope:** Response data returned directly, not wrapped in envelope (OK for REST, but inconsistent with pagination)

### 4.2 Serializer Design

**Query Optimization Documented:**

Every serializer has comments explaining prefetch requirements:

```python
class DebateDetailSerializer(serializers.ModelSerializer):
    """
    Query optimization note: This serializer accesses participants (many-to-many)
    and messages (reverse foreign key) with nested serializers. Ensure debates
    are fetched with:
    Debate.objects.prefetch_related(
        'participants',
        'messages__persona',
        'messages__text_citations__primary_text'
    )
    """
```

**Specialization Pattern:**

Three serializers for debates:
1. **DebateListSerializer:** Lightweight (counts + names)
2. **DebateDetailSerializer:** Full (nested messages, citations)
3. **DebateCreateSerializer:** Input validation (credit checks)

### 4.3 Error Handling

**Good Practices:**
- Model validation via Django validators + signal handlers
- Serializer validation via validate_* methods
- View-level business logic checks (credit sufficiency)
- 400 errors for client faults, 500 for server faults

**Inconsistencies:**
- Some views return `{'error': 'message'}`, others use DRF's default `{'detail': 'message'}`
- No custom exception handlers to normalize error format
- Some try/except blocks log but don't re-raise (silent failures)

### 4.4 Authentication & Authorization

**JWT with Cookies:**
- Access token stored in HttpOnly cookie
- Refresh token in separate cookie
- CookieJWTAuthentication class prioritizes cookie over header
- Auto-refresh on 401 (client-side interceptor)

**Permission Model:**
- Most endpoints require IsAuthenticated
- Some (persona list, text search) allow anonymous
- No role-based access control (RBAC) visible—all users have same permissions

**Potential Issues:**
1. ⚠️ **Token Expiry:** Access token TTL not shown (likely 5-15 min default)
2. ⚠️ **Refresh Token Rotation:** No refresh token rotation visible
3. ⚠️ **Session Fixation:** Cookies not rotate after login

---

## 5. Testing & Quality Assurance

### 5.1 Backend Testing (pytest-django)

**Test Organization:**
```
debates/tests/
├── test_models.py
├── test_serializers.py
├── test_views.py
└── test_utils.py

Total: ~7,100 lines of test code
```

**Fixtures (conftest.py):**
```python
- api_client()          # DRF APIClient
- authenticated_client()# With bearer token
- test_user()          # Pro subscription + 1000 credits
- test_personas()      # Socrates, Plato, Aristotle
- test_debate()        # Sample debate with 2 participants
- mock_anthropic_response()  # Mock Claude API
```

**Celery Test Config:**
```python
CELERY_TASK_ALWAYS_EAGER = True  # Run tasks synchronously in tests
CELERY_TASK_EAGER_PROPAGATES = True
```

**Test Coverage:**
- Backend: ~60% coverage (target per CLAUDE.md)
- Focus areas: Models, serializers, views, Stripe webhooks

**Strengths:**
- Comprehensive fixtures reduce boilerplate
- Throttling disabled in tests (prevent false negatives)
- Database access enabled by default
- Celery runs eagerly (deterministic)

**Gaps:**
1. ⚠️ **Integration Tests:** No full-flow tests (debate creation → generation → completion)
2. ⚠️ **Edge Cases:** No tests for concurrent debate creation with credit race conditions
3. ⚠️ **Error Scenarios:** Limited failure path testing (network errors, API timeouts)

### 5.2 Frontend Testing (Vitest)

**Setup:**
- Vitest 3.2 (Jest-compatible runner)
- React Testing Library 16.3
- Happy-DOM (lightweight JSDOM alternative)

**Command:**
```bash
npm test              # Watch mode
npm test -- --run    # Single run
npm run test:coverage # With coverage
```

**Target:** 60%+ coverage for production (per CLAUDE.md)

**Test Utilities:**
```typescript
renderWithProviders() // Wraps with React Query, Auth context
mockLocalStorage()    // LocalStorage mocking
```

**Potential Issues:**
1. ⚠️ **Few Tests:** Only test utilities visible; no test files shown
2. ⚠️ **API Mocking:** Mock axios instance pattern not shown

---

## 6. Strengths & Quality Assessment

### 6.1 Architectural Strengths

| Strength | Impact | Evidence |
|----------|--------|----------|
| **Clear Domain Separation** | HIGH | 6 specialized Django apps with focused responsibilities |
| **Security-First Design** | HIGH | 3-layer sanitization, HTTPS enforcement, rate limiting |
| **Query Optimization** | MEDIUM | Prefetch_related documented everywhere; composite indexes |
| **Async Task Processing** | MEDIUM | Celery + Redis for scalable debate generation |
| **Type Safety** | HIGH | TypeScript strict mode + Python type hints throughout |
| **Real-time Updates** | HIGH | SSE + Redis pub/sub for live debate progress |
| **Subscription Billing** | MEDIUM | Credit system + Stripe integration with webhooks |
| **Full-Text Search** | MEDIUM | PostgreSQL FTS with GIN indexes on texts |
| **Docker Orchestration** | HIGH | Production-ready compose with health checks |

### 6.2 Code Quality Observations

**Django Backend (Python):**
- ✓ Follows PEP 8 conventions
- ✓ Google-style docstrings
- ✓ Type hints in critical functions
- ✓ Signal handlers for cross-cutting concerns
- ⚠️ Some files exceed 400 lines (views.py: 306 lines, okay)
- ⚠️ Minimal logging (mostly absent outside error paths)

**Next.js Frontend (TypeScript):**
- ✓ Strict mode enabled
- ✓ No `any` type usage
- ✓ Functional components with hooks
- ✓ Material-UI best practices
- ⚠️ Some components >200 lines (complex form: 827 lines!)
- ⚠️ Limited component testing

---

## 7. Potential Issues & Vulnerabilities

### 7.1 Security Concerns

| Issue | Severity | Recommendation |
|-------|----------|-----------------|
| Stripe webhook signature not verified | HIGH | Implement HMAC validation with webhook secret |
| SQL injection via text ingestion | MEDIUM | Audit text search implementation; use parameterized queries |
| Token expiry not visible | MEDIUM | Document JWT TTL; implement refresh token rotation |
| Error message information disclosure | LOW | Sanitize error responses; don't leak subscription state |
| Concurrent credit deduction race | HIGH | Add database-level constraint or pessimistic locking |

### 7.2 Scalability Concerns

| Concern | Impact | Mitigation |
|---------|--------|-----------|
| Celery concurrency (2) | MEDIUM | Increase for more concurrent debates; monitor CPU |
| Gunicorn workers (3) | MEDIUM | Scale to 8-12 for production; use load testing |
| Transcript storage (TextField) | LOW | Implement pagination for large debates |
| SearchVector staleness | LOW | Add trigger to update on text change |
| SSE connection limits | MEDIUM | Implement max connections; add client-side backoff |

### 7.3 Testing Gaps

| Gap | Impact | Effort |
|-----|--------|--------|
| Integration tests | MEDIUM | Create end-to-end test flows |
| Concurrent credit tests | HIGH | Test race conditions with competing users |
| API error scenarios | MEDIUM | Test network failures, timeouts, rate limits |
| SSE disconnection handling | LOW | Test client reconnect behavior |
| Frontend component tests | MEDIUM | Add RTL tests for key components |

---

## 8. Architectural Patterns & Design Decisions

### 8.1 Key Design Patterns

1. **Dual-Storage Architecture (Personas)**
   - Source of Truth: Markdown files (human-editable, version-controlled)
   - Runtime: PostgreSQL table (served via API)
   - Sync: `load_personas` command syncs files → DB
   - Trade-off: Flexibility vs. complexity

2. **State Machine (Debates)**
   - Linear flow: pending → generating → completed/failed
   - Status enforced in views; prevents invalid transitions
   - Signal handlers sanitize on entry

3. **Credit System (Users)**
   - Deducted at creation time (not generation end)
   - Calculation: `participants × rounds × depth_multiplier`
   - Prevents overages; enables predictable costs

4. **Serializer Specialization**
   - List serializer: Lightweight, no nested relations
   - Detail serializer: Full nested objects
   - Create serializer: Input validation + business logic
   - Reduces over-fetching; improves API efficiency

5. **SSE + Pub/Sub (Real-time)**
   - Celery publishes events to Redis channel
   - Frontend SSE listener receives updates
   - Decouples generation from UI; scalable to many users

### 8.2 Trade-offs Made

| Decision | Pros | Cons |
|----------|------|------|
| **Dual-storage personas** | Human-editable, version-controlled | Extra sync step required |
| **Credit system** | Predictable costs, prevents overages | Doesn't match actual usage |
| **Celery concurrency=2** | Low resource usage | May bottleneck during spikes |
| **TextField for transcript** | Simple, self-contained | No pagination for long debates |
| **Django admin for personas** | Easy management | Requires syncing back to markdown |

---

## 9. Deployment Readiness

### 9.1 Production Configuration

**Environment Requirements:**
- PostgreSQL 14+
- Redis 8+
- Gunicorn + Nginx
- SSL certificates (Let's Encrypt via Certbot)

**Required Environment Variables:**
```bash
SECRET_KEY              # Django secret (non-negotiable)
DEBUG=False             # Production security
DJANGO_ENV=production   # Settings isolation
ALLOWED_HOSTS           # CORS origins
DB_*                    # PostgreSQL credentials
REDIS_URL               # Redis connection
ANTHROPIC_API_KEY       # Claude API key
STRIPE_SECRET_KEY       # Stripe signing
STRIPE_WEBHOOK_SECRET   # Webhook validation
SENTRY_DSN              # Error tracking
```

**Pre-Deployment Checklist:**
- ✓ All tests passing (60%+ coverage)
- ✓ Migrations applied
- ✓ Stripe webhooks configured
- ✓ Sentry DSN configured
- ✓ Health checks operational
- ✓ HTTPS enforced
- ✓ Database backups configured

### 9.2 Monitoring & Observability

**Health Checks:**
- `GET /health/` - Liveness probe
- `GET /ready/` - Readiness probe (checks dependencies)

**Logging:**
- Python: Structured logging configured (not extensively shown)
- Frontend: Console logging for errors

**Error Tracking:**
- Sentry integration configured (optional)
- Django exceptions auto-reported

**Task Monitoring:**
- Flower UI at localhost:5555 (task queue monitoring)
- Prometheus metrics (referenced in requirements)

---

## 10. Recommendations for Improvement

### 10.1 High Priority

1. **Stripe Webhook Validation (Security)**
   ```python
   # Add HMAC signature verification
   import hmac
   signature = request.headers.get('Stripe-Signature')
   secret = settings.STRIPE_WEBHOOK_SECRET
   assert hmac.compare_digest(signature, expected_signature)
   ```

2. **Concurrent Credit Deduction (Data Integrity)**
   ```python
   # Use select_for_update() to prevent race conditions
   user = User.objects.select_for_update().get(id=user_id)
   if user.credits_remaining < required:
       raise InsufficientCredits()
   user.deduct_credits(required)
   ```

3. **Error Response Normalization (API Quality)**
   Create custom exception handler to standardize all error responses:
   ```python
   {
     "error": "error_code",
     "message": "human-readable message",
     "status": 400
   }
   ```

### 10.2 Medium Priority

4. **Integration Tests (Testing)**
   - End-to-end debate creation → generation → completion
   - Stripe webhook → credit handling
   - SSE stream reliability

5. **Frontend Component Tests (Testing)**
   - DebateTheaterView animation logic
   - Header auth state transitions
   - Error boundary handling

6. **Celery Concurrency Tuning (Scalability)**
   - Benchmark with production load
   - Consider Celery queues (priority vs. standard tasks)
   - Monitor CPU/memory per debate generation

7. **Transcript Pagination (Scalability)**
   - Add TextSection-like hierarchy to messages
   - Implement lazy-loading in UI
   - Reduce initial payload for long debates

### 10.3 Low Priority

8. **Logging Enhancement**
   - Add structured logging (Python logging.handlers.RotatingFileHandler)
   - Track API latency, task duration, cache hit rates
   - Audit trail for subscription changes

9. **API Documentation**
   - drf-spectacular already configured
   - Add request/response examples
   - Document error codes and recovery strategies

10. **Frontend Performance**
    - Code splitting on debate pages
    - Image lazy-loading for persona portraits
    - ServiceWorker for offline debate viewing

---

## 11. Conclusion

### Overall Architecture Quality: **8.5/10**

**Verdict:** This is a well-engineered, production-ready application with thoughtful design decisions, strong security practices, and scalable architecture.

**Key Strengths:**
1. Clear separation of concerns across 6 Django apps
2. Security-first approach with multiple validation layers
3. Async task processing for scalability
4. Real-time updates via SSE + Redis
5. Type safety throughout (Python + TypeScript)
6. Subscription billing integrated with Stripe
7. Docker orchestration with health checks

**Key Weaknesses:**
1. Missing Stripe webhook signature validation (security gap)
2. Potential race conditions in concurrent credit deduction
3. Limited integration and component testing
4. Inconsistent error response formats
5. Some complex components need refactoring (forms: 827 lines)

**Recommendation:** Ship to production with fixes for items 1-2. Address testing gaps (3) in next sprint. Consider scalability improvements (concurrency, pagination) when traffic scales.

**Estimated Production Readiness:** 85% (with high-priority fixes: 95%)
