# Prompt the Past - Architecture Analysis Summary

## Quick Assessment

**Overall Quality Score: 8.5/10**

This is a **well-engineered, production-ready full-stack application** with thoughtful architecture, strong security practices, and modern development patterns. The codebase demonstrates professional software engineering standards.

---

## Key Metrics

| Aspect | Score | Notes |
|--------|-------|-------|
| **Architecture Quality** | 9/10 | Clear domain separation, well-structured |
| **Security** | 8/10 | Strong sanitization, HTTPS, rate limiting; needs webhook verification |
| **Code Quality** | 8.5/10 | TypeScript strict mode, PEP 8, good documentation |
| **Scalability** | 8/10 | Celery + Redis; could optimize concurrency |
| **Testing** | 7/10 | 60% coverage; good fixtures; missing integration tests |
| **Documentation** | 8/10 | CLAUDE.md complete; could use more API docs |
| **DevOps** | 9/10 | Docker setup excellent; health checks, monitoring |

---

## Technology Stack Overview

### Backend (Django 5.2 + DRF 3.16)
- **Framework:** Django REST Framework with ViewSets
- **Database:** PostgreSQL 14 with advanced indexing (GIN indexes, composite indexes)
- **Task Queue:** Celery 5.5 + Redis 8 (for debate generation)
- **Search:** PostgreSQL full-text search with GIN indexes
- **Payment:** Stripe with webhook handlers
- **Monitoring:** Sentry error tracking
- **API Docs:** drf-spectacular (OpenAPI 3.0)

### Frontend (Next.js 15.5)
- **Framework:** React 19 with TypeScript 5 (strict mode)
- **Styling:** Material-UI v7 + Emotion CSS-in-JS
- **Data Fetching:** React Query v5 + Axios with interceptors
- **Testing:** Vitest + React Testing Library
- **State:** React Context (auth) + Axios interceptors

### Infrastructure
- **Containers:** Docker Compose (7 services)
- **Production:** Gunicorn + Nginx + Certbot (Let's Encrypt)
- **Broker:** Redis (pub/sub for real-time updates)
- **Monitoring:** Flower (Celery task UI) + Health checks

---

## Architecture Highlights

### 1. **6 Well-Organized Django Apps**

```
debates/      → Debate orchestration, generation, streaming
personas/     → Historical figures with dual-storage (markdown + DB)
users/        → Custom user model, subscriptions, JWT auth
payments/     → Stripe integration with webhooks
texts/        → Primary source library with full-text search
health/       → Kubernetes-style health/readiness checks
```

### 2. **Security-First Design**

- **3-Layer Sanitization:** HTML-safe markdown → plain text
- **Model Signal Handlers:** Auto-sanitize all inputs on pre_save
- **HTTPS/TLS:** HSTS headers, secure cookies in production
- **Rate Limiting:** Anonymous (20/hr), Authenticated (100/hr), Debates (10/hr)
- **Credit System:** Prevents overages; billing validation on creation

### 3. **Real-Time Debate Streaming**

```
Celery Worker generates debate
  → Publishes events to Redis channel
  → Frontend SSE listener receives updates
  → TypeWriter animation plays messages in real-time
  → No polling; efficient pub/sub architecture
```

### 4. **Subscription & Billing**

- **Tier Structure:** Trial (15 credits), Starter ($10), Pro ($25)
- **Credit System:** `credits = participants × rounds × depth_multiplier`
- **Stripe Integration:** Webhooks handle subscription events
- **Idempotent Processing:** Event ID prevents duplicate processing

### 5. **Query Optimization**

- Prefetch_related documented in every serializer
- Composite indexes: `[debate, round_number, persona]`
- Serializer specialization: List (lightweight) vs. Detail (nested)
- Reduces N+1 queries significantly

---

## Critical Issues (Fix Before Production)

### 🔴 HIGH PRIORITY

1. **Stripe Webhook Signature Verification Missing**
   - Current: Blindly trusts webhook events
   - Fix: Implement HMAC signature validation
   ```python
   import hmac
   signature = request.headers.get('Stripe-Signature')
   assert hmac.compare_digest(signature, expected_signature)
   ```

2. **Race Condition in Credit Deduction**
   - Current: User A and B both create debates with same credits
   - Both checks pass, both deduct, user goes negative
   - Fix: Use `select_for_update()` in serializer
   ```python
   user = User.objects.select_for_update().get(id=user_id)
   ```

3. **No Timeout on Debate Generation**
   - Long debates could hang indefinitely
   - Fix: Add `time_limit` to Celery task

### 🟡 MEDIUM PRIORITY

4. **Inconsistent Error Response Format**
   - Some endpoints return `{'error': 'msg'}`, others `{'detail': 'msg'}`
   - Fix: Create custom exception handler to normalize

5. **Missing Integration Tests**
   - No end-to-end tests (create → generate → complete)
   - No concurrent credit tests
   - Effort: 2-3 days to add comprehensive suite

6. **Limited Frontend Testing**
   - Only test utilities visible; few component tests
   - Effort: 1-2 days for critical path coverage

---

## Scalability Assessment

### Current Capacity (Estimated)

| Component | Capacity | Bottleneck |
|-----------|----------|------------|
| **Celery Workers** | 2 concurrent debates | Concurrency too low |
| **Gunicorn Workers** | 3 (30-50 RPS) | Could scale to 8-12 |
| **Database Connections** | ~20 pools | PostgreSQL limit: ∞ |
| **Redis** | Single instance | OK for small traffic |
| **Nginx** | 1000+ concurrent | OK for production |

### Scaling Recommendations

1. **Increase Celery Concurrency:** From 2 to 4-8 (benchmark first)
2. **Add Celery Queues:** Separate priority queues for fast vs. thorough debates
3. **Database Connection Pooling:** Use PgBouncer for PostgreSQL
4. **Redis Clustering:** For high-traffic scenarios
5. **Frontend Caching:** Cache persona list, debate templates
6. **CDN:** Serve static assets + debate PDFs from CloudFront

---

## Architectural Patterns

### Good Patterns Used

1. **ViewSet Pattern** - Standard CRUD auto-generated
2. **Serializer Specialization** - List vs. Detail vs. Create
3. **Signal Handlers** - Cross-cutting concerns (sanitization)
4. **State Machine** - Debate lifecycle enforcement
5. **SSE + Pub/Sub** - Real-time decoupled from generation
6. **Prefetch Documentation** - Every serializer explains optimization
7. **Error Handling** - Tries/except with graceful degradation
8. **Environment Isolation** - Development vs. Production configs

### Trade-offs Made

| Decision | Pros | Cons |
|----------|------|------|
| **Dual-Storage (Personas)** | Version control, human-editable | Sync required |
| **TextField for Transcript** | Simple, self-contained | No pagination |
| **Celery Concurrency=2** | Low resource usage | Bottleneck at scale |
| **JWT in Cookies** | Prevents CSRF | Single-domain only |
| **Search Vector** | Fast FTS queries | Staleness possible |

---

## Production Readiness Checklist

- [ ] Fix Stripe webhook signature verification (HIGH)
- [ ] Add select_for_update() to credit deduction (HIGH)
- [ ] Document JWT TTL and token rotation strategy (MEDIUM)
- [ ] Add integration tests for core flows (MEDIUM)
- [ ] Test error scenarios and edge cases (MEDIUM)
- [ ] Load test Celery with concurrent debates (MEDIUM)
- [ ] Stress test database connections (LOW)
- [ ] Implement API error response normalization (LOW)
- [ ] Add comprehensive logging (LOW)
- [ ] Document scaling procedures (LOW)

---

## What's Great

1. ✅ **Clear Separation of Concerns** - Each Django app has a single responsibility
2. ✅ **Security by Default** - Multiple validation layers; sanitization everywhere
3. ✅ **Type Safety** - TypeScript strict mode + Python type hints
4. ✅ **Async Architecture** - Celery + Redis for scalability
5. ✅ **Real-time Updates** - SSE + pub/sub (not polling)
6. ✅ **Modern Frontend** - Next.js App Router, React 19
7. ✅ **Production-Ready Docker** - Health checks, proper secrets
8. ✅ **Thoughtful Design** - Credits, tiers, subscriptions all integrated

---

## What Needs Improvement

1. ⚠️ **Security Gaps** - Stripe webhook validation, race conditions
2. ⚠️ **Test Coverage** - Missing integration and edge-case tests
3. ⚠️ **Error Handling** - Inconsistent response formats
4. ⚠️ **Scalability** - Celery concurrency too low; Gunicorn workers could scale
5. ⚠️ **Logging** - Minimal logging outside error paths
6. ⚠️ **Component Size** - Some frontend pages very large (827 lines)
7. ⚠️ **API Documentation** - Could use more examples and error codes

---

## Development Workflow

### Starting Services
```bash
# Backend
cd backend
docker compose up -d

# Frontend
cd frontend
npm run dev

# Access:
# - API: http://localhost:8001/api/
# - Docs: http://localhost:8001/api/docs/
# - Frontend: http://localhost:3001
# - Flower: http://localhost:5555 (admin/admin)
```

### Running Tests
```bash
# Backend
docker compose exec web pytest --cov

# Frontend
npm test -- --run
npm run test:coverage
```

### Deployment
```bash
# Production (exclude override file!)
docker compose -f docker-compose.yml build
docker compose -f docker-compose.yml up -d
docker compose -f docker-compose.yml exec web python manage.py migrate
```

---

## Estimated Development Timeline

| Task | Effort | Priority |
|------|--------|----------|
| Fix Stripe webhook verification | 4 hours | HIGH |
| Add select_for_update() to credits | 2 hours | HIGH |
| Integration test suite | 2-3 days | MEDIUM |
| Frontend component tests | 1-2 days | MEDIUM |
| Error response normalization | 4 hours | MEDIUM |
| Celery performance tuning | 1 day | MEDIUM |
| Full logging implementation | 2-3 days | LOW |
| Documentation improvements | 1 day | LOW |

**Total for Production: ~5-6 days (fixes only) or ~12-14 days (comprehensive)**

---

## Conclusion

**Prompt the Past is well-architected and production-ready with minor fixes needed.**

### Recommendation: **DEPLOY with HIGH-PRIORITY fixes**

The application demonstrates professional engineering standards with clear architecture, strong security (mostly), and modern development practices. The two critical security issues (Stripe validation, race condition) should be fixed before production, but the overall system is solid.

**Quality Rating: 8.5/10 overall → 9.0/10 after fixes**

For detailed analysis of each component, see: `ARCHITECTURE_ANALYSIS.md`
