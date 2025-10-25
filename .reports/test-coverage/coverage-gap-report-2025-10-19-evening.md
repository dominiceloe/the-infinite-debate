# Test Coverage Gap Analysis Report

**Generated:** 2025-10-19 Evening
**Test Maintainer Agent:** Comprehensive Coverage Assessment
**Project:** Prompt the Past - Historical Persona Debates Platform

---

## Executive Summary

### Overall Coverage Status

| Component | Coverage | Status | Target |
|-----------|----------|--------|--------|
| **Backend (Django/DRF)** | **51.54%** | ⚠️ Below Target | 60%+ |
| **Frontend (Next.js/React)** | **93.9%** | ✅ Excellent | 60%+ |
| **Combined Platform** | **~72.7%** | ⚠️ Backend Needs Work | 60%+ |

### Test Execution Results

**Backend:**
- Total Tests: 568 collected
- Passing: 563 (99.1%)
- **Failing: 5** (0.9%) - Model field mismatches
- Execution Time: 13.74s

**Frontend:**
- Total Tests: 218
- Passing: 218 (100%)
- Failing: 0
- Execution Time: 2.64s

### Critical Issues Identified

1. **5 Backend Test Failures** - Immediate fix required
   - `test_list_debates_authenticated` - Unexpected kwargs: 'tone', 'depth'
   - `test_list_debates_only_user_debates` - Same issue
   - `test_retrieve_debate` - Same issue
   - `test_retrieve_debate_wrong_user` - Same issue
   - `test_detail_view_prefetches_messages_and_personas` - Query count mismatch (7 vs 5)

2. **Critical Modules Below Target**
   - payments/views.py: 16.67% - **PAYMENT PROCESSING**
   - health/views.py: 22.58% - **K8S HEALTH CHECKS**
   - debates/citation_markup.py: 0% - **CITATION RENDERING**

---

## Backend Coverage Breakdown (51.54%)

### Detailed Module Analysis

| Module | Statements | Missed | Coverage | Priority |
|--------|-----------|--------|----------|----------|
| debates/citation_markup.py | 28 | 28 | **0.00%** | 🔴 CRITICAL |
| debates/pdf_export.py | 114 | 100 | **12.28%** | 🔴 CRITICAL |
| texts/validators.py | 167 | 141 | **15.57%** | 🔴 CRITICAL |
| payments/views.py | 204 | 170 | **16.67%** | 🔴 CRITICAL |
| health/views.py | 31 | 24 | **22.58%** | 🔴 CRITICAL |
| debates/utils.py | 60 | 39 | **35.00%** | 🟠 HIGH |
| users/views.py | 113 | 72 | **36.28%** | 🟠 HIGH |
| texts/views.py | 79 | 49 | **37.97%** | 🟠 HIGH |
| personas/views.py | 55 | 29 | **47.27%** | 🟠 HIGH |
| texts/citation_extractor.py | 97 | 49 | **49.48%** | 🟠 HIGH |
| users/serializers.py | 86 | 43 | **50.00%** | 🟡 MEDIUM |
| users/models.py | 60 | 24 | **60.00%** | 🟡 MEDIUM |
| debates/prompts.py | 47 | 17 | **63.83%** | 🟡 MEDIUM |
| texts/signals.py | 23 | 8 | **65.22%** | 🟢 LOW |

### Well-Tested Modules (>90%)

✅ debates/models.py: **100%**
✅ debates/views.py: **100%**
✅ debates/throttles.py: **100%**
✅ debates/urls.py: **100%**
✅ payments/models.py: **100%**
✅ payments/urls.py: **100%**
✅ personas/models.py: **97.92%**
✅ personas/serializers.py: **93.33%**
✅ debates/serializers.py: **92.54%**
✅ debates/generator.py: **92.75%**
✅ texts/models.py: **91.55%**
✅ texts/serializers.py: **93.02%**

---

## Frontend Coverage Breakdown (93.9%)

### Component Coverage

| File | Statements | Branch | Functions | Lines | Status |
|------|-----------|--------|-----------|-------|--------|
| **Components** | **94.17%** | **87.09%** | **62.5%** | **94.17%** | ✅ |
| DebateTheaterView.tsx | 96.37% | 86.45% | 87.5% | 96.37% | ✅ |
| Header.tsx | 88.51% | 62.5% | 25% | 88.51% | ⚠️ |
| MessageContent.tsx | 91.04% | 100% | 33.33% | 91.04% | ⚠️ |
| ProtectedRoute.tsx | 100% | 100% | 100% | 100% | ✅ |

### Context/State Coverage

| File | Coverage | Branch | Status |
|------|----------|--------|--------|
| AuthContext.tsx | 82.35% | 76.92% | ⚠️ Needs improvement |

### Utility Coverage

| File | Coverage | Status |
|------|----------|--------|
| api.ts | 90.9% | ✅ |
| categories.ts | 100% | ✅ |
| theme.ts | 100% | ✅ |
| tiers.ts | 98.48% | ✅ |
| api/texts.ts | 100% | ✅ |
| hooks/useTypewriter.ts | 100% | ✅ |

### Frontend Gaps (Minor)

1. **Header.tsx** - Function coverage only 25% (likely untested button handlers)
2. **MessageContent.tsx** - Function coverage 33.33% (likely event handlers)
3. **AuthContext.tsx** - 4 act() warnings in tests, some error paths at 82.35%

---

## Prioritized Testing Roadmap

### Priority Matrix

```
Priority = Business Impact × Code Complexity × Coverage Gap

Business Impact:
- CRITICAL: Payment, auth, debate generation, health checks
- HIGH: API endpoints, data models, core user flows
- MEDIUM: Admin, utilities, helpers
- LOW: Internal tools, migrations

Code Complexity:
- HIGH: Complex algorithms, multiple paths, error handling
- MEDIUM: CRUD operations, transformations
- LOW: Simple getters, config, constants

Coverage Gap:
- HIGH: 0-30% covered
- MEDIUM: 30-60% covered
- LOW: 60%+ covered
```

---

## CRITICAL PRIORITY (Fix Immediately)

### 1. Fix 5 Failing Backend Tests

**Issue:** Model field mismatch - Debate model doesn't accept 'tone', 'depth' kwargs

**Files:**
- `debates/tests/test_views.py` (4 failures)
- `debates/tests/test_debate_views.py` (1 failure)

**Action Required:**
1. Check Debate model for removed/renamed fields
2. Update test fixtures to use current model schema
3. Verify all tests pass before proceeding with new test generation

**Estimated Effort:** 30 minutes

---

### 2. payments/views.py (16.67% → 80%+)

**Business Impact:** CRITICAL (Stripe payment processing)
**Complexity:** HIGH (webhooks, idempotency, error handling)
**Gap:** HIGH (170/204 statements untested)

**Missing Coverage:**
- Lines 24-133: Stripe checkout session creation
- Lines 147-197: Subscription retrieval and management
- Lines 201-217: Portal session creation
- Lines 221-256: Subscription cancellation
- Lines 260-301: Payment history
- Lines 305-323: Subscription update
- Lines 327-346: Webhook idempotency checks
- Lines 350-370: Subscription event handling
- Lines 380-403: Invoice payment handling
- Lines 413-434: Payment failed handling
- Lines 447-463: Customer deletion

**Required Tests:**
```python
# backend/payments/tests/test_views.py
- test_create_checkout_session_success
- test_create_checkout_session_invalid_tier
- test_get_subscription_active
- test_get_subscription_none
- test_cancel_subscription_success
- test_cancel_subscription_not_found
- test_payment_history_paginated
- test_webhook_subscription_created (mock Stripe event)
- test_webhook_subscription_updated (mock Stripe event)
- test_webhook_invoice_payment_succeeded (mock Stripe event)
- test_webhook_invoice_payment_failed (mock Stripe event)
- test_webhook_idempotency (prevent duplicate processing)
- test_webhook_invalid_signature
```

**Estimated Effort:** 4-6 hours
**Priority Score:** 10/10 (CRITICAL × HIGH × HIGH)

---

### 3. health/views.py (22.58% → 90%+)

**Business Impact:** CRITICAL (Kubernetes liveness/readiness probes)
**Complexity:** MEDIUM (simple checks but critical for deployment)
**Gap:** HIGH (24/31 statements untested)

**Missing Coverage:**
- Lines 16-27: Liveness probe implementation
- Lines 41-66: Readiness probe with DB/cache checks

**Required Tests:**
```python
# backend/health/tests/test_views.py
- test_health_check_returns_200
- test_health_check_response_format
- test_readiness_check_all_healthy
- test_readiness_check_db_failure
- test_readiness_check_cache_failure
- test_readiness_check_response_format
```

**Estimated Effort:** 1-2 hours
**Priority Score:** 9/10 (CRITICAL × MEDIUM × HIGH)

---

### 4. debates/citation_markup.py (0% → 80%+)

**Business Impact:** HIGH (Citation rendering in debates)
**Complexity:** MEDIUM (text processing and markup)
**Gap:** HIGH (28/28 statements untested)

**Missing Coverage:**
- Lines 7-82: All citation markup logic

**Required Tests:**
```python
# backend/debates/tests/test_citation_markup.py
- test_extract_citations_from_text
- test_markup_citations_inline
- test_markup_citations_with_links
- test_handle_invalid_citation_format
- test_markup_multiple_citations
- test_markup_citations_empty_text
```

**Estimated Effort:** 2-3 hours
**Priority Score:** 8/10 (HIGH × MEDIUM × HIGH)

---

## HIGH PRIORITY (Next Sprint)

### 5. debates/pdf_export.py (12.28% → 70%+)

**Business Impact:** HIGH (Academic export feature)
**Complexity:** HIGH (PDF generation with citations)
**Gap:** HIGH (100/114 statements untested)

**Missing Coverage:**
- Lines 28-77: PDF styling and formatting
- Lines 82-179: Content generation
- Lines 184-206: Citation formatting
- Lines 211-233: Header/footer generation
- Lines 238-247: Table of contents
- Lines 252-305: Section rendering
- Lines 310-320: Error handling

**Required Tests:**
```python
# backend/debates/tests/test_pdf_export.py
- test_generate_pdf_basic_debate
- test_generate_pdf_with_citations
- test_generate_pdf_formatting
- test_generate_pdf_table_of_contents
- test_generate_pdf_error_handling
- test_generate_pdf_empty_debate
```

**Estimated Effort:** 4-5 hours
**Priority Score:** 7/10 (HIGH × HIGH × HIGH)

---

### 6. texts/validators.py (15.57% → 70%+)

**Business Impact:** HIGH (Data quality, citation accuracy)
**Complexity:** HIGH (validation rules, confidence scoring)
**Gap:** HIGH (141/167 statements untested)

**Missing Coverage:**
- Lines 59-64, 71-74: Basic validation
- Lines 90-137: Citation matching algorithms
- Lines 155-171: Confidence scoring
- Lines 184-186: Error handling
- Lines 208-297: Advanced validation logic
- Lines 327-366: Text section validation
- Lines 373-376, 401-465: Edge cases

**Required Tests:**
```python
# backend/texts/tests/test_validators.py
- test_validate_text_title_required
- test_validate_text_author_format
- test_validate_citation_match_high_confidence
- test_validate_citation_match_low_confidence
- test_validate_citation_no_match
- test_validate_text_section_hierarchy
- test_validate_url_format
```

**Estimated Effort:** 5-6 hours
**Priority Score:** 7/10 (HIGH × HIGH × HIGH)

---

### 7. users/views.py (36.28% → 70%+)

**Business Impact:** CRITICAL (Authentication, user management)
**Complexity:** MEDIUM (JWT auth, profile updates)
**Gap:** MEDIUM (72/113 statements untested)

**Missing Coverage:**
- Lines 49-54: Registration error handling
- Lines 119-140: Login edge cases
- Lines 166, 186-202: Token refresh
- Lines 227-233: Profile update
- Lines 260-265: Password change
- Lines 292-318: User deletion
- Lines 347-398: Credit management

**Required Tests:**
```python
# backend/users/tests/test_views.py
- test_register_duplicate_email
- test_register_invalid_password
- test_login_invalid_credentials
- test_login_inactive_user
- test_token_refresh_expired
- test_profile_update_authenticated
- test_profile_update_email_taken
- test_password_change_wrong_old_password
- test_credit_deduction_insufficient_credits
```

**Estimated Effort:** 3-4 hours
**Priority Score:** 7/10 (CRITICAL × MEDIUM × MEDIUM)

---

### 8. texts/views.py (37.97% → 70%+)

**Business Impact:** HIGH (Primary text library API)
**Complexity:** MEDIUM (CRUD with search/filter)
**Gap:** MEDIUM (49/79 statements untested)

**Missing Coverage:**
- Lines 40-42, 48-70: Text list filtering
- Lines 79-82, 91-94: Text retrieval
- Lines 109-130: Section retrieval
- Lines 154-156, 160-172: Citation queries

**Required Tests:**
```python
# backend/texts/tests/test_views.py
- test_list_texts_filter_by_category
- test_list_texts_filter_by_era
- test_list_texts_search_title
- test_list_texts_search_author
- test_retrieve_text_with_sections
- test_retrieve_text_citations
- test_retrieve_nonexistent_text
```

**Estimated Effort:** 2-3 hours
**Priority Score:** 6/10 (HIGH × MEDIUM × MEDIUM)

---

### 9. debates/utils.py (35.00% → 70%+)

**Business Impact:** MEDIUM (Helper functions)
**Complexity:** MEDIUM (Credit calculation, slug generation)
**Gap:** MEDIUM (39/60 statements untested)

**Missing Coverage:**
- Lines 30, 33, 36, 39, 42: Credit calculation logic
- Lines 52, 56, 60: Slug generation
- Lines 69-104: Topic suggestion
- Lines 126, 138: Debate summary utilities
- Lines 158-167: Formatting helpers

**Required Tests:**
```python
# backend/debates/tests/test_utils.py
- test_calculate_credits_basic
- test_calculate_credits_depth_level
- test_generate_slug_from_topic
- test_generate_slug_uniqueness
- test_suggest_topic_for_personas
- test_format_debate_summary
```

**Estimated Effort:** 2-3 hours
**Priority Score:** 5/10 (MEDIUM × MEDIUM × MEDIUM)

---

## MEDIUM PRIORITY (Future Iterations)

### 10. texts/citation_extractor.py (49.48% → 70%+)

**Estimated Effort:** 3-4 hours
**Priority Score:** 5/10

### 11. personas/views.py (47.27% → 70%+)

**Estimated Effort:** 2-3 hours
**Priority Score:** 4/10

### 12. users/serializers.py (50.00% → 70%+)

**Estimated Effort:** 2-3 hours
**Priority Score:** 4/10

### 13. users/models.py (60.00% → 80%+)

**Estimated Effort:** 2 hours
**Priority Score:** 3/10

### 14. debates/prompts.py (63.83% → 80%+)

**Estimated Effort:** 2 hours
**Priority Score:** 3/10

---

## Frontend Improvements (Optional)

### Minor Gaps to Address

1. **Header.tsx** - Test button click handlers (25% → 80% function coverage)
2. **MessageContent.tsx** - Test citation link handlers (33% → 80% function coverage)
3. **AuthContext.tsx** - Fix act() warnings, test error recovery paths (82% → 90%)

**Estimated Combined Effort:** 2-3 hours
**Priority:** LOW (already above 80% overall)

---

## Estimated Timeline to 60% Backend Coverage

### Phase 1: Critical Fixes (Week 1)
- **Day 1:** Fix 5 failing tests (30 min)
- **Days 1-2:** payments/views.py tests (6 hours)
- **Day 3:** health/views.py tests (2 hours)
- **Day 4:** debates/citation_markup.py tests (3 hours)

**Expected Coverage After Phase 1:** ~56%

### Phase 2: High Priority (Week 2)
- **Days 5-6:** debates/pdf_export.py tests (5 hours)
- **Days 7-8:** texts/validators.py tests (6 hours)
- **Days 9-10:** users/views.py tests (4 hours)

**Expected Coverage After Phase 2:** ~62%

### Phase 3: Remaining High Priority (Week 3)
- **Days 11-12:** texts/views.py tests (3 hours)
- **Days 13-14:** debates/utils.py tests (3 hours)

**Expected Coverage After Phase 3:** ~65%

**Total Estimated Effort:** 32-38 hours of focused test development

---

## Testing Infrastructure Status

### Backend Testing (pytest-django)

✅ **Strengths:**
- Excellent fixture setup in conftest.py
- Good use of pytest-django patterns
- Comprehensive Celery integration tests
- Good API endpoint test coverage (debates/tests/test_debate_views.py)

⚠️ **Areas for Improvement:**
- Need Stripe webhook mocking fixtures
- Missing fixtures for primary texts and citations
- Need better error scenario testing
- Add more edge case coverage

### Frontend Testing (Vitest + Testing Library)

✅ **Strengths:**
- Comprehensive component tests
- Excellent API client mocking
- Good use of renderWithProviders pattern
- Strong hook testing (useTypewriter 100%)

⚠️ **Minor Issues:**
- Some act() warnings in AuthContext tests
- Could improve function coverage for event handlers

---

## Recommendations

### Immediate Actions (This Week)

1. **Fix 5 failing backend tests** - Blocks further test development
2. **Generate payments/views.py tests** - Critical business impact
3. **Generate health/views.py tests** - Critical for K8s deployment
4. **Generate debates/citation_markup.py tests** - Currently 0% coverage

### Short-term Goals (Next 2 Weeks)

5. Achieve **60%+ backend coverage** via Phase 1-2 roadmap
6. Add comprehensive Stripe webhook tests with idempotency
7. Improve error handling test coverage across all critical modules

### Long-term Goals (Next Month)

8. Achieve **70%+ backend coverage** for production readiness
9. Maintain **90%+ frontend coverage**
10. Establish CI/CD coverage enforcement (fail builds below 60%)
11. Create test documentation and patterns guide

---

## Coverage Enforcement Strategy

### Proposed CI/CD Rules

```yaml
# .github/workflows/tests.yml
coverage:
  backend:
    minimum: 60%
    critical_modules:
      payments: 80%
      users: 70%
      debates/generator: 85%
  frontend:
    minimum: 80%
```

### Pre-commit Hooks

- Run tests before commit
- Prevent coverage regression (new code must be tested)
- Auto-format test files

---

## Quality Metrics

### Test Quality Indicators

✅ **Good Practices Observed:**
- Clear test names following `test_{what}_{condition}_{result}` pattern
- Proper use of AAA (Arrange, Act, Assert) pattern
- Good fixture reuse
- Comprehensive API endpoint testing
- Integration tests for Celery tasks

⚠️ **Areas to Watch:**
- Ensure all new tests follow existing patterns
- Add docstrings to complex test cases
- Keep test execution time under 30s for backend
- Maintain test independence (no order dependencies)

---

## Conclusion

### Current State
- **Backend:** 51.54% (9 points below 60% target)
- **Frontend:** 93.9% (excellent, exceeds target)
- **Platform:** Strong foundation with critical gaps

### Path to Production Readiness
1. Fix 5 failing tests immediately
2. Focus on critical modules (payments, health, auth)
3. Execute Phase 1-2 roadmap (2 weeks, 32-38 hours)
4. Achieve 60%+ backend coverage for confidence

### Risk Assessment
- **HIGH RISK:** Payment processing under-tested (16.67%)
- **HIGH RISK:** Health checks under-tested (22.58%)
- **MEDIUM RISK:** Citation system gaps
- **LOW RISK:** Frontend well-tested

**Recommended Action:** Execute Phase 1 (Critical Fixes) immediately before adding new features or deploying to production.

---

**Report Generated By:** Test Maintainer Agent
**Next Review:** After Phase 1 completion (1 week)
**Contact:** See test-maintainer.md for usage examples
