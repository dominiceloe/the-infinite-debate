# Test Coverage Gap Analysis
**Date:** October 19, 2025
**Project:** Prompt the Past - Historical Debate Platform
**Analysis By:** Test Maintainer Agent

---

## Executive Summary

### Current Coverage Status

**Backend (Django REST API):**
- **Overall Coverage:** 21.73% (379/1744 lines)
- **Status:** CRITICAL - Far below production readiness threshold
- **Test Infrastructure:** 155 tests exist but require Docker/PostgreSQL setup
- **Blockers:** Tests configured for Docker environment, won't run in local venv

**Frontend (Next.js):**
- **Overall Coverage:** 52.95% statements
- **Branch Coverage:** 89.37%
- **Function Coverage:** 73.33%
- **Status:** MODERATE - Approaching acceptable levels but gaps remain
- **Test Infrastructure:** 9 test files, 135 passing tests

### Production Readiness Assessment

| Tier | Target | Backend | Frontend | Status |
|------|--------|---------|----------|--------|
| **Critical modules** (auth, payments, debate generation) | 80%+ | ~18% | ~53% | HIGH RISK |
| **Core modules** (API endpoints, models) | 60%+ | ~22% | ~53% | AT RISK |
| **Overall platform** | 60%+ | 22% | 53% | NOT READY |

---

## Backend Coverage Analysis (Django REST API)

### Coverage by Module

| Module | Statements | Covered | Coverage | Priority | Status |
|--------|-----------|---------|----------|----------|--------|
| **CRITICAL BUSINESS LOGIC** |
| `debates/generator.py` | 69 | 13 | **18.84%** | CRITICAL | Missing core debate generation logic |
| `debates/views.py` | 61 | 0 | **0.00%** | CRITICAL | No API endpoint tests |
| `debates/tasks.py` | 27 | 6 | **22.22%** | CRITICAL | Celery async generation untested |
| `payments/views.py` | 204 | 0 | **0.00%** | CRITICAL | Stripe webhooks, subscriptions untested |
| `users/views.py` | 113 | 0 | **0.00%** | CRITICAL | Auth endpoints (login/register) untested |
| `users/serializers.py` | 86 | 0 | **0.00%** | CRITICAL | User validation untested |
| **HIGH IMPACT** |
| `texts/citation_extractor.py` | 97 | 15 | **15.46%** | HIGH | Citation linking to sources |
| `texts/validators.py` | 167 | 0 | **0.00%** | HIGH | Gutenberg URL, citation validation |
| `texts/views.py` | 79 | 0 | **0.00%** | HIGH | Primary text API untested |
| `texts/serializers.py` | 43 | 40 | **93.02%** | HIGH | Good coverage |
| `personas/views.py` | 55 | 0 | **0.00%** | HIGH | Persona API untested |
| `personas/serializers.py` | 30 | 28 | **93.33%** | HIGH | Good coverage |
| **MEDIUM IMPACT** |
| `debates/serializers.py` | 67 | 33 | **49.25%** | MEDIUM | Partial coverage |
| `debates/prompts.py` | 47 | 5 | **10.64%** | MEDIUM | Prompt building logic |
| `debates/utils.py` | 60 | 4 | **6.67%** | MEDIUM | Utility functions |
| `debates/pdf_export.py` | 114 | 0 | **0.00%** | MEDIUM | PDF generation untested |
| `texts/signals.py` | 23 | 6 | **26.09%** | MEDIUM | Auto-citation extraction |
| `users/models.py` | 60 | 30 | **50.00%** | MEDIUM | Partial coverage |
| **WELL TESTED** |
| `debates/models.py` | 38 | 37 | **97.37%** | LOW | Excellent |
| `personas/models.py` | 48 | 47 | **97.92%** | LOW | Excellent |
| `payments/models.py` | 39 | 39 | **100%** | LOW | Excellent |
| `texts/models.py` | 71 | 65 | **91.55%** | LOW | Excellent |

### Critical Gaps Identified

#### 1. Authentication & Authorization (CRITICAL - 0% Coverage)
**Files:**
- `users/views.py` (113 lines, 0% coverage)
- `users/serializers.py` (86 lines, 0% coverage)

**Missing Tests:**
- User registration endpoint
- Login endpoint (JWT token generation)
- Token refresh logic
- Password reset flow
- Profile retrieval
- Credit balance checks
- Tier validation

**Business Impact:** Security vulnerability, authentication bypass risk

#### 2. Payment Processing (CRITICAL - 0% Coverage)
**Files:**
- `payments/views.py` (204 lines, 0% coverage)

**Missing Tests:**
- Stripe checkout session creation
- Subscription webhooks (created, updated, deleted, payment failed)
- Payment intent webhooks
- Credit allocation on successful payment
- Subscription cancellation
- Proration handling
- Webhook signature validation

**Business Impact:** Revenue loss, incorrect billing, security issues

#### 3. Debate Generation (CRITICAL - 18-22% Coverage)
**Files:**
- `debates/generator.py` (69 lines, 18.84% coverage)
- `debates/views.py` (61 lines, 0% coverage)
- `debates/tasks.py` (27 lines, 22.22% coverage)

**Missing Tests:**
- Debate creation API endpoint
- Anthropic API call orchestration
- Opening statement generation
- Multi-round dialogue generation
- Consensus detection
- Error handling (API failures, rate limits)
- Credit deduction logic
- Celery task queuing
- Real-time status updates

**Business Impact:** Core product feature failure, poor UX, Anthropic API cost overruns

#### 4. Citation Extraction (HIGH - 15% Coverage)
**Files:**
- `texts/citation_extractor.py` (97 lines, 15.46% coverage)

**Missing Tests:**
- Debate message parsing for citations
- Primary text search and matching
- Passage extraction from Gutenberg texts
- Citation object creation
- Regex pattern matching for references

**Business Impact:** Key differentiator (academic credibility) broken

#### 5. Text & Persona APIs (HIGH - 0% Coverage)
**Files:**
- `texts/views.py` (79 lines, 0% coverage)
- `texts/validators.py` (167 lines, 0% coverage)
- `personas/views.py` (55 lines, 0% coverage)

**Missing Tests:**
- Primary text list/retrieve/search endpoints
- Citation list for debates
- Gutenberg URL validation
- Persona list (filtered by tier/category)
- Persona detail retrieval

**Business Impact:** Users can't browse texts/personas

---

## Frontend Coverage Analysis (Next.js)

### Coverage by Module

| Module | Statements | Branch | Functions | Lines | Status |
|--------|-----------|--------|-----------|-------|--------|
| **WELL TESTED** |
| `lib/tiers.ts` | 98.48% | 86.95% | 100% | 98.48% | Excellent |
| `lib/categories.ts` | 100% | 100% | 100% | 100% | Excellent |
| `lib/theme.ts` | 100% | 100% | 100% | 100% | Excellent |
| `lib/api/texts.ts` | 100% | 96.77% | 100% | 100% | Excellent |
| `hooks/useTypewriter.ts` | 100% | 100% | 100% | 100% | Excellent |
| `components/ProtectedRoute.tsx` | 100% | 100% | 100% | 100% | Excellent |
| **GOOD COVERAGE** |
| `components/MessageContent.tsx` | 91.04% | 100% | 33.33% | 91.04% | Good |
| `components/Header.tsx` | 88.51% | 62.5% | 25% | 88.51% | Good |
| `contexts/AuthContext.tsx` | 82.35% | 76.92% | 60% | 82.35% | Good |
| **CRITICAL GAPS** |
| `lib/api.ts` | **0%** | 0% | 0% | 0% | CRITICAL |
| `components/DebateTheaterView.tsx` | **0%** | 100% | 100% | 0% | CRITICAL |

### Critical Frontend Gaps

#### 1. API Client (CRITICAL - 0% Coverage)
**File:** `lib/api.ts` (257 lines, 0% coverage)

**Missing Tests:**
- Axios instance configuration
- JWT token injection in headers
- Token refresh on 401 errors
- API error handling
- Request/response interceptors
- Debate CRUD operations
- Persona fetching
- Text fetching
- User profile API calls

**Business Impact:** API communication failures undetected

#### 2. Debate Theater View (CRITICAL - 0% Coverage)
**File:** `components/DebateTheaterView.tsx` (652 lines, 0% coverage)

**Missing Tests:**
- Debate rendering (messages, participants)
- Real-time message streaming display
- Typewriter effect integration
- Debate status indicators (pending, generating, completed)
- Citation display and linking
- PDF export trigger
- Responsive layout

**Business Impact:** Core UX component untested, user-facing bugs

#### 3. Test Quality Issues
**File:** `contexts/AuthContext.test.tsx`

**Issues Found:**
- Multiple "act(...)" warnings (state updates not wrapped)
- Expected console errors for error cases (noisy logs)

**Recommendation:** Refactor to use `waitFor` and proper async patterns

---

## Priority Matrix for Test Development

### Priority = Business Impact × Code Complexity × Coverage Gap

| Rank | File | Impact | Complexity | Gap | Priority Score | Recommended Action |
|------|------|--------|------------|-----|----------------|-------------------|
| 1 | `payments/views.py` | CRITICAL | HIGH | 100% | 300 | Create Stripe webhook tests IMMEDIATELY |
| 2 | `users/views.py` | CRITICAL | MEDIUM | 100% | 200 | Create auth endpoint tests |
| 3 | `users/serializers.py` | CRITICAL | MEDIUM | 100% | 200 | Create user validation tests |
| 4 | `debates/generator.py` | CRITICAL | HIGH | 81% | 243 | Mock Anthropic API, test orchestration |
| 5 | `debates/views.py` | CRITICAL | MEDIUM | 100% | 200 | Create debate API endpoint tests |
| 6 | `debates/tasks.py` | CRITICAL | MEDIUM | 78% | 156 | Mock Celery, test async generation |
| 7 | `lib/api.ts` (frontend) | CRITICAL | MEDIUM | 100% | 200 | Mock axios, test API client |
| 8 | `components/DebateTheaterView.tsx` | CRITICAL | HIGH | 100% | 300 | Component tests with mock data |
| 9 | `texts/citation_extractor.py` | HIGH | HIGH | 85% | 170 | Test citation parsing logic |
| 10 | `texts/validators.py` | HIGH | MEDIUM | 100% | 150 | Test Gutenberg URL validation |
| 11 | `texts/views.py` | HIGH | MEDIUM | 100% | 150 | Test primary text endpoints |
| 12 | `personas/views.py` | HIGH | LOW | 100% | 100 | Test persona list/retrieve |
| 13 | `debates/pdf_export.py` | MEDIUM | HIGH | 100% | 150 | Test PDF generation |
| 14 | `debates/prompts.py` | MEDIUM | MEDIUM | 89% | 111 | Test prompt building |
| 15 | `debates/serializers.py` | MEDIUM | MEDIUM | 51% | 51 | Increase coverage to 80%+ |

---

## Test Infrastructure Assessment

### Backend (pytest-django)

**Strengths:**
- Test structure exists (155 tests written)
- Good model coverage (97%+ for Debate, Persona, Payment models)
- Pytest configuration is comprehensive (`pytest.ini`, `.coveragerc`)
- Fixtures defined in `conftest.py`

**Weaknesses:**
- Tests require Docker/PostgreSQL to run (won't run in local venv)
- Database connection failures blocking test execution
- `test_views.py` filename collision between apps
- Tests not running in CI/CD (assumption based on errors)

**Recommendations:**
1. **Fix test execution:** Set up SQLite for tests or document Docker requirement
2. **Rename conflicting files:** Use unique names like `test_debate_views.py`
3. **Add test running instructions** to README
4. **Create mocking strategy** for Anthropic API, Stripe webhooks, Celery tasks

### Frontend (Vitest)

**Strengths:**
- Modern testing setup (Vitest, Testing Library, happy-dom)
- 135 passing tests
- Good utility/lib coverage
- Clear test organization

**Weaknesses:**
- No component tests for DebateTheaterView (652 lines untested)
- No API client tests (257 lines untested)
- Some tests have `act()` warnings (quality issue)
- Missing tests for page components (excluded from coverage)

**Recommendations:**
1. **Create DebateTheaterView tests** with mock debate data
2. **Create API client tests** with mocked axios
3. **Fix act() warnings** in AuthContext tests
4. **Consider E2E tests** for page components (Playwright/Cypress)

---

## Recommended Testing Roadmap

### Phase 1: Critical Security & Revenue (Week 1)
**Goal:** Secure authentication and payment systems

1. **Payments Module** (Priority #1)
   - Create `backend/payments/tests/test_webhooks.py`
   - Mock Stripe webhook events (subscription.created, payment_intent.succeeded, etc.)
   - Test webhook signature validation
   - Test credit allocation logic
   - Target: 80%+ coverage

2. **Users Module** (Priority #2-3)
   - Create `backend/users/tests/test_authentication.py`
   - Test registration, login, token refresh endpoints
   - Test JWT token generation and validation
   - Test tier restrictions and credit checks
   - Target: 70%+ coverage

3. **User Serializers** (Priority #3)
   - Create `backend/users/tests/test_user_serializers.py`
   - Test email validation
   - Test password strength requirements
   - Test profile data serialization
   - Target: 80%+ coverage

**Expected Outcome:** Backend coverage → 35-40%

### Phase 2: Core Debate Functionality (Week 2)
**Goal:** Ensure debate generation works reliably

4. **Debate Generator** (Priority #4)
   - Create `backend/debates/tests/test_generator.py`
   - Mock Anthropic API responses
   - Test opening statement generation
   - Test multi-round dialogue
   - Test error handling (API failures, invalid responses)
   - Target: 80%+ coverage

5. **Debate Views** (Priority #5)
   - Enhance `backend/debates/tests/test_views.py` (currently failing)
   - Test debate creation endpoint
   - Test debate list/retrieve
   - Test authorization (users can't access others' debates)
   - Target: 80%+ coverage

6. **Debate Tasks** (Priority #6)
   - Create `backend/debates/tests/test_celery_tasks.py`
   - Mock Celery task execution
   - Test async debate generation
   - Test task failure handling
   - Target: 70%+ coverage

**Expected Outcome:** Backend coverage → 50-55%

### Phase 3: Frontend Core Components (Week 2)
**Goal:** Test user-facing debate experience

7. **API Client** (Priority #7)
   - Create `frontend/__tests__/lib/api.test.ts`
   - Mock axios responses
   - Test token injection
   - Test token refresh on 401
   - Test error handling
   - Target: 80%+ coverage

8. **DebateTheaterView** (Priority #8)
   - Create `frontend/__tests__/components/DebateTheaterView.test.tsx`
   - Test debate rendering
   - Test message display
   - Test citation links
   - Test export button
   - Target: 60%+ coverage (large component)

**Expected Outcome:** Frontend coverage → 65-70%

### Phase 4: Academic Features (Week 3)
**Goal:** Ensure citation system works

9. **Citation Extractor** (Priority #9)
   - Create `backend/texts/tests/test_citation_extractor.py`
   - Test citation pattern matching
   - Test primary text lookup
   - Test passage extraction from Gutenberg
   - Target: 70%+ coverage

10. **Text Validators** (Priority #10)
    - Create `backend/texts/tests/test_validators.py`
    - Test Gutenberg URL validation
    - Test citation format validation
    - Target: 70%+ coverage

11. **Text Views** (Priority #11)
    - Create `backend/texts/tests/test_text_views.py`
    - Test primary text list/retrieve
    - Test citation endpoints
    - Target: 70%+ coverage

**Expected Outcome:** Backend coverage → 60%+, Frontend → 70%+

### Phase 5: Polish & Quality (Week 4)
**Goal:** Reach production-ready thresholds

12. **Increase Backend Coverage to 65%+**
    - Add tests for `debates/prompts.py`
    - Add tests for `debates/pdf_export.py`
    - Add tests for `personas/views.py`
    - Fill gaps in serializers

13. **Increase Frontend Coverage to 75%+**
    - Fix AuthContext `act()` warnings
    - Add missing component tests
    - Add missing hook tests

14. **Integration Tests**
    - Create end-to-end debate creation flow test
    - Create subscription upgrade flow test
    - Create citation extraction integration test

15. **Test Quality Audit**
    - Review all tests for brittleness
    - Improve test descriptions
    - Ensure proper mocking
    - Document testing patterns

**Expected Outcome:** Backend → 65%+, Frontend → 75%+

---

## Coverage Thresholds by Module

### Recommended Targets

| Module Category | Minimum Target | Rationale |
|----------------|----------------|-----------|
| **Payment Processing** | 85% | Revenue-critical, regulatory compliance |
| **Authentication** | 80% | Security-critical, user data protection |
| **Debate Generation** | 75% | Core product feature, complex logic |
| **API Endpoints** | 70% | User-facing, integration points |
| **Citation System** | 70% | Key differentiator, academic credibility |
| **Models** | 90% | Already achieved, maintain |
| **Serializers** | 80% | Data validation, API contracts |
| **Utilities** | 60% | Supporting code |
| **PDF Export** | 50% | Nice-to-have feature |
| **Admin Interfaces** | 40% | Internal tools only |

### Overall Platform Targets

| Milestone | Backend | Frontend | Status |
|-----------|---------|----------|--------|
| **Current** | 21.73% | 52.95% | CRITICAL |
| **Phase 1 Complete** | 40% | 53% | AT RISK |
| **Phase 2 Complete** | 55% | 70% | APPROACHING |
| **Phase 3 Complete** | 60% | 70% | ACCEPTABLE |
| **Phase 4 Complete** | 65% | 75% | PRODUCTION READY |
| **Ideal State** | 70%+ | 80%+ | EXCELLENT |

---

## Files Ready for Testing (Existing Tests Need Fixes)

### Currently Failing Tests

1. **Database Connection Issues**
   - All test files expect PostgreSQL running in Docker
   - Error: `could not translate host name "db" to address`
   - Fix: Update test settings to use SQLite or document Docker setup

2. **Test File Name Collisions**
   - `users/tests/test_views.py` conflicts with `personas/tests/test_views.py`
   - Error: `imported module 'test_views' has this __file__ attribute`
   - Fix: Rename to unique names (`test_user_views.py`, `test_persona_views.py`)

3. **Test Count**
   - 155 tests collected (good sign - substantial test suite exists)
   - Once database + naming issues fixed, these will provide baseline coverage

---

## Next Steps

### Immediate Actions (This Week)

1. **Fix Test Execution Environment**
   - Document Docker setup for running tests
   - OR configure SQLite for pytest
   - Verify all 155 tests pass

2. **Create Payment Tests** (Priority #1)
   - Start with `test_webhooks.py`
   - Mock Stripe events
   - 80%+ coverage target

3. **Create Auth Tests** (Priority #2)
   - Start with `test_authentication.py`
   - Test login/register/refresh
   - 70%+ coverage target

4. **Create Frontend API Tests** (Priority #7)
   - Start with `lib/api.test.ts`
   - Mock axios
   - 80%+ coverage target

### Success Metrics

**Week 1:** Backend 35%, Frontend 60%
**Week 2:** Backend 50%, Frontend 65%
**Week 3:** Backend 60%, Frontend 70%
**Week 4:** Backend 65%, Frontend 75%

---

## Testing Best Practices for This Project

### Backend (pytest-django)

**Mocking Strategy:**
- **Anthropic API:** Use `@patch('debates.generator.Anthropic')` with mock responses
- **Stripe:** Use `@patch('stripe.Webhook.construct_event')` for webhooks
- **Celery:** Use `@patch('debates.tasks.generate_debate_task.delay')`
- **Email:** Use `@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')`

**Fixture Strategy:**
- Create `test_user` fixture with credits
- Create `test_free_user` fixture without credits
- Create `test_debate` fixture with participants
- Create `test_personas` fixture with sample historical figures
- Create `test_primary_text` fixture with Gutenberg data

**API Testing Pattern:**
```python
@pytest.mark.django_db
class TestDebateViewSet:
    def test_create_debate_success(self, api_client, test_user, test_personas):
        """Test creating debate with valid data and sufficient credits"""
        api_client.force_authenticate(user=test_user)
        data = {
            'topic': 'What is the nature of consciousness?',
            'participant_ids': [p.id for p in test_personas[:3]]
        }
        response = api_client.post('/api/debates/', data)
        assert response.status_code == 201
        assert test_user.profile.credits_remaining < test_user.profile.credits_total
```

### Frontend (Vitest)

**Mocking Strategy:**
- **Axios:** Use `vi.mock('axios')` with typed responses
- **Next.js Router:** Use `vi.mock('next/navigation')`
- **AuthContext:** Use `renderWithProviders` wrapper

**Component Testing Pattern:**
```typescript
describe('DebateTheaterView', () => {
  it('displays debate messages in chronological order', () => {
    const mockDebate = createMockDebate({ messageCount: 3 });
    render(<DebateTheaterView debate={mockDebate} />);

    const messages = screen.getAllByRole('article');
    expect(messages).toHaveLength(3);
    expect(messages[0]).toHaveTextContent(mockDebate.messages[0].content);
  });
});
```

---

## Conclusion

The Prompt the Past platform has **critical coverage gaps** that pose security and revenue risks:

- **Backend at 22%** coverage is far below production readiness
- **Frontend at 53%** coverage is approaching acceptable but has critical gaps
- **155 backend tests exist** but require infrastructure fixes to run
- **Payment processing (0%)**, **authentication (0%)**, and **debate generation (18%)** are high-risk areas

**Recommended immediate action:**
1. Fix test execution environment (Docker or SQLite)
2. Create payment webhook tests (Priority #1)
3. Create authentication endpoint tests (Priority #2)
4. Follow 4-week roadmap to reach 65% backend, 75% frontend coverage

**Estimated effort:** 4 weeks of focused test development to reach production-ready state.

**Risk if not addressed:** Security vulnerabilities, payment processing failures, unreliable debate generation, poor user experience.
