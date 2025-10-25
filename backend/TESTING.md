# Testing Guide

## Overview

The backend has 169 pytest tests covering models, serializers, views, Celery tasks, and health endpoints.

**Current Coverage**: 21.73% (379/1744 lines)

## Running Tests

### Method 1: Docker (Recommended)

Tests are configured to run inside Docker containers with PostgreSQL access.

```bash
# From the backend directory
cd /Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/backend

# Run all tests
docker compose exec web pytest

# Run with verbose output
docker compose exec web pytest -v

# Run with coverage report
docker compose exec web pytest --cov

# Run specific test file
docker compose exec web pytest debates/tests/test_models.py -v

# Run specific test
docker compose exec web pytest debates/tests/test_models.py::TestDebateModel::test_debate_participant_names_ordering -v

# Run tests matching a pattern
docker compose exec web pytest -k "test_debate" -v

# Collect tests only (verify they can be discovered)
docker compose exec web pytest --collect-only
```

### Method 2: Local (Not Recommended)

Local execution requires a running PostgreSQL instance with the test database configured. This is more complex than using Docker.

## Test Configuration

**pytest.ini** - Main configuration file:
- Test discovery patterns: `test_*.py`, `*_tests.py`
- Coverage reporting: terminal, HTML, XML
- Test markers: `unit`, `integration`, `slow`, `celery`
- Strict configuration for reliability

**conftest.py** - Global fixtures:
- `django_db_setup` - Configures test database (uses 'db' host from Docker)
- `enable_db_access_for_all_tests` - Enables DB access by default
- `api_client` - DRF API client for testing endpoints
- `authenticated_client` - Pre-authenticated API client
- `test_user` - Sample user fixture
- `test_personas` - Sample personas (Socrates, Plato)
- `test_debate` - Sample debate fixture
- `mock_anthropic_response` - Mock for AI API responses

## Test Organization

```
backend/
├── debates/tests/
│   ├── __init__.py
│   ├── test_celery_integration.py   # 5 tests - Celery task execution
│   ├── test_models.py                # 49 tests - Debate & DebateMessage models
│   ├── test_performance.py           # 8 tests - Query optimization verification
│   ├── test_serializers.py           # 45 tests - API serializers
│   └── test_views.py                 # 11 tests - ViewSet endpoints
│
├── personas/tests/
│   ├── __init__.py
│   └── test_views.py                 # 12 tests - Persona API endpoints
│
├── users/tests/
│   ├── __init__.py
│   └── test_views.py                 # 14 tests - Authentication endpoints
│
└── payments/tests/
    ├── __init__.py
    └── test_webhooks.py              # 38 tests - Stripe webhooks
```

## Test Markers

Use markers to categorize and filter tests:

```bash
# Run only unit tests
docker compose exec web pytest -m unit

# Skip slow tests
docker compose exec web pytest -m "not slow"

# Run only integration tests
docker compose exec web pytest -m integration

# Run only Celery tests
docker compose exec web pytest -m celery
```

## Coverage Reports

```bash
# Generate HTML coverage report
docker compose exec web pytest --cov --cov-report=html

# View coverage in browser (from host)
open backend/htmlcov/index.html

# Generate terminal report with missing lines
docker compose exec web pytest --cov --cov-report=term-missing

# Generate XML report for CI/CD
docker compose exec web pytest --cov --cov-report=xml
```

## Common Issues & Solutions

### Issue: Tests can't find database

**Error**: `could not translate host name "db" to address`

**Solution**: Run tests inside Docker containers, not locally.

```bash
# ❌ Wrong - runs on host without DB access
pytest

# ✅ Correct - runs inside Docker with DB access
docker compose exec web pytest
```

### Issue: Test collection errors

**Error**: `import file mismatch` or duplicate test names

**Solution**: Ensure all test directories have `__init__.py` files.

```bash
# Verify all __init__.py files exist
ls -la */tests/__init__.py

# Should show:
# debates/tests/__init__.py
# personas/tests/__init__.py
# users/tests/__init__.py
# payments/tests/__init__.py
```

### Issue: Django app registry errors

**Error**: `Apps aren't loaded yet` or `No module named 'config'`

**Solution**: Use `pytest` instead of `python -m pytest`. The Django plugin needs to initialize properly.

```bash
# ❌ Wrong
docker compose exec web python -m pytest

# ✅ Correct
docker compose exec web pytest
```

### Issue: Cache conflicts

**Error**: Tests find wrong modules or fail unexpectedly

**Solution**: Clear Python cache and restart container.

```bash
# Clear cache
docker compose exec web find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
docker compose exec web find . -name "*.pyc" -delete

# Restart container
docker compose restart web
```

## Writing New Tests

### Example: Model Test

```python
# debates/tests/test_models.py
import pytest
from debates.models import Debate

@pytest.mark.unit
def test_debate_creation(test_user):
    """Test creating a debate."""
    debate = Debate.objects.create(
        topic="What is justice?",
        max_rounds=3,
        user=test_user
    )
    assert debate.status == "pending"
    assert debate.topic == "What is justice?"
```

### Example: API Test

```python
# debates/tests/test_views.py
import pytest
from rest_framework import status

@pytest.mark.integration
def test_list_debates(authenticated_client):
    """Test listing user's debates."""
    response = authenticated_client.get('/api/debates/')
    assert response.status_code == status.HTTP_200_OK
    assert 'results' in response.data
```

### Example: Celery Test

```python
# debates/tests/test_celery_integration.py
import pytest
from debates.tasks import generate_debate_task

@pytest.mark.celery
def test_debate_task_execution(test_debate):
    """Test Celery task executes."""
    result = generate_debate_task.delay(test_debate.id)
    assert result.successful()
```

## Best Practices

1. **Use fixtures**: Leverage `conftest.py` fixtures for common test data
2. **Mark tests**: Use `@pytest.mark.unit`, `@pytest.mark.integration`, etc.
3. **Test in Docker**: Always run tests in Docker for consistency
4. **Check coverage**: Aim for 60%+ coverage before production
5. **Mock external APIs**: Use `@patch` for Anthropic, Stripe, etc.
6. **Clean test data**: Tests should be isolated and not depend on order
7. **Descriptive names**: Use clear test names like `test_debate_creation_requires_user`

## CI/CD Integration

For automated testing in CI/CD pipelines:

```yaml
# .github/workflows/test.yml
name: Run Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          cd backend
          docker compose up -d db redis
          docker compose run web pytest --cov --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml
```

## Next Steps

1. Increase test coverage to 60%+:
   - Add view tests for authentication endpoints
   - Add view tests for payment webhooks
   - Add generator tests with mocked Anthropic API
   - Add citation extractor tests

2. Set up continuous integration:
   - Configure GitHub Actions for automated testing
   - Add coverage reporting to pull requests
   - Block merges if coverage decreases

3. Add integration tests:
   - End-to-end debate generation flow
   - Stripe subscription lifecycle
   - User authentication flow

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-django Documentation](https://pytest-django.readthedocs.io/)
- [Django REST Framework Testing](https://www.django-rest-framework.org/api-guide/testing/)
- [Celery Testing Documentation](https://docs.celeryproject.org/en/stable/userguide/testing.html)
