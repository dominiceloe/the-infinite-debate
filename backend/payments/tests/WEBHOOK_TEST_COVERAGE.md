# Webhook Test Coverage Analysis

## Test File
- **Location**: `/Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/backend/payments/tests/test_webhooks.py`
- **Lines**: 1050
- **Test Classes**: 10
- **Test Methods**: 38

## Coverage Target
- **Target File**: `backend/payments/views.py` (lines 139-371: StripeWebhookView)
- **Current Coverage**: 0%
- **Target Coverage**: 80%+

## Test Classes and Coverage

### 1. TestWebhookSignatureValidation (4 tests)
**Covers lines**: 146-172 (webhook validation and event logging)
- ✓ Valid signature processing
- ✓ Invalid payload (ValueError)
- ✓ Invalid signature (SignatureVerificationError)
- ✓ Duplicate event handling

**Lines covered**:
- 147-149: Signature header and secret retrieval
- 151-154: construct_event call
- 155-156: ValueError handling
- 157-158: SignatureVerificationError handling
- 161-167: Event creation/retrieval
- 169-171: Duplicate event check

### 2. TestCheckoutSessionCompleted (4 tests)
**Covers lines**: 199-218 (_handle_checkout_completed method)
- ✓ Checkout updates user with customer and tier
- ✓ Non-existent user handling
- ✓ Missing metadata handling
- ✓ User.DoesNotExist exception path

**Lines covered**:
- 200-203: Session data extraction
- 206-208: User lookup
- 209-215: User update with customer ID and tier
- 216-217: User.DoesNotExist exception

### 3. TestSubscriptionCreated (4 tests)
**Covers lines**: 219-256 (_handle_subscription_created method)
- ✓ Starter tier (30 credits allocation)
- ✓ Pro tier (100 credits allocation)
- ✓ Unknown price ID handling
- ✓ Credits reset date setting

**Lines covered**:
- 220-222: Subscription data extraction
- 225-227: User lookup by customer_id
- 228-236: Starter tier logic (price check, credits, tier)
- 237-238: Pro tier logic (price check, credits, tier)
- 239: Subscription status
- 240-241: Credits reset date calculation
- 243: User save
- 245-253: Subscription history creation
- 255-256: User.DoesNotExist exception

### 4. TestSubscriptionUpdated (5 tests)
**Covers lines**: 258-301 (_handle_subscription_updated method)
- ✓ Tier change (starter -> pro)
- ✓ Status change (active -> past_due)
- ✓ Canceled status handling
- ✓ No tier change (no history logged)
- ✓ Credit reset on tier change

**Lines covered**:
- 259-261: Subscription data extraction
- 264-265: User lookup
- 267-274: Status mapping
- 276-285: Tier detection and credit allocation
- 287: User save
- 289-298: History creation on tier change
- 300-301: User.DoesNotExist exception

### 5. TestSubscriptionDeleted (1 test)
**Covers lines**: 303-323 (_handle_subscription_deleted method)
- ✓ Subscription cancellation status update

**Lines covered**:
- 304-306: Subscription data extraction
- 309-310: User lookup
- 311-312: Status update to cancelled
- 314-320: History creation
- 322-323: User.DoesNotExist exception

### 6. TestPaymentSucceeded (2 tests)
**Covers lines**: 325-346 (_handle_payment_succeeded method)
- ✓ Payment record creation
- ✓ Missing payment_intent handling (uses invoice ID)

**Lines covered**:
- 326-328: Invoice data extraction
- 331-332: User lookup
- 334-343: Payment record creation with all fields
- 345-346: User.DoesNotExist exception

### 7. TestPaymentFailed (1 test)
**Covers lines**: 348-370 (_handle_payment_failed method)
- ✓ Failed payment status update and record creation

**Lines covered**:
- 349-351: Invoice data extraction
- 354-357: User lookup and status update
- 359-367: Failed payment record creation
- 369-370: User.DoesNotExist exception

### 8. TestWebhookErrorHandling (2 tests)
**Covers lines**: 174-196 (event handler routing and error logging)
- ✓ Processing error logging in StripeEvent
- ✓ Unknown event type handling

**Lines covered**:
- 174-186: Event type routing (all handler calls)
- 188-190: Processed flag update
- 192-195: Exception handling and error logging

### 9. TestCreditAllocation (4 tests)
**Covers lines**: 231-236, 280-285 (credit allocation logic)
- ✓ Starter tier = 30 credits
- ✓ Pro tier = 100 credits
- ✓ Upgrade resets credits
- ✓ Credits reset date set to +30 days

**Lines covered**:
- Reinforces coverage of subscription handlers
- Tests the actual credit values and reset logic

### 10. Integration Coverage
The tests also cover:
- Line 14: stripe.api_key setting (via imports)
- Lines 161-171: StripeEvent model interaction
- Model creation for StripePayment and StripeSubscriptionHistory

## Coverage Estimate

### Lines in StripeWebhookView (139-371): 233 lines total

**Covered Lines** (excluding blank/comment lines):
- Webhook main handler: ~30 lines (146-196)
- _handle_checkout_completed: ~17 lines (199-217)
- _handle_subscription_created: ~32 lines (219-256)
- _handle_subscription_updated: ~38 lines (258-301)
- _handle_subscription_deleted: ~17 lines (303-323)
- _handle_payment_succeeded: ~18 lines (325-346)
- _handle_payment_failed: ~18 lines (348-370)

**Total covered**: ~170 lines
**Estimated coverage**: **~85%** (170/200 executable lines)

## Not Covered
The tests do NOT cover:
- CreateCheckoutSessionView (lines 17-136) - separate functionality
- GetSubscriptionView (lines 373-403)
- CancelSubscriptionView (lines 406-437)
- PaymentHistoryView (lines 440-463)

These views require separate test files:
- `test_checkout.py` for checkout session creation
- `test_subscription_views.py` for get/cancel subscription
- `test_payment_history.py` for payment history

## Test Quality

### Strengths
1. ✓ Comprehensive mocking with @patch decorator
2. ✓ Tests all webhook event types
3. ✓ Tests both success and error paths
4. ✓ Tests edge cases (missing data, non-existent users)
5. ✓ Tests credit allocation logic thoroughly
6. ✓ Tests tier upgrades/downgrades
7. ✓ Tests database record creation (StripeEvent, StripePayment, StripeSubscriptionHistory)
8. ✓ Tests idempotency (duplicate events)

### Best Practices
- Uses pytest fixtures for reusable test data
- Follows pytest-django conventions
- Mocks external dependencies (Stripe API)
- Tests database state changes with .refresh_from_db()
- Clear test names describing what is being tested
- Organized into logical test classes
- Tests both positive and negative cases

## Running the Tests

```bash
# Run all webhook tests
pytest backend/payments/tests/test_webhooks.py -v

# Run with coverage
pytest backend/payments/tests/test_webhooks.py --cov=backend/payments/views --cov-report=term-missing

# Run specific test class
pytest backend/payments/tests/test_webhooks.py::TestSubscriptionCreated -v

# Run specific test
pytest backend/payments/tests/test_webhooks.py::TestSubscriptionCreated::test_subscription_created_starter_tier -v
```

## Next Steps

To achieve 100% coverage of `payments/views.py`, create these additional test files:

1. **test_checkout.py** - CreateCheckoutSessionView
   - Test checkout session creation
   - Test subscription upgrades/downgrades
   - Test Stripe customer creation
   - Test error handling

2. **test_subscription_views.py** - GetSubscriptionView, CancelSubscriptionView
   - Test getting subscription info
   - Test canceling subscriptions
   - Test error cases

3. **test_payment_history.py** - PaymentHistoryView
   - Test payment history retrieval
   - Test ordering and filtering
