# Architecture Documentation

**Project:** The Infinite Debate
**Last Updated:** October 20, 2025
**Status:** Production-ready with ongoing improvements

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Dual Debate System Architecture](#dual-debate-system-architecture)
3. [Technology Stack](#technology-stack)
4. [Backend Architecture](#backend-architecture)
5. [Frontend Architecture](#frontend-architecture)
6. [Data Flow](#data-flow)
7. [Persona System](#persona-system)
8. [Primary Text Integration](#primary-text-integration)
9. [Security Architecture](#security-architecture)
10. [Deployment Architecture](#deployment-architecture)
11. [Decision Records](#decision-records)

---

## System Overview

The Infinite Debate is an AI-powered platform that orchestrates debates between historical figures (philosophers, theologians, scientists) using Claude AI. The system allows users to select personas and topics, then generates authentic multi-round debates with citation linking to primary sources.

### Core Capabilities

- **196 Historical Personas** across 29 categories
- **100+ Primary Texts** with hierarchical section structure
- **Multi-Round Debates** with chronological turn ordering
- **Real-Time Generation** via Celery task queue
- **Citation Extraction** linking debate statements to source texts
- **Subscription Management** with credit-based usage (Stripe)
- **PDF Export** for academic use

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Theater Mode │  │ Browse       │  │ User Account │      │
│  │ (Real-time)  │  │ Debates      │  │ Management   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST API + JWT Auth
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (Django)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Debates      │  │ Personas     │  │ Texts        │      │
│  │ (ViewSets)   │  │ (ViewSets)   │  │ (ViewSets)   │      │
│  └──────┬───────┘  └──────────────┘  └──────────────┘      │
│         │                                                     │
│         ▼                                                     │
│  ┌──────────────┐       ┌──────────────┐                    │
│  │ Celery Task  │◄──────│ Redis Queue  │                    │
│  │ (Generator)  │       └──────────────┘                    │
│  └──────┬───────┘                                            │
│         │                                                     │
│         ▼                                                     │
│  ┌──────────────────────────────────────┐                   │
│  │ Claude API (Anthropic)                │                   │
│  │ - Persona embodiment                  │                   │
│  │ - Multi-round dialogue                │                   │
│  └──────────────────────────────────────┘                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │   PostgreSQL     │
                  │   - Users        │
                  │   - Debates      │
                  │   - Messages     │
                  │   - Personas     │
                  │   - Texts        │
                  └──────────────────┘
```

---

## Dual Debate System Architecture

**⚠️ CRITICAL: This project has TWO debate systems that serve different purposes.**

### System Comparison

| Feature | CLI Debate System | Web Debate System |
|---------|-------------------|-------------------|
| **Purpose** | Testing, prototyping, quality validation | Production user-facing platform |
| **Location** | `.claude/commands/debate.md` | `backend/debates/` Django app |
| **Data Storage** | Filesystem (`debates/*.md`) | PostgreSQL database |
| **Personas** | 31 hardcoded personas | 196 database personas |
| **Turn Invocation** | `/debate` slash command | Web UI at `/debates/new` |
| **Authentication** | None (open) | JWT-based user auth |
| **Credits** | None | Subscription-based credit system |
| **Primary Texts** | Not integrated | Full text library with citations |
| **Real-Time UI** | Terminal output only | Theater mode with typewriter animation |
| **Export** | Markdown files | PDF with formatted citations |
| **Use Case** | Development testing | End-user production |

### Data Flow Isolation

```
CLI System:
┌──────────────┐
│ /debate cmd  │
└──────┬───────┘
       │
       ▼
┌──────────────────────────┐
│ debates/YYYY-MM-DD_*.md  │  ← Filesystem only
└──────────────────────────┘

Web System:
┌──────────────┐
│ Web UI       │
└──────┬───────┘
       │
       ▼
┌──────────────────────────┐
│ PostgreSQL (debates)     │  ← Database only
└──────────────────────────┘
```

**⚠️ These systems DO NOT sync.** A debate created via CLI will not appear in the web UI and vice versa.

### When to Use Each System

**CLI System (`/debate`):**
- ✅ Rapid prototyping of new personas
- ✅ Testing persona authenticity before adding to database
- ✅ Generating sample debates for quality evaluation
- ✅ Quick philosophical explorations during development
- ❌ **NEVER for production user-facing features**

**Web System (Django + Next.js):**
- ✅ All production use cases
- ✅ User-facing debates with auth and credits
- ✅ Citation linking to primary texts
- ✅ Persistent storage with search and history
- ✅ PDF export for academic use
- ✅ Theater mode with real-time updates

### Architectural Decision Rationale

**Why maintain both systems?**

1. **Development Velocity:** CLI system enables rapid persona testing without database setup
2. **Quality Assurance:** Quick validation of debate quality before committing to database
3. **Historical Context:** Original prototype provides reference for core debate logic
4. **Separation of Concerns:** Keeps development/testing separate from production data

**Why not merge them?**

- CLI is optimized for speed and simplicity
- Web system requires authentication, credits, complex state management
- Different output formats (terminal vs UI)
- Different data models (markdown files vs relational DB)

---

## Technology Stack

### Backend Stack

```
Django 5.2
├── Django REST Framework 3.16 (API layer)
├── djangorestframework-simplejwt (JWT auth)
├── Celery 5.4 (async task queue)
├── anthropic 0.37 (Claude API client)
├── psycopg2 2.9 (PostgreSQL adapter)
├── redis 5.0 (Celery broker/cache)
├── stripe 11.4 (payment processing)
├── reportlab 4.2 (PDF generation)
├── bleach 7.0 (HTML sanitization)
└── sentry-sdk 2.17 (error tracking)
```

**Python Version:** 3.12+

### Frontend Stack

```
Next.js 15.5 (App Router)
├── React 19 (UI framework)
├── TypeScript 5 (strict mode)
├── Material-UI 7 (component library)
├── Emotion 11 (CSS-in-JS)
├── TanStack Query 5 (server state)
├── axios 1.7 (HTTP client)
├── Vitest (testing framework)
└── React Testing Library (component tests)
```

**Node Version:** 22+

### Infrastructure

```
Docker Compose
├── nginx (reverse proxy)
├── web (Django + Gunicorn)
├── celery (task worker)
├── celery-beat (scheduled tasks)
├── db (PostgreSQL 17)
├── redis (Redis 7)
└── flower (Celery monitoring)
```

---

## Backend Architecture

### Django Apps Structure

```
backend/
├── debates/          # Core debate orchestration
├── personas/         # Historical figure profiles
├── texts/            # Primary source library
├── users/            # Authentication & subscriptions
├── payments/         # Stripe integration
└── health/           # Kubernetes probes
```

### Debates App

**Purpose:** Orchestrate multi-round debates between personas

**Models:**
```python
Debate:
  - user: ForeignKey(User)
  - participants: ManyToMany(Persona)
  - topic: CharField
  - status: pending → generating → completed/failed
  - max_rounds: IntegerField
  - depth_level: introductory/intermediate/advanced
  - credits_used: IntegerField

DebateMessage:
  - debate: ForeignKey(Debate)
  - persona: ForeignKey(Persona)
  - round_number: IntegerField
  - content: TextField (markdown)
  - message_type: opening/response/conclusion
```

**Key Logic:**

1. **Credit Deduction:** On debate creation, calculate required credits and deduct from user
2. **Async Generation:** Trigger Celery task for debate generation
3. **Turn Ordering:** Sort participants by birth_year (chronological)
4. **Message Generation:** Call Claude API for each persona's turn
5. **Citation Extraction:** Post-process messages to link primary text references

**API Endpoints:**
- `POST /api/debates/` - Create debate (validates credits)
- `GET /api/debates/{slug}/` - Retrieve with messages
- `POST /api/debates/{slug}/generate/` - Trigger async generation
- `GET /api/debates/{slug}/export/` - Download PDF

### Personas App

**Purpose:** Manage historical figure profiles

**Model:**
```python
Persona:
  - name: CharField
  - slug: SlugField
  - category: ForeignKey(PersonaCategory)
  - birth_year: IntegerField (for chronological ordering)
  - era: CharField
  - tradition: CharField
  - primary_works: JSONField
  - core_positions: TextField
  - debate_style: TextField
  - external_links: JSONField (Wikipedia, Stanford, etc.)
  - tier: free/trial/starter/pro/enterprise
  - portrait: ImageField
```

**Dual Storage Architecture:**

See [Persona System](#persona-system) section for detailed explanation.

**API Endpoints:**
- `GET /api/personas/` - List with search/filter
- `GET /api/personas/by_category/` - Grouped by category
- `GET /api/personas/{slug}/` - Detail with debate stats

### Texts App

**Purpose:** Primary source text library with citation linking

**Models:**
```python
PrimaryText:
  - title: CharField
  - author: CharField
  - slug: SlugField
  - source_url: URLField (Gutenberg, Perseus, etc.)
  - era: CharField
  - tradition: CharField
  - full_text: TextField
  - metadata: JSONField

TextSection:
  - text: ForeignKey(PrimaryText)
  - parent: ForeignKey('self', null=True)  # Hierarchical structure
  - section_type: book/chapter/section/paragraph
  - title: CharField
  - content: TextField
  - position: IntegerField

TextCitation:
  - debate_message: ForeignKey(DebateMessage)
  - text: ForeignKey(PrimaryText)
  - section: ForeignKey(TextSection, null=True)
  - quoted_phrase: TextField
  - confidence: FloatField (0.0-1.0)
```

**Text Ingestion Workflow:**

1. `ingest_text` management command loads text from URL
2. Parse hierarchical structure (book → chapter → section)
3. Store in database with full-text search indexing
4. Link to personas via external_links

**Citation Extraction:**

1. After debate message generated, run `citation_markup.py`
2. Regex patterns detect work titles (e.g., `{Nicomachean Ethics}`)
3. Match to PrimaryText by title/author
4. Create TextCitation with confidence score
5. Frontend renders as clickable links to text sections

### Users App

**Purpose:** Authentication and subscription management

**Model:**
```python
User (Custom):
  - email: EmailField (unique, used for login)
  - subscription_tier: trial/free/starter/pro/enterprise
  - subscription_status: active/expired/cancelled
  - trial_start_date: DateTimeField
  - trial_end_date: DateTimeField
  - credits_remaining: IntegerField
  - monthly_credit_limit: IntegerField
  - last_credit_reset: DateTimeField
  - stripe_customer_id: CharField
```

**Credit System:**

```python
Tier Credits (Monthly):
- Trial: 15 credits (7 days)
- Free: 5 credits
- Starter ($10/mo): 50 credits
- Pro ($25/mo): 200 credits
- Enterprise: Unlimited

Credit Cost Formula:
base = num_participants * max_rounds
multiplier = {'introductory': 1.0, 'intermediate': 1.5, 'advanced': 2.0}
cost = base * multiplier
```

**Authentication Flow:**

1. User registers → Auto-create trial subscription
2. User logs in → JWT access + refresh tokens issued
3. Frontend stores tokens in localStorage (⚠️ XSS vulnerable, being upgraded to HttpOnly cookies)
4. API requests include `Authorization: Bearer {token}` header
5. Django middleware validates JWT and attaches user to request

### Payments App

**Purpose:** Stripe integration for subscriptions

**Models:**
```python
StripeEvent:
  - event_id: CharField (idempotent key)
  - event_type: CharField
  - data: JSONField
  - processed: BooleanField

StripePayment:
  - user: ForeignKey(User)
  - amount: IntegerField
  - status: pending/succeeded/failed

StripeSubscriptionHistory:
  - user: ForeignKey(User)
  - tier: CharField
  - start_date: DateTimeField
  - end_date: DateTimeField
```

**Webhook Handling:**

1. Stripe sends event to `/api/payments/webhook/`
2. Verify signature with webhook secret
3. Check if `event_id` already processed (idempotency)
4. Update user subscription_tier and credits
5. Log in StripeEvent for audit trail

---

## Frontend Architecture

### Next.js App Router Structure

```
app/
├── page.tsx                    # Home (public)
├── login/, register/           # Auth pages
├── debates/
│   ├── page.tsx                # Browse debates
│   ├── new/page.tsx            # Create debate (827 lines, needs refactor)
│   └── [slug]/page.tsx         # View debate (theater + transcript modes)
├── personas/[slug]/page.tsx    # Persona profile
├── texts/
│   ├── page.tsx                # Browse library
│   └── [slug]/page.tsx         # Read text with citations
├── account/page.tsx            # User management (protected)
└── pricing/page.tsx            # Subscription tiers
```

### Key Components

**DebateTheaterView.tsx (653 lines)**
- Real-time debate visualization with typewriter effect
- Polling via React Query (refetchInterval: 2000ms)
- Persona avatars with speech bubbles
- Round counter and progress indicator
- Message history with citation links

**MessageContent.tsx**
- Renders debate messages as markdown
- Detects citation markup (`{Title}` syntax)
- Converts to clickable links → `/texts/{slug}`
- Syntax highlighting for code blocks (if any)

**ProtectedRoute.tsx**
- HOC wrapper for authenticated pages
- Checks localStorage for JWT token
- Redirects to `/login` if not authenticated
- Validates token expiry

### State Management

**Server State (React Query):**
```typescript
// Fetch debates with auto-refetch on focus
const { data: debates } = useQuery({
  queryKey: ['debates'],
  queryFn: () => apiClient.debates.list(),
  refetchOnWindowFocus: true
});

// Poll debate status during generation
const { data: debate } = useQuery({
  queryKey: ['debate', slug],
  queryFn: () => apiClient.debates.getBySlug(slug),
  refetchInterval: (query) =>
    query.state.data?.status === 'generating' ? 2000 : false
});
```

**Client State (React Context):**
```typescript
AuthContext:
  - user: User | null
  - login(email, password): Promise<void>
  - logout(): void
  - refreshToken(): Promise<void>
```

### API Client (axios)

```typescript
// lib/api.ts
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Request interceptor: Attach JWT token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: Refresh token on 401
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Attempt token refresh
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        const { data } = await axios.post('/api/auth/refresh/', {
          refresh: refreshToken
        });
        localStorage.setItem('access_token', data.access);
        // Retry original request
        return apiClient(error.config);
      }
    }
    return Promise.reject(error);
  }
);
```

---

## Data Flow

### Debate Creation Flow

```
1. User fills form (/debates/new)
   ├── Selects 2-15 personas
   ├── Enters topic
   ├── Sets max_rounds (3-10)
   └── Sets depth_level (introductory/intermediate/advanced)

2. Frontend submits POST /api/debates/
   └── apiClient.debates.create({ participants, topic, ... })

3. Django DRF Serializer validates
   ├── Check user has sufficient credits
   ├── Calculate required credits
   ├── Deduct credits from user
   └── Create Debate instance (status='pending')

4. ViewSet triggers Celery task
   └── generate_debate_task.delay(debate.id)

5. Celery worker picks up task
   ├── Load persona definitions from DB
   ├── Sort participants by birth_year
   ├── Generate opening statements (Claude API)
   ├── Run N rounds of dialogue
   ├── Extract citations from messages
   └── Update debate status='completed'

6. Frontend polls GET /api/debates/{slug}/
   ├── Every 2 seconds while status='generating'
   └── Displays messages in theater mode

7. User views completed debate
   ├── Theater mode with typewriter animation
   ├── Click citations → Navigate to /texts/{slug}
   └── Export PDF button → Download formatted debate
```

### Persona Sync Flow

```
1. Developer edits persona markdown
   └── backend/personas/fixtures/scientists/einstein.md

2. Run management command
   └── python manage.py load_personas

3. Command discovers all persona files
   ├── Glob: personas/fixtures/**/*.md
   ├── Parse structured markdown sections
   ├── Extract metadata (birth_year, works, etc.)
   └── Call update_or_create(slug=slug, defaults={...})

4. Database updated
   └── personas_persona table now reflects changes

5. Frontend fetches updated persona
   └── GET /api/personas/einstein/
```

**⚠️ CRITICAL:** The management command is the ONLY way to sync markdown → database. Without running it:
- New personas won't appear in web UI
- Edits to existing personas won't be reflected
- Debate generation will use stale data

---

## Persona System

### Dual Storage Architecture

**Source of Truth:** Markdown files
- Location: `backend/personas/fixtures/{category}/{slug}.md`
- Human-editable, version-controlled
- Contains full persona definitions (7-10 sections)
- 196 files organized by category

**Runtime Database:** PostgreSQL
- Table: `personas_persona`
- Served via REST API to frontend
- Queried for debates, filtering, search
- Includes parsed fields (birth_year, primary_works, external_links)

**Sync Mechanism:** Management Command
```bash
python manage.py load_personas
```

### Persona File Structure

```markdown
# [Name]

**Title:** [Title]
**Era:** [Era]
**Tradition:** [Tradition]
**Primary Works:** [Works]

---

## Identity

[Who they are, historical context]

## Core Philosophical Positions

[Key doctrines, beliefs, arguments]

## Debate Style and Approach

[Methodology, tone, rhetorical strengths]

## Key Concepts and Terminology

[Essential vocabulary and ideas]

## Engagement with Other Traditions

[How this thinker would interact with specific other traditions]

## Representative Quotes/Positions

[Characteristic statements]

## Debate Priorities

[Ordered list of debate strategies]

## Potential Weaknesses/Vulnerabilities

[Areas where the position is challenged]

## Character Notes

[Guidance for embodying the persona]
```

### Management Command Logic

```python
# personas/management/commands/load_personas.py
def handle(self, *args, **options):
    fixtures_dir = Path(__file__).parent.parent.parent / 'fixtures'

    for md_file in fixtures_dir.rglob('*.md'):
        # Parse markdown sections
        sections = parse_persona_markdown(md_file.read_text())

        # Extract metadata
        birth_year = extract_birth_year(sections['Identity'])
        primary_works = extract_works(sections['Primary Works'])

        # Sync to database
        Persona.objects.update_or_create(
            slug=md_file.stem,
            defaults={
                'name': sections['name'],
                'category': determine_category(md_file.parent.name),
                'birth_year': birth_year,
                'core_positions': sections['Core Philosophical Positions'],
                'debate_style': sections['Debate Style and Approach'],
                'primary_works': primary_works,
                # ... other fields
            }
        )
```

### Why This Architecture?

**Benefits:**
- ✅ Version control for personas (git tracks changes)
- ✅ Easy editing (markdown more accessible than SQL)
- ✅ Automatic database sync via command
- ✅ Separation of human-edited content from runtime data
- ✅ Can regenerate database from markdown at any time

**Tradeoffs:**
- ⚠️ Requires manual sync step after edits
- ⚠️ Two sources of truth (risk of drift if command not run)
- ⚠️ More complex than single-source approach

---

## Primary Text Integration

### Text Ingestion Pipeline

```
1. Acquire text (Project Gutenberg, Perseus, etc.)
   └── URL to plaintext or HTML

2. Run management command
   └── python manage.py ingest_text --url {url} --title "{title}" --author "{author}"

3. Command downloads and parses
   ├── Detect structure (book → chapter → section)
   ├── Extract hierarchical sections
   └── Store in PrimaryText + TextSection models

4. Link to personas
   └── Update persona.external_links with text references

5. Index for search
   └── PostgreSQL full-text search on content
```

### Citation Extraction

**Challenge:** Debate messages contain implicit references to works, but no explicit citations.

**Solution:** Post-processing with regex + fuzzy matching

```python
# debates/citation_markup.py
def extract_citations(message_content: str) -> List[Citation]:
    """
    Detect work titles in debate messages and link to PrimaryText.

    Patterns:
    - {Title} markup (explicit citation)
    - "As I wrote in Title" (implicit reference)
    - Common work titles (e.g., "Nicomachean Ethics")
    """
    citations = []

    # Explicit markup
    for match in re.finditer(r'\{([^}]+)\}', message_content):
        title = match.group(1)
        text = PrimaryText.objects.filter(title__icontains=title).first()
        if text:
            citations.append(Citation(text=text, confidence=1.0))

    # Implicit references (lower confidence)
    for work_title in KNOWN_WORK_TITLES:
        if work_title.lower() in message_content.lower():
            text = PrimaryText.objects.filter(title__iexact=work_title).first()
            if text:
                citations.append(Citation(text=text, confidence=0.7))

    return citations
```

**Status:** Function exists but not yet integrated into debate generation pipeline (see NEXT_STEPS.md Priority 4a).

---

## Security Architecture

### Current State (B+ Grade)

**Authentication:**
- JWT tokens with djangorestframework-simplejwt
- Access token (5 min expiry) + Refresh token (24 hr expiry)
- Tokens stored in localStorage (⚠️ XSS vulnerable)

**Authorization:**
- Django REST Framework permissions
- IsAuthenticated for all debate/persona/text endpoints
- Row-level permissions (users can only access their own debates)

**Input Validation:**
- Django model validators (length, format)
- DRF serializer validation
- ⚠️ Missing: HTML/JS sanitization for debate topics and messages

**Vulnerabilities Identified:**

1. **XSS via localStorage tokens** (High)
   - Tokens accessible to malicious JavaScript
   - Mitigation: Upgrade to HttpOnly cookies (in progress)

2. **Missing input sanitization** (Medium)
   - Debate topics/messages not sanitized
   - Mitigation: Add bleach library for HTML stripping

3. **No rate limiting** (Low)
   - API endpoints unprotected from abuse
   - Mitigation: Add django-ratelimit

### Planned Security Improvements

See NEXT_STEPS.md Priority 2 for detailed implementation plan.

**Week 1 Deliverables:**
- HttpOnly cookie authentication (backend + frontend)
- Input sanitization with bleach library
- XSS prevention in markdown rendering
- OWASP security testing

---

## Deployment Architecture

### Current Deployment (Development)

```
┌─────────────────────────────────────────────────────────┐
│                      Localhost                           │
│                                                          │
│  ┌────────────────┐         ┌────────────────┐         │
│  │  Frontend      │         │  Backend       │         │
│  │  (Next.js)     │────────>│  (Django)      │         │
│  │  Port 3001     │         │  Port 8001     │         │
│  └────────────────┘         └────────┬───────┘         │
│                                       │                  │
│                                       ▼                  │
│                            ┌────────────────┐           │
│                            │  PostgreSQL    │           │
│                            │  Port 5432     │           │
│                            └────────────────┘           │
└─────────────────────────────────────────────────────────┘
```

**Docker Compose Services (Development):**
- `docker-compose.yml` - Base configuration
- `docker-compose.override.yml` - Development overrides (⚠️ Auto-merged!)
  - Mounts code directories for live reload
  - Uses Django runserver (not Gunicorn)
  - Exposes debug ports

**⚠️ CRITICAL:** `docker-compose.override.yml` is DANGEROUS for production!
- Auto-merges when running `docker compose up`
- Production must explicitly exclude with `-f docker-compose.yml` flag

### Target Production Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Vercel (Frontend)                   │
│  ┌────────────────────────────────────────────────┐    │
│  │  Next.js App (Static + SSR)                     │    │
│  │  Domain: theinfinitedebate.com                      │    │
│  └─────────────────┬──────────────────────────────┘    │
└────────────────────┼──────────────────────────────────┘
                     │ HTTPS
                     ▼
┌─────────────────────────────────────────────────────────┐
│         AWS Lightsail (Backend + Database)              │
│                                                          │
│  ┌────────────────┐         ┌────────────────┐         │
│  │  Nginx         │────────>│  Django        │         │
│  │  (Reverse      │         │  (Gunicorn)    │         │
│  │   Proxy)       │         └────────┬───────┘         │
│  └────────────────┘                  │                  │
│                                       │                  │
│                          ┌────────────┼────────────┐    │
│                          │            │            │    │
│                          ▼            ▼            ▼    │
│                   ┌──────────┐ ┌──────────┐ ┌──────┐  │
│                   │ Celery   │ │ Redis    │ │ DB   │  │
│                   │ Worker   │ │          │ │ (PG) │  │
│                   └──────────┘ └──────────┘ └──────┘  │
└─────────────────────────────────────────────────────────┘
```

**Production Requirements:**
- ✅ Separate docker-compose.prod.yml (no code mounts)
- ✅ Pre-deployment validation script
- ✅ Gunicorn with multiple workers
- ✅ Nginx reverse proxy with SSL
- ✅ PostgreSQL with automated backups
- ✅ Redis for Celery + caching
- ✅ Sentry for error tracking
- ✅ Health checks for Kubernetes/Lightsail

### Deployment Workflow

**Backend (AWS Lightsail):**
```bash
# SSH into Lightsail instance
ssh user@lightsail-instance

# Pull latest code
cd /opt/the-infinite-debate/backend
git pull

# Run validation script
bash scripts/validate-production.sh

# Build and deploy with EXPLICIT production config
docker compose -f docker-compose.yml build --no-cache
docker compose -f docker-compose.yml up -d

# Run migrations
docker compose -f docker-compose.yml exec web python manage.py migrate

# Collect static files
docker compose -f docker-compose.yml exec web python manage.py collectstatic --no-input

# Verify health
curl http://localhost:8001/health/
```

**Frontend (Vercel):**
- Push to GitHub main branch
- Vercel auto-deploys via webhook
- Preview deployments for PRs

---

## Decision Records

### ADR-001: Dual Debate System

**Date:** October 20, 2025
**Status:** Accepted

**Context:**
- CLI debate system (`/debate` command) exists from original prototype
- Django web app debate system provides full production features
- Both systems functional but create data fragmentation

**Decision:**
Keep both systems with clear separation:
- CLI for testing/prototyping only
- Web app for all production use
- No data sync between systems

**Rationale:**
- CLI enables rapid persona testing without database overhead
- Web app provides user auth, credits, citations, persistence
- Attempting to merge would compromise both systems' strengths

**Consequences:**
- ✅ Fast development iteration with CLI testing
- ✅ Production system remains clean and isolated
- ⚠️ Risk of confusion if not documented clearly
- ⚠️ Duplicate debate logic (acceptable for different use cases)

---

### ADR-002: Markdown Persona Files + Database Sync

**Date:** October 20, 2025
**Status:** Accepted

**Context:**
- Personas require rich structured content (7-10 sections)
- Database needed for API queries, filtering, search
- Editing SQL directly is error-prone and not version-controlled

**Decision:**
Dual storage with markdown as source of truth:
- Store personas as markdown files in `personas/fixtures/`
- Sync to database via `load_personas` management command
- Require manual sync step after edits

**Rationale:**
- Version control (git) tracks persona changes over time
- Markdown more accessible for content editing than SQL
- Database provides query performance for web app
- Trade-off: Manual sync step acceptable for ease of editing

**Consequences:**
- ✅ Easy content editing with git history
- ✅ Fast database queries for web app
- ⚠️ Must remember to run sync command after edits
- ⚠️ Risk of drift if command not run (mitigated by docs)

---

### ADR-003: Celery for Async Debate Generation

**Date:** October 20, 2025
**Status:** Accepted

**Context:**
- Debate generation takes 30-120 seconds (multiple Claude API calls)
- Users should not wait for synchronous HTTP response
- Need real-time UI updates as debate progresses

**Decision:**
Use Celery task queue with Redis broker:
- API creates debate with status='pending'
- Triggers async task via Celery
- Frontend polls debate status every 2 seconds
- Task updates debate status to 'completed' when done

**Rationale:**
- Non-blocking API responses (instant debate creation)
- Celery mature and battle-tested
- Redis provides fast message broker
- Polling acceptable for MVP (can upgrade to WebSockets/SSE later)

**Consequences:**
- ✅ Fast API responses
- ✅ Scalable task processing (add more workers)
- ⚠️ Additional complexity (Redis dependency)
- ⚠️ Polling inefficient (upgrade to SSE planned for Week 2)

---

### ADR-004: JWT Auth with localStorage (Upgrading to Cookies)

**Date:** October 20, 2025
**Status:** Deprecated (being replaced with HttpOnly cookies)

**Context:**
- Need user authentication for debates, subscriptions, credits
- JWT tokens industry standard for stateless auth
- Original implementation stored tokens in localStorage

**Decision (Original):**
JWT tokens stored in localStorage, included in Authorization header

**Rationale (Original):**
- Simple implementation with djangorestframework-simplejwt
- Stateless (no server-side session storage)
- Works with SPA architecture

**Consequences:**
- ✅ Easy implementation
- ❌ **SECURITY RISK:** XSS attacks can steal tokens from localStorage
- ❌ Identified in security review as critical vulnerability

**New Decision (October 2025):**
Upgrade to HttpOnly cookies:
- Backend sets JWT in HttpOnly cookie (not accessible to JavaScript)
- Frontend sends cookie automatically with `credentials: 'include'`
- Remove localStorage token storage

**Implementation:** See NEXT_STEPS.md Priority 2a for detailed plan.

---

## Performance Considerations

### Current Bottlenecks

1. **Frontend Polling (Inefficient)**
   - React Query polls debate status every 2s
   - Unnecessary API calls when no updates
   - Solution: Upgrade to Server-Sent Events (SSE) in Week 2

2. **No Caching Layer**
   - Persona list fetched on every page load
   - Primary texts not cached
   - Solution: Add Redis caching with 5-10 min TTL

3. **Large React Components**
   - `DebateTheaterView.tsx` (653 lines) re-renders entire debate on each message
   - `debates/new/page.tsx` (827 lines) handles complex form state
   - Solution: Split into smaller memoized components

### Optimization Roadmap

See NEXT_STEPS.md Priority 6 (Week 2) for detailed performance improvements.

---

## Testing Strategy

### Backend Testing (pytest-django)

**Coverage:** 84% (564 tests)

**Key Test Files:**
- `debates/tests/test_models.py` - Model logic and relationships
- `debates/tests/test_views.py` - API endpoint behavior
- `debates/tests/test_tasks.py` - Celery task execution
- `personas/tests/test_management.py` - load_personas command
- `payments/tests/test_webhooks.py` - Stripe webhook handling

**Fixtures (conftest.py):**
```python
@pytest.fixture
def test_user():
    return User.objects.create_user(
        email='test@example.com',
        subscription_tier='pro',
        credits_remaining=100
    )

@pytest.fixture
def authenticated_client(test_user):
    client = APIClient()
    refresh = RefreshToken.for_user(test_user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client
```

### Frontend Testing (Vitest + React Testing Library)

**Coverage:** 94% (218 tests)

**Key Test Files:**
- `__tests__/components/DebateTheaterView.test.tsx`
- `__tests__/lib/api.test.ts`
- `__tests__/contexts/AuthContext.test.tsx`

**Test Utilities:**
```typescript
// __tests__/utils/test-utils.tsx
export function renderWithProviders(ui: React.ReactElement) {
  return render(
    <QueryClientProvider client={testQueryClient}>
      <AuthProvider>
        {ui}
      </AuthProvider>
    </QueryClientProvider>
  );
}
```

---

## Monitoring & Observability

### Current Monitoring

**Sentry Integration:**
- Error tracking in Django and Next.js
- Performance monitoring (transaction tracing)
- User context attached to errors

**Health Checks:**
- `GET /health/` - Liveness probe (returns 200 if web server up)
- `GET /ready/` - Readiness probe (checks DB connection, Redis, Celery)

**Logging:**
- Structured logging with Python's logging module
- Log rotation (max 10MB per file, keep 5 files)
- Levels: DEBUG (dev), INFO (prod), WARNING, ERROR

### Planned Monitoring (Week 2)

- UptimeRobot for uptime monitoring
- Celery task dashboard (Flower)
- Database query performance logging
- Redis cache hit rate metrics

---

## Future Architecture Improvements

### Short-Term (1-2 Weeks)

See NEXT_STEPS.md for prioritized improvements:
- HttpOnly cookie authentication
- Input sanitization with bleach
- Production Docker configuration
- Automated backup/restore scripts
- Component refactoring (split large components)
- SSE for real-time updates
- Redis caching layer

### Long-Term (1-3 Months)

**Real-Time Updates:**
- Replace polling with WebSockets or SSE
- Live typing indicators during debate generation
- Instant message delivery

**Advanced Persona Features:**
- Dynamic persona creation (user-submitted)
- Persona rating/feedback system
- Persona relationship graph (who debates whom most)

**Enhanced Text Integration:**
- Full-text search across all primary texts
- Automatic citation suggestion during debate
- Citation confidence scoring with ML

**Performance:**
- Database query optimization (identify N+1 queries)
- CDN for static assets
- Lazy loading for debate messages (pagination)

**Analytics:**
- User engagement metrics (debates per user, average depth)
- Popular persona combinations
- Topic trend analysis

---

## References

- **Status Document:** `STATUS.md` (local working file, not committed)
- **Implementation Plan:** `NEXT_STEPS.md` (prioritized tasks)
- **Code Review:** `/Users/thedom/LLM_PLAYGROUND/OCT_20_REVIEW`
- **Quick Start:** `QUICKSTART.md` (development setup)
- **Claude Guide:** `CLAUDE.md` (AI assistant instructions)

---

**Document Version:** 1.0
**Last Reviewed:** October 20, 2025
**Next Review:** After Week 1 implementation (October 27, 2025)
