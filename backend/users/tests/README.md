# Users App Tests

## Overview

This directory contains comprehensive tests for the `users` app, focusing on authentication endpoints and user management.

## Test Files

### test_authentication.py (PRIMARY)
**869 lines | 58 tests | 12 test classes**

Comprehensive test suite covering all authentication endpoints:
- User registration with trial subscription
- JWT login and token management
- Token refresh and logout
- User profile management
- Email verification
- Password reset flow
- Subscription status and credits
- User statistics
- Authorization and permissions

**Coverage Target:** 70%+ for `users/views.py`

### test_views.py (LEGACY)
**289 lines | 14 tests**

Basic tests for authentication endpoints. Kept for reference.

## Quick Start

### Run All Tests
```bash
# In Docker (recommended)
docker-compose exec backend pytest users/tests/ -v

# Local (if pytest installed)
cd backend
pytest users/tests/ -v
```

### Run Specific Test File
```bash
# Authentication tests only
docker-compose exec backend pytest users/tests/test_authentication.py -v

# Legacy tests only
docker-compose exec backend pytest users/tests/test_views.py -v
```

### Run Specific Test Class
```bash
# Test only registration
docker-compose exec backend pytest users/tests/test_authentication.py::TestRegisterView -v

# Test only login
docker-compose exec backend pytest users/tests/test_authentication.py::TestLoginView -v
```

### Run Specific Test Method
```bash
# Test single scenario
docker-compose exec backend pytest \
  users/tests/test_authentication.py::TestRegisterView::test_register_success -v
```

## Coverage Reports

### Generate Coverage Report
```bash
# Terminal report
docker-compose exec backend pytest users/tests/ \
  --cov=users \
  --cov-report=term-missing

# HTML report (opens in browser)
docker-compose exec backend pytest users/tests/ \
  --cov=users \
  --cov-report=html

# Then open htmlcov/index.html
```

### Target Coverage
```
users/views.py        → 70%+  (113 statements)
users/serializers.py  → 80%+  (87 statements)
users/models.py       → 85%+  (68 statements)
```

## Test Structure

### Fixtures Available
```python
api_client          # DRF APIClient for HTTP requests
trial_user          # User with active trial (15 credits, 7 days)
pro_user            # User with pro subscription (100 credits)
expired_trial_user  # User with expired trial
```

### Test Classes
1. `TestRegisterView` - User registration
2. `TestLoginView` - JWT login
3. `TestRefreshTokenView` - Token refresh
4. `TestLogoutView` - Token blacklisting
5. `TestUserProfileView` - Profile management
6. `TestEmailVerificationView` - Email verification
7. `TestPasswordResetRequestView` - Password reset request
8. `TestPasswordResetConfirmView` - Password reset confirm
9. `TestSubscriptionStatusView` - Subscription info
10. `TestUserStatsView` - User statistics
11. `TestAuthorizationAndPermissions` - JWT & permissions
12. `TestCreditBalanceAndTiers` - Credit & tier logic

## Common Test Patterns

### Testing Authenticated Endpoints
```python
def test_protected_endpoint(self, api_client, trial_user):
    api_client.force_authenticate(user=trial_user)
    response = api_client.get('/api/auth/profile/')
    assert response.status_code == 200
```

### Testing JWT Authentication
```python
def test_jwt_auth(self, api_client, trial_user):
    from rest_framework_simplejwt.tokens import RefreshToken

    refresh = RefreshToken.for_user(trial_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    response = api_client.get('/api/auth/profile/')
    assert response.status_code == 200
```

### Testing Validation Errors
```python
def test_invalid_data(self, api_client):
    data = {'username': 'test'}  # Missing required fields
    response = api_client.post('/api/auth/register/', data)
    assert response.status_code == 400
    assert 'email' in str(response.data)
```

## Debugging Tests

### Run with Verbose Output
```bash
docker-compose exec backend pytest users/tests/ -vv
```

### Run with Print Statements
```bash
docker-compose exec backend pytest users/tests/ -s
```

### Run Failed Tests Only
```bash
docker-compose exec backend pytest users/tests/ --lf
```

### Run with Debugging
```bash
docker-compose exec backend pytest users/tests/ --pdb
```

## Best Practices

### DO ✅
- Use fixtures for setup
- Test happy path + error cases
- Use descriptive test names
- Verify database state with `.refresh_from_db()`
- Test authorization requirements
- Use status code constants (`status.HTTP_200_OK`)

### DON'T ❌
- Don't create test data in test methods (use fixtures)
- Don't test Django/DRF internals
- Don't skip authentication tests
- Don't use hardcoded status codes (use constants)
- Don't forget to test edge cases

## Documentation

- **TEST_COVERAGE.md** - Detailed coverage mapping
- **IMPLEMENTATION_REPORT.md** - Full implementation details
- **README.md** - This file

## Troubleshooting

### Tests fail with database errors
```bash
# Recreate test database
docker-compose exec backend python manage.py migrate
docker-compose exec backend pytest users/tests/ --create-db
```

### Import errors
```bash
# Ensure backend container is running
docker-compose up -d backend

# Rebuild if needed
docker-compose build backend
```

### Fixture not found
```bash
# Check conftest.py is present
ls backend/conftest.py
ls backend/users/tests/__init__.py
```

## Contributing

When adding new tests:

1. Follow existing naming conventions
2. Use appropriate fixtures
3. Add docstrings to test methods
4. Test both success and failure cases
5. Update TEST_COVERAGE.md
6. Run full test suite before committing

## Contact

For questions about these tests, see:
- Main project documentation
- Django REST Framework testing docs
- pytest-django documentation
