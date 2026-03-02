# Plan: Fix deprecated stripe.error exception references for SDK v13

**Type:** fix
**Complexity:** SMALL
**Scope:** backend

## Problem

The project uses `stripe==13.0.1` (from `backend/requirements.txt`), but the codebase
references exceptions via the deprecated `stripe.error` submodule (e.g.,
`stripe.error.SignatureVerificationError`, `stripe.error.StripeError`). In Stripe Python
SDK v6+, these exception classes were moved to the top-level `stripe` namespace. The
`stripe.error` attribute no longer exists in v13, causing `AttributeError` at runtime.

A production Sentry alert confirms that the webhook endpoint crashes when Stripe sends
a request with an invalid signature, because the `except stripe.error.SignatureVerificationError`
clause itself raises `AttributeError` before it can handle the verification failure.

## Solution

Replace all `stripe.error.X` references with `stripe.X` across production code and tests.
This is a mechanical 1:1 substitution -- no logic changes, no new imports, no behavioral
differences. The test mock path must also be updated so the mock patches the correct
attribute on the stripe module.

## Files

| File | Change | Lines |
|------|--------|-------|
| `backend/payments/views.py` | `stripe.error.StripeError` -> `stripe.StripeError` (line 153) | ~1 |
| `backend/payments/views.py` | `stripe.error.SignatureVerificationError` -> `stripe.SignatureVerificationError` (line 222) | ~1 |
| `backend/payments/tests/test_webhooks.py` | `mock_stripe.error.SignatureVerificationError` -> `mock_stripe.SignatureVerificationError` (line 227) | ~1 |

**Total:** ~3 lines changed across 2 files

## Implementation

### File 1: `backend/payments/views.py`

- [ ] Line 153: Change `except stripe.error.StripeError as e:` to `except stripe.StripeError as e:`
  - Context: `CreateCheckoutSessionView.post()` -- catches errors when retrieving an
    existing subscription during upgrade/downgrade flow
- [ ] Line 222: Change `except stripe.error.SignatureVerificationError:` to `except stripe.SignatureVerificationError:`
  - Context: `StripeWebhookView.post()` -- catches invalid webhook signatures from
    `stripe.Webhook.construct_event()`

### File 2: `backend/payments/tests/test_webhooks.py`

- [ ] Line 227: Change `mock_stripe.error.SignatureVerificationError = SignatureVerificationError`
  to `mock_stripe.SignatureVerificationError = SignatureVerificationError`
  - Context: `TestWebhookSignatureValidation.test_invalid_signature()` -- the test
    patches `payments.views.stripe` with a MagicMock and must assign the custom
    exception class to the correct attribute so the except clause matches

## Tests

- [ ] Existing test `test_invalid_signature` covers the SignatureVerificationError path
  (must pass after both views.py and test file are updated together)
- [ ] Existing test `test_valid_signature` ensures normal webhook processing still works
- [ ] No new tests required -- this is a namespace fix, not a logic change

## Verification

```bash
# Run the webhook test suite to confirm all 3 changes are consistent
docker compose exec web pytest payments/tests/test_webhooks.py -v

# Full payments test suite
docker compose exec web pytest payments/ -v
```

## Risks

1. **Risk:** Partial application (updating views.py but not the test, or vice versa)
   **Mitigation:** All 3 changes must be applied atomically in a single commit. The
   test_invalid_signature test will fail if views.py and test file are out of sync.

**Estimated:** 10-15 minutes

---

**Status:** Ready for approval
