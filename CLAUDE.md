# CLAUDE.md - The Infinite Debate Project Guide

This file provides guidance to Claude Code and contributors working on The Infinite Debate platform.

## Project Overview

**The Infinite Debate** is an AI-powered debate platform that brings historical thinkers to life. Users select personas (philosophers, scientists, theologians, cultural figures) and topics to generate authentic debates using Claude AI. The platform features full-text primary source integration, citation extraction, and subscription-based access tiers.

**Core Features:**
- Multi-persona debates with chronological turn ordering
- Real-time debate generation with theater mode visualization
- Primary text library with citation linking
- Subscription tiers with credit-based usage (Trial/Starter/Pro/Enterprise)
- PDF export with citations for academic use

## Technology Stack

### Backend
- **Framework:** Django 5.2 + Django REST Framework 3.16
- **Database:** PostgreSQL (philosophical_debates)
- **Task Queue:** Celery + Redis
- **AI:** Anthropic Claude API (Sonnet models)
- **Payment:** Stripe integration for subscriptions
- **Auth:** JWT with djangorestframework-simplejwt

### Frontend
- **Framework:** Next.js 15.5 (App Router)
- **UI Library:** Material-UI v7 with Emotion
- **State:** React Query (TanStack Query v5)
- **Language:** TypeScript 5 (strict mode)
- **Testing:** Vitest + React Testing Library

### Infrastructure
- **Containerization:** Docker Compose (7 services)
- **Monitoring:** Sentry error tracking
- **Logging:** Structured logging with rotation

## Architecture

### Django Apps

The backend is organized into specialized Django apps:

1. **debates** - Debate orchestration and management
   - Models: `Debate`, `DebateMessage`
   - ViewSet: CRUD, generate (Celery task), export (PDF)
   - Status flow: pending → generating → completed/failed

2. **personas** - Historical figure profiles
   - Models: `Persona`, `PersonaRequest`
   - Tiers: Free/Trial/Starter/Pro/Enterprise
   - Turn order: Chronological by birth_year

3. **texts** - Primary source library
   - Models: `PrimaryText`, `TextSection` (hierarchical), `TextCitation`
   - Features: Full-text search, citation extraction, confidence scoring

4. **users** - Authentication and subscriptions
   - Model: Custom `User` with credits and subscription management
   - Credit system: Monthly reset based on tier
   - Trial: 7 days, 15 credits auto-granted on registration

5. **payments** - Stripe integration
   - Models: `StripeEvent`, `StripePayment`, `StripeSubscriptionHistory`
   - Webhooks: Idempotent event processing
   - Tiers: Student (Starter $10/mo), Scholar (Pro $25/mo)

6. **health** - Kubernetes probes
   - Endpoints: `/health/` (liveness), `/ready/` (readiness)

### Persona System Architecture

**⚠️ IMPORTANT:** Personas use a dual-storage architecture:

1. **Source of Truth:** Markdown files in `backend/personas/fixtures/{category}/{slug}.md`
   - Human-editable, version-controlled
   - Contains full persona definitions (identity, debate style, positions, etc.)
   - 196 files organized by category (theologians, philosophers, scientists)

2. **Runtime Database:** PostgreSQL `personas_persona` table
   - Served via REST API to frontend
   - Queried for debates, filtering, search
   - Includes parsed fields (birth_year, primary_works, external_links)

**Critical Management Command:**
```bash
python manage.py load_personas
```

**What it does:**
- Discovers all markdown files in `backend/personas/fixtures/`
- Parses structured sections (Core Positions, Debate Style, etc.)
- Extracts metadata (birth year, era, works)
- Uses `update_or_create()` to sync to database
- Links portrait images if available

**When to run:**
- ✅ **Initial setup** (required—database starts empty!)
- ✅ After editing persona markdown files
- ✅ After adding new personas
- ✅ After pulling updates with persona changes

**Consequences of not running:**
- ❌ Zero personas in database
- ❌ API returns empty results
- ❌ Frontend shows no personas
- ❌ Cannot create debates

See `backend/personas/management/commands/load_personas.py` for implementation details.

### Key Model Relationships

```
User (1) ──→ (M) Debate
         └──→ (M) Persona [participants, many-to-many]

Debate (1) ──→ (M) DebateMessage
                    ├──→ (1) Persona
                    └──→ (M) TextCitation
                            └──→ (1) PrimaryText
                            └──→ (0,1) TextSection
```

### Frontend Structure

```
app/
├── page.tsx                    # Home (public)
├── login/, register/           # Auth pages
├── debates/
│   ├── page.tsx                # Browse debates (React Query)
│   ├── new/page.tsx            # Create debate (complex form, 827 lines)
│   └── [slug]/page.tsx         # View debate (theater + transcript modes)
├── personas/[slug]/page.tsx    # Persona profile
├── texts/
│   ├── page.tsx                # Browse library
│   └── [slug]/page.tsx         # Read text with citations
├── account/page.tsx            # User management (protected)
└── pricing/page.tsx            # Subscription tiers
```

**Key Components:**
- `DebateTheaterView.tsx` (653 lines) - Live debate visualization with typewriter animation
- `MessageContent.tsx` - Renders messages with inline citation links
- `Header.tsx` - Navigation with auth-aware user menu
- `ProtectedRoute.tsx` - HOC wrapper for auth-required pages

### API Endpoints

**Authentication:**
- `POST /api/auth/register/` - Register with auto trial start
- `POST /api/auth/login/` - JWT token retrieval
- `POST /api/auth/refresh/` - Token refresh
- `GET /api/auth/user/` - Current user profile

**Personas:**
- `GET /api/personas/` - List with search/filter
- `GET /api/personas/by_category/` - Grouped by category
- `GET /api/personas/{slug}/` - Detail with stats

**Debates:**
- `GET /api/debates/` - User's debates
- `POST /api/debates/` - Create (validates credits, deducts on save)
- `GET /api/debates/{slug}/` - Detail with messages
- `POST /api/debates/{slug}/generate/` - Trigger Celery task
- `GET /api/debates/{slug}/export/` - Download PDF

**Texts:**
- `GET /api/texts/` - Library with filters (category, era, author)
- `GET /api/texts/{slug}/` - Full text with sections
- `GET /api/texts/{slug}/citations/` - All citations to this text

**Payments:**
- `POST /api/payments/create-checkout/` - Stripe session
- `POST /api/payments/webhook/` - Stripe event handler
- `GET /api/payments/subscription/` - Current subscription
- `POST /api/payments/cancel/` - Cancel subscription
- `GET /api/payments/history/` - Payment records

## Database Conventions

### Querying Data

**Preferred:** Django ORM via manage.py shell

```bash
cd backend
python manage.py shell_plus --print-sql
```

```python
from debates.models import Debate, DebateMessage
from personas.models import Persona
from django.utils import timezone

# Query completed debates
debates = Debate.objects.filter(status='completed').prefetch_related('participants', 'messages__persona')

# Find cross-category debates
cross = Debate.objects.filter(
    participants__category='theologians'
).filter(
    participants__category='philosophers'
).distinct()

# Persona debates with message count
persona_debates = Debate.objects.filter(
    participants__slug='aquinas'
).annotate(msg_count=Count('messages'))
```

**Fallback:** PostgreSQL direct queries

```bash
psql -U postgres -d philosophical_debates
```

```sql
-- List recent debates
SELECT d.id, d.topic, d.status, STRING_AGG(p.name, ', ') as participants
FROM debates_debate d
JOIN debates_debate_participants dp ON d.id = dp.debate_id
JOIN personas_persona p ON dp.persona_id = p.id
WHERE d.status = 'completed'
GROUP BY d.id, d.topic, d.status
ORDER BY d.created_at DESC
LIMIT 10;
```

### Query Optimization

Always use `select_related()` for ForeignKeys and `prefetch_related()` for ManyToMany:

```python
# Optimized debate detail query
debate = Debate.objects.select_related('user').prefetch_related(
    'participants',
    Prefetch('messages', queryset=DebateMessage.objects.select_related('persona'))
).get(slug=slug)
```

### Indexes

Key indexes for performance:
- `Persona.birth_year` - Chronological ordering
- `DebateMessage.[debate, round_number, persona]` - Composite index for filtering

## Testing Conventions

### Backend (pytest-django)

**Running Tests:**
```bash
cd backend
docker compose exec web pytest --cov
docker compose exec web pytest debates/tests/test_models.py -v
docker compose exec web pytest -k "test_debate" -v
```

**Test Organization:**
```
app_name/tests/
├── __init__.py
├── test_models.py
├── test_serializers.py
├── test_views.py
└── test_utils.py
```

**Fixtures (conftest.py):**
- `api_client()` - DRF APIClient
- `authenticated_client()` - With Bearer token
- `test_user()` - User with pro subscription
- `test_personas()` - Socrates, Plato, Aristotle
- `test_debate()` - Sample debate with 2 participants
- `mock_anthropic_response()` - Mock LLM response

**Coverage Target:** 60%+ for production

### Frontend (Vitest)

**Running Tests:**
```bash
cd frontend
npm test                    # Watch mode
npm test -- --run           # Single run
npm run test:coverage       # With coverage
```

**Test Utilities (`__tests__/utils/test-utils.tsx`):**
```typescript
import { renderWithProviders, mockLocalStorage } from '@/__tests__/utils/test-utils'

it('renders component', () => {
  const { getByText } = renderWithProviders(<MyComponent />)
  expect(getByText('Hello')).toBeInTheDocument()
})
```

**Mocking:**
- Next.js router: Mocked in `vitest.setup.ts`
- API calls: Mock axios instance
- Auth context: Custom AuthProvider wrapper

**Coverage Target:** 60%+ for production

## Code Quality Standards

### Python (Django)

- **Style:** Follow PEP 8
- **Docstrings:** Google style for all public functions
- **Type Hints:** Use where beneficial (views, serializers, utils)
- **Imports:** Group by stdlib, third-party, local
- **Logging:** Use structured logging, not print statements

**Example:**
```python
def calculate_debate_credits(
    num_participants: int,
    max_rounds: int,
    depth_level: str
) -> int:
    """Calculate credits required for a debate.

    Args:
        num_participants: Number of personas (2-15)
        max_rounds: Maximum debate rounds
        depth_level: Difficulty (introductory/intermediate/advanced)

    Returns:
        Credit cost as integer
    """
    base = num_participants * max_rounds
    multiplier = {'introductory': 1.0, 'intermediate': 1.5, 'advanced': 2.0}
    return int(base * multiplier.get(depth_level, 1.0))
```

### TypeScript (Next.js)

- **Strict Mode:** Enabled in tsconfig.json
- **No any:** Avoid using `any` type
- **Interfaces:** Use for component props and API responses
- **React Patterns:** Prefer functional components with hooks
- **Memoization:** Use `React.memo`, `useCallback`, `useMemo` for performance

**Example:**
```typescript
interface DebateCardProps {
  debate: Debate;
  onSelect?: (slug: string) => void;
}

const DebateCard = memo(({ debate, onSelect }: DebateCardProps) => {
  const handleClick = useCallback(() => {
    onSelect?.(debate.slug);
  }, [debate.slug, onSelect]);

  return <Card onClick={handleClick}>...</Card>;
});

DebateCard.displayName = 'DebateCard';
```

## Management Commands

**Personas:**
- `load_personas` - **[REQUIRED]** Import from `backend/personas/fixtures/{category}/{slug}.md` → database
  - Must run during initial setup and after any persona file changes
  - Without this, database has zero personas
- `redistribute_tiers` - Rebalance persona tier distribution
- `add_wikipedia_links` - Populate external_links field

**Texts:**
- `ingest_text --url {url} --title "{title}" --author "{author}"` - Add primary text
- `extract_citations --min-confidence 0.7` - Parse debate messages for citations
- `validate_citations` - Verify citation accuracy

**Users:**
- `reset_monthly_credits` - Cron job for credit reset (run monthly)
- `expire_trials` - Mark expired trial subscriptions

**Debates:**
- `generate_summaries` - Batch generate summaries for completed debates

## Contribution Workflow

### Using `/contribute` Command

For all code changes, use the structured contribution workflow:

```bash
# Feature addition
/contribute "Add email notifications for debate completion"

# Bug fix
/contribute fix "Citation links broken on mobile"

# Refactoring
/contribute refactor "Extract debate credit calculation to utility"
```

### Workflow Phases

1. **Planning** - Analyzes request, identifies affected files, creates checklist
2. **Approval Gate** - User reviews plan before proceeding
3. **Implementation** - Makes code changes following project conventions
4. **Testing** - Generates unit tests for new/modified code
5. **Validation** - Runs linters, tests, coverage checks
6. **Commit** - Creates conventional commit with reports

### Report Structure

All workflow outputs are committed to `.reports/contributions/`:

```
.reports/contributions/
└── YYYY-MM-DD/
    └── feature-name/
        ├── workflow.md        # Orchestration log
        ├── plan.md            # Implementation plan
        ├── implementation.md  # Changes made
        ├── tests.md           # Test generation
        ├── validation.md      # Quality checks
        └── commit.md          # Final commit details
```

### Commit Message Format

All commits use conventional commit format:

```
<type>(<scope>): <subject>

<body>

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types:** feat, fix, refactor, test, docs, style, chore
**Scopes:** debates, personas, texts, users, payments, health, ui, api, auth, config

## Project-Specific Patterns

### Django Patterns

**ViewSet with Prefetch:**
```python
class DebateViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Debate.objects.filter(user=self.request.user).prefetch_related(
            'participants',
            Prefetch('messages', queryset=DebateMessage.objects.select_related('persona'))
        )
```

**Credit Validation in Serializer:**
```python
def validate(self, data):
    required_credits = calculate_debate_credits(...)
    if not self.context['request'].user.can_create_debate(required_credits):
        raise ValidationError("Insufficient credits")
    return data
```

**Celery Task Pattern:**
```python
@shared_task(max_retries=3, default_retry_delay=60)
def generate_debate_task(debate_id):
    try:
        debate = Debate.objects.get(id=debate_id)
        generator = DebateGenerator()
        generator.generate(debate)
    except Exception as exc:
        logger.error(f"Debate generation failed: {exc}")
        debate.status = 'failed'
        debate.error_message = str(exc)
        debate.save()
        raise self.retry(exc=exc)
```

### React Patterns

**React Query with Polling:**
```typescript
const { data, isLoading } = useQuery({
  queryKey: ['debate', slug],
  queryFn: () => apiClient.debates.getBySlug(slug),
  refetchInterval: (query) =>
    query.state.data?.status === 'generating' ? 2000 : false
});
```

**Protected Route:**
```typescript
export default function ProtectedPage() {
  return (
    <ProtectedRoute>
      <YourComponent />
    </ProtectedRoute>
  );
}
```

**Material-UI Responsive:**
```typescript
<Box sx={{
  display: 'grid',
  gridTemplateColumns: { xs: '1fr', md: '2fr 1fr' },
  gap: 2
}}>
```

## Environment Variables

### Backend (.env)
```
# Django
SECRET_KEY=<required>
DEBUG=True
DJANGO_ENV=development
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (PostgreSQL)
DB_NAME=philosophical_debates
DB_USER=postgres
DB_PASSWORD=<required>
DB_HOST=localhost
DB_PORT=5432

# Celery/Redis
REDIS_URL=redis://localhost:6379/0

# API Keys
ANTHROPIC_API_KEY=<required>

# Stripe
STRIPE_SECRET_KEY=<required>
STRIPE_WEBHOOK_SECRET=<required>
STRIPE_STUDENT_PRICE_ID=<price_id>
STRIPE_SCHOLAR_PRICE_ID=<price_id>

# Monitoring
SENTRY_DSN=<optional>
SENTRY_ENABLED=False
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8001/api
```

## Development Workflow

### Starting Services

**Backend:**
```bash
cd backend
docker compose up -d  # Starts all services with docker-compose.override.yml
# Backend automatically runs on http://localhost:8001 via nginx
# Django dev server inside container auto-reloads on code changes
```

**Note:** `docker-compose.override.yml` is automatically merged in development:
- Mounts your code directory to `/app` in containers
- Uses Django's `runserver` for auto-reload
- Changes to Python files are immediately visible (no rebuild needed)

**Frontend:**
```bash
cd frontend
npm run dev  # Runs on port 3001
```

### Making Database Changes

1. Modify model in `app_name/models.py`
2. Create migration: `python manage.py makemigrations`
3. Review migration file
4. Apply: `python manage.py migrate`
5. Update tests to reflect schema changes

### Adding New Persona

1. Create markdown file: `backend/personas/fixtures/{category}/{slug}.md`
2. **Run sync command (REQUIRED):** `python manage.py load_personas`
   - Without this, the new persona only exists as a file—not in the database
   - The API won't see it and users can't select it for debates
3. Verify in admin: http://localhost:8001/admin/personas/persona/
4. Test in frontend: Should appear in persona selection dropdowns

### Running Quality Checks

```bash
# Backend tests
docker compose exec web pytest --cov

# Frontend tests
npm test -- --run

# Lint frontend
npm run lint
```

## Deployment

**Target Infrastructure:**
- Backend: AWS Lightsail with Docker Compose
- Frontend: Vercel
- Domain: theinfinitedebate.com (ICDSoft)
- Database: PostgreSQL on Lightsail
- Redis: Redis on Lightsail

**Pre-Deployment Checklist:**
- [ ] All tests passing (backend + frontend)
- [ ] Coverage ≥ 60% on both sides
- [ ] Migrations applied to production DB
- [ ] Environment variables configured
- [ ] Stripe webhooks pointing to production
- [ ] Sentry DSN configured
- [ ] Health checks operational

**Deployment Commands:**

```bash
# Backend deployment to AWS Lightsail
# IMPORTANT: Use explicit -f flag to exclude docker-compose.override.yml
cd backend
docker compose -f docker-compose.yml build --no-cache
docker compose -f docker-compose.yml up -d
docker compose -f docker-compose.yml exec web python manage.py migrate
docker compose -f docker-compose.yml exec web python manage.py collectstatic --no-input

# Frontend deployment to Vercel
cd frontend
# Vercel handles deployment via git push
```

**⚠️ Development vs Production:**
- **Development**: Uses `docker-compose.override.yml` (auto-merged, mounts code, uses runserver)
- **Production**: Must use `-f docker-compose.yml` flag to exclude override file
- The override file enables live code changes in development but is dangerous in production

## Getting Help

- **Agent Documentation:** `.claude/agents/README.md`
- **Command Usage:** `.claude/commands/README.md`
- **Development Status:** `STATUS.md` (local working file)
- **Quality Reports:** `.reports/` (committed to git)

## Important Notes

- **STATUS.md is local only** - Don't commit it, use it for personal tracking
- **All agent outputs go to `.reports/`** - These ARE committed
- **Never hardcode counts** - Always discover state dynamically via queries
- **Use `/contribute` for all changes** - Ensures consistency and quality
- **Reports are project history** - They document decisions and provide context
