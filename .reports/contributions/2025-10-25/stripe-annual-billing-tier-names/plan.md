# Implementation Plan: Stripe Annual Billing & Tier Names

**Date:** 2025-10-25
**Type:** refactor
**Estimated Effort:** Medium (3-4 hours)

---

## Summary

This refactoring updates the Stripe integration to:
1. Support both monthly and annual billing periods
2. Rename subscription tiers from "student/scholar" to "starter/pro" (user-facing names already use starter/pro, but internal code and Stripe variables use old names)
3. Update all environment variables, settings, and webhook handlers to use 4 price IDs (2 tiers × 2 billing periods)
4. Remove legacy price ID configuration entirely (no backwards compatibility needed - app not live yet)

**New Stripe Price IDs:**
- Starter Monthly: `price_1SMJdgBOpZCPz6T21xV5B1Vj`
- Starter Annual: `price_1SMJegBOpZCPz6T2ufUMeKOM`
- Pro Monthly: `price_1SMJgGBOpZCPz6T2Y2UhEN9U`
- Pro Annual: `price_1SMJh8BOpZCPz6T2Mjm28HFC`

---

## Affected Files

### Backend Modified (4 files)
- `backend/config/settings.py` (lines 309-314)
- `backend/payments/views.py` (lines 68-71, 272-277, 321-326)
- `backend/.env.example` (lines 55-57)
- `backend/.env.docker` (lines 29-30)

### Frontend Modified (2 files)
- `frontend/app/pricing/page.tsx` (lines 206-210, 413-425, 509, 642, 658)
- `frontend/lib/api.ts` (lines 173-189)

### Backend Test Files (2 files)
- `backend/payments/tests/test_views.py` - Update to test annual billing
- `backend/payments/tests/test_webhooks.py` - Add tests for 4 price IDs

### Frontend Test Files (1 file)
- `frontend/__tests__/lib/api.test.ts` - Add tests for billing_period parameter

---

## Implementation Steps

### Step 1: Update Environment Variables

**File:** `backend/config/settings.py`

**Remove (lines 313-314):**
```python
STRIPE_STUDENT_PRICE_ID = os.getenv('STRIPE_STUDENT_PRICE_ID', '')
STRIPE_SCHOLAR_PRICE_ID = os.getenv('STRIPE_SCHOLAR_PRICE_ID', '')
```

**Add (replace above lines):**
```python
# Stripe Price IDs - Starter Tier (30 credits/month, $10/mo or $96/yr)
STRIPE_STARTER_MONTHLY_PRICE_ID = os.getenv('STRIPE_STARTER_MONTHLY_PRICE_ID', '')
STRIPE_STARTER_YEARLY_PRICE_ID = os.getenv('STRIPE_STARTER_YEARLY_PRICE_ID', '')

# Stripe Price IDs - Pro Tier (100 credits/month, $25/mo or $240/yr)
STRIPE_PRO_MONTHLY_PRICE_ID = os.getenv('STRIPE_PRO_MONTHLY_PRICE_ID', '')
STRIPE_PRO_YEARLY_PRICE_ID = os.getenv('STRIPE_PRO_YEARLY_PRICE_ID', '')
```

---

**File:** `backend/.env.example`

**Update (lines 55-57):**
```bash
# Stripe Price IDs (get from Stripe Dashboard)
# Starter Tier (30 credits/month)
STRIPE_STARTER_MONTHLY_PRICE_ID=price_your_starter_monthly_price_id
STRIPE_STARTER_YEARLY_PRICE_ID=price_your_starter_yearly_price_id

# Pro Tier (100 credits/month)
STRIPE_PRO_MONTHLY_PRICE_ID=price_your_pro_monthly_price_id
STRIPE_PRO_YEARLY_PRICE_ID=price_your_pro_yearly_price_id
```

---

**File:** `backend/.env.docker`

**Update (lines 29-30):**
```bash
# Stripe Configuration
STRIPE_SECRET_KEY=***STRIPE_SECRET_REMOVED***
STRIPE_PUBLISHABLE_KEY=***STRIPE_PUBKEY_REMOVED***
STRIPE_WEBHOOK_SECRET=***STRIPE_WEBHOOK_REMOVED***

# Starter Tier Price IDs
STRIPE_STARTER_MONTHLY_PRICE_ID=price_1SMJdgBOpZCPz6T21xV5B1Vj
STRIPE_STARTER_YEARLY_PRICE_ID=price_1SMJegBOpZCPz6T2ufUMeKOM

# Pro Tier Price IDs
STRIPE_PRO_MONTHLY_PRICE_ID=price_1SMJgGBOpZCPz6T2Y2UhEN9U
STRIPE_PRO_YEARLY_PRICE_ID=price_1SMJh8BOpZCPz6T2Mjm28HFC
```

---

### Step 2: Update CreateCheckoutSessionView

**File:** `backend/payments/views.py`

**Changes:**

1. **Update API Schema (lines 27-43)** - Add `billing_period` field:
```python
request={
    "type": "object",
    "properties": {
        "tier": {
            "type": "string",
            "enum": ["starter", "pro"],
            "description": "Subscription tier to purchase"
        },
        "billing_period": {
            "type": "string",
            "enum": ["monthly", "yearly"],
            "default": "monthly",
            "description": "Billing frequency (monthly or yearly)"
        },
        "success_url": {
            "type": "string",
            "description": "URL to redirect after successful payment"
        },
        "cancel_url": {
            "type": "string",
            "description": "URL to redirect if payment is cancelled"
        }
    },
    "required": ["tier"]
}
```

2. **Update post() method (lines 63-76)** - Extract `billing_period` and build dynamic price mapping:
```python
def post(self, request):
    user = request.user
    tier = request.data.get('tier')  # 'starter' or 'pro'
    billing_period = request.data.get('billing_period', 'monthly')  # 'monthly' or 'yearly'

    # Validate inputs
    if tier not in ['starter', 'pro']:
        return Response(
            {'error': 'Invalid subscription tier. Must be "starter" or "pro".'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if billing_period not in ['monthly', 'yearly']:
        return Response(
            {'error': 'Invalid billing period. Must be "monthly" or "yearly".'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Map tier + billing_period to Stripe price ID
    price_mapping = {
        ('starter', 'monthly'): settings.STRIPE_STARTER_MONTHLY_PRICE_ID,
        ('starter', 'yearly'): settings.STRIPE_STARTER_YEARLY_PRICE_ID,
        ('pro', 'monthly'): settings.STRIPE_PRO_MONTHLY_PRICE_ID,
        ('pro', 'yearly'): settings.STRIPE_PRO_YEARLY_PRICE_ID,
    }

    price_id = price_mapping.get((tier, billing_period))
    if not price_id:
        return Response(
            {'error': f'No Stripe price configured for {tier} {billing_period}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
```

3. **Update checkout session metadata (line 160-163)** - Include billing_period:
```python
metadata={
    'user_id': user.id,
    'tier': tier,
    'billing_period': billing_period,
}
```

4. **Update subscription upgrade logic (lines 94-96)** - Use new price_id variable:
```python
updated_subscription = stripe.Subscription.modify(
    user.stripe_subscription_id,
    items=[{
        'id': subscription_item_id,
        'price': price_id,  # Use dynamically selected price_id
    }],
    proration_behavior='create_prorations',
)
```

---

### Step 3: Update Webhook Handlers

**File:** `backend/payments/views.py`

**Changes:**

1. **Update `_handle_subscription_created()` (lines 260-297)** - Support 4 price IDs:
```python
def _handle_subscription_created(self, event):
    """Handle new subscription creation."""
    subscription = event['data']['object']
    customer_id = subscription['customer']

    from users.models import User
    try:
        user = User.objects.get(stripe_customer_id=customer_id)
        user.stripe_subscription_id = subscription['id']

        # Determine tier from price ID
        price_id = subscription['items']['data'][0]['price']['id']

        if price_id in [
            settings.STRIPE_STARTER_MONTHLY_PRICE_ID,
            settings.STRIPE_STARTER_YEARLY_PRICE_ID,
        ]:
            user.subscription_tier = 'starter'
            user.credits_remaining = 30
        elif price_id in [
            settings.STRIPE_PRO_MONTHLY_PRICE_ID,
            settings.STRIPE_PRO_YEARLY_PRICE_ID,
        ]:
            user.subscription_tier = 'pro'
            user.credits_remaining = 100

        user.subscription_status = 'active'

        # Set credits reset date to next month
        user.credits_reset_date = timezone.now().date() + timedelta(days=30)

        user.save()

        # Log subscription history
        StripeSubscriptionHistory.objects.create(
            user=user,
            subscription_id=subscription['id'],
            action='created',
            tier=user.subscription_tier,
            status='active',
            metadata={'price_id': price_id}
        )

    except User.DoesNotExist:
        pass
```

2. **Update `_handle_subscription_updated()` (lines 299-342)** - Same 4-price-ID logic:
```python
def _handle_subscription_updated(self, event):
    """Handle subscription updates (e.g., plan changes)."""
    subscription = event['data']['object']
    customer_id = subscription['customer']

    from users.models import User
    try:
        user = User.objects.get(stripe_customer_id=customer_id)

        # Update subscription status
        status_mapping = {
            'active': 'active',
            'past_due': 'past_due',
            'canceled': 'cancelled',
            'unpaid': 'past_due',
        }
        user.subscription_status = status_mapping.get(subscription['status'], 'active')

        # Check if plan changed
        price_id = subscription['items']['data'][0]['price']['id']
        old_tier = user.subscription_tier

        if price_id in [
            settings.STRIPE_STARTER_MONTHLY_PRICE_ID,
            settings.STRIPE_STARTER_YEARLY_PRICE_ID,
        ]:
            user.subscription_tier = 'starter'
            user.credits_remaining = 30
        elif price_id in [
            settings.STRIPE_PRO_MONTHLY_PRICE_ID,
            settings.STRIPE_PRO_YEARLY_PRICE_ID,
        ]:
            user.subscription_tier = 'pro'
            user.credits_remaining = 100

        user.save()

        # Log if tier changed
        if old_tier != user.subscription_tier:
            StripeSubscriptionHistory.objects.create(
                user=user,
                subscription_id=subscription['id'],
                action='updated',
                tier=user.subscription_tier,
                status=user.subscription_status,
                metadata={'old_tier': old_tier, 'new_tier': user.subscription_tier}
            )

    except User.DoesNotExist:
        pass
```

---

### Step 4: Update Tests

**File:** `backend/payments/tests/test_views.py`

**Add new test cases:**

```python
@pytest.mark.django_db
class TestCreateCheckoutSessionAnnualBilling:
    """Test checkout session creation with annual billing."""

    @patch('stripe.checkout.Session.create')
    def test_create_checkout_starter_yearly(
        self, mock_session_create, authenticated_client, test_user
    ):
        """Test creating checkout session for starter yearly subscription."""
        test_user.stripe_customer_id = 'cus_test'
        test_user.save()

        mock_session_create.return_value = MagicMock(
            url='https://checkout.stripe.com/yearly',
            id='cs_yearly'
        )

        response = authenticated_client.post('/api/payments/create-checkout/', {
            'tier': 'starter',
            'billing_period': 'yearly'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_upgrade'] is False

        # Verify correct price ID used
        session_kwargs = mock_session_create.call_args[1]
        assert session_kwargs['line_items'][0]['price'] == settings.STRIPE_STARTER_YEARLY_PRICE_ID
        assert session_kwargs['metadata']['billing_period'] == 'yearly'

    @patch('stripe.checkout.Session.create')
    def test_create_checkout_pro_yearly(
        self, mock_session_create, authenticated_client, test_user
    ):
        """Test creating checkout session for pro yearly subscription."""
        test_user.stripe_customer_id = 'cus_test'
        test_user.save()

        mock_session_create.return_value = MagicMock(
            url='https://checkout.stripe.com/pro_yearly',
            id='cs_pro_yearly'
        )

        response = authenticated_client.post('/api/payments/create-checkout/', {
            'tier': 'pro',
            'billing_period': 'yearly'
        })

        assert response.status_code == status.HTTP_200_OK
        session_kwargs = mock_session_create.call_args[1]
        assert session_kwargs['line_items'][0]['price'] == settings.STRIPE_PRO_YEARLY_PRICE_ID

    def test_invalid_billing_period_returns_400(self, authenticated_client):
        """Test that invalid billing period returns 400 error."""
        response = authenticated_client.post('/api/payments/create-checkout/', {
            'tier': 'starter',
            'billing_period': 'invalid'
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Invalid billing period' in response.data['error']

    @patch('stripe.checkout.Session.create')
    def test_billing_period_defaults_to_monthly(
        self, mock_session_create, authenticated_client, test_user
    ):
        """Test that billing_period defaults to monthly if not provided."""
        test_user.stripe_customer_id = 'cus_test'
        test_user.save()

        mock_session_create.return_value = MagicMock(
            url='https://checkout.stripe.com/default',
            id='cs_default'
        )

        response = authenticated_client.post('/api/payments/create-checkout/', {
            'tier': 'starter'
            # No billing_period provided
        })

        assert response.status_code == status.HTTP_200_OK
        session_kwargs = mock_session_create.call_args[1]
        assert session_kwargs['line_items'][0]['price'] == settings.STRIPE_STARTER_MONTHLY_PRICE_ID
        assert session_kwargs['metadata']['billing_period'] == 'monthly'

    @patch('stripe.Subscription.modify')
    @patch('stripe.Subscription.retrieve')
    def test_upgrade_from_monthly_to_yearly(
        self, mock_retrieve, mock_modify, authenticated_client_starter, test_user_starter
    ):
        """Test upgrading from monthly to yearly billing."""
        mock_retrieve.return_value = {
            'status': 'active',
            'items': {'data': [{'id': 'si_item123'}]}
        }
        mock_modify.return_value = MagicMock()

        response = authenticated_client_starter.post('/api/payments/create-checkout/', {
            'tier': 'starter',
            'billing_period': 'yearly'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_upgrade'] is True

        # Verify subscription modified to yearly price
        modify_kwargs = mock_modify.call_args[1]
        assert modify_kwargs['items'][0]['price'] == settings.STRIPE_STARTER_YEARLY_PRICE_ID
```

---

**File:** `backend/payments/tests/test_webhooks.py`

**Add new test cases:**

```python
@pytest.mark.django_db
class TestWebhooksWithAnnualBilling:
    """Test webhook handlers recognize all 4 price IDs."""

    @patch('stripe.Webhook.construct_event')
    def test_subscription_created_starter_yearly(
        self, mock_construct_event, webhook_client, test_user_with_stripe
    ):
        """Test subscription creation with starter yearly price ID."""
        event = {
            'id': 'evt_starter_yearly',
            'type': 'customer.subscription.created',
            'data': {
                'object': {
                    'id': 'sub_starter_yearly',
                    'customer': test_user_with_stripe.stripe_customer_id,
                    'status': 'active',
                    'items': {
                        'data': [{
                            'price': {
                                'id': settings.STRIPE_STARTER_YEARLY_PRICE_ID
                            }
                        }]
                    }
                }
            }
        }
        mock_construct_event.return_value = event

        response = webhook_client.post(
            '/api/payments/webhook/',
            data=json.dumps({'test': 'data'}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )

        assert response.status_code == status.HTTP_200_OK

        test_user_with_stripe.refresh_from_db()
        assert test_user_with_stripe.subscription_tier == 'starter'
        assert test_user_with_stripe.credits_remaining == 30

    @patch('stripe.Webhook.construct_event')
    def test_subscription_created_pro_yearly(
        self, mock_construct_event, webhook_client, test_user_with_stripe
    ):
        """Test subscription creation with pro yearly price ID."""
        event = {
            'id': 'evt_pro_yearly',
            'type': 'customer.subscription.created',
            'data': {
                'object': {
                    'id': 'sub_pro_yearly',
                    'customer': test_user_with_stripe.stripe_customer_id,
                    'status': 'active',
                    'items': {
                        'data': [{
                            'price': {
                                'id': settings.STRIPE_PRO_YEARLY_PRICE_ID
                            }
                        }]
                    }
                }
            }
        }
        mock_construct_event.return_value = event

        response = webhook_client.post(
            '/api/payments/webhook/',
            data=json.dumps({'test': 'data'}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )

        assert response.status_code == status.HTTP_200_OK

        test_user_with_stripe.refresh_from_db()
        assert test_user_with_stripe.subscription_tier == 'pro'
        assert test_user_with_stripe.credits_remaining == 100

    @patch('stripe.Webhook.construct_event')
    def test_subscription_created_starter_monthly(
        self, mock_construct_event, webhook_client, test_user_with_stripe
    ):
        """Test subscription creation with starter monthly price ID."""
        event = {
            'id': 'evt_starter_monthly',
            'type': 'customer.subscription.created',
            'data': {
                'object': {
                    'id': 'sub_starter_monthly',
                    'customer': test_user_with_stripe.stripe_customer_id,
                    'status': 'active',
                    'items': {
                        'data': [{
                            'price': {
                                'id': settings.STRIPE_STARTER_MONTHLY_PRICE_ID
                            }
                        }]
                    }
                }
            }
        }
        mock_construct_event.return_value = event

        response = webhook_client.post(
            '/api/payments/webhook/',
            data=json.dumps({'test': 'data'}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )

        assert response.status_code == status.HTTP_200_OK

        test_user_with_stripe.refresh_from_db()
        assert test_user_with_stripe.subscription_tier == 'starter'
        assert test_user_with_stripe.credits_remaining == 30

    @patch('stripe.Webhook.construct_event')
    def test_subscription_created_pro_monthly(
        self, mock_construct_event, webhook_client, test_user_with_stripe
    ):
        """Test subscription creation with pro monthly price ID."""
        event = {
            'id': 'evt_pro_monthly',
            'type': 'customer.subscription.created',
            'data': {
                'object': {
                    'id': 'sub_pro_monthly',
                    'customer': test_user_with_stripe.stripe_customer_id,
                    'status': 'active',
                    'items': {
                        'data': [{
                            'price': {
                                'id': settings.STRIPE_PRO_MONTHLY_PRICE_ID
                            }
                        }]
                    }
                }
            }
        }
        mock_construct_event.return_value = event

        response = webhook_client.post(
            '/api/payments/webhook/',
            data=json.dumps({'test': 'data'}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )

        assert response.status_code == status.HTTP_200_OK

        test_user_with_stripe.refresh_from_db()
        assert test_user_with_stripe.subscription_tier == 'pro'
        assert test_user_with_stripe.credits_remaining == 100
```

---

### Step 5: Update Frontend - API Client

**File:** `frontend/lib/api.ts`

**Current Code (lines 173-189):**
```typescript
createCheckout: async (data: { tier: 'starter' | 'pro'; success_url: string; cancel_url: string }): Promise<{
  checkout_url?: string;
  session_id?: string;
  is_upgrade?: boolean;
  message?: string;
  tier?: string;
  old_tier?: string;
}> => {
  const response = await api.post<{
    checkout_url?: string;
    session_id?: string;
    is_upgrade?: boolean;
    message?: string;
    tier?: string;
    old_tier?: string;
  }>('/payments/create-checkout/', data);
  return response.data;
},
```

**Updated Code:**
```typescript
createCheckout: async (data: {
  tier: 'starter' | 'pro';
  billing_period?: 'monthly' | 'yearly';  // NEW: optional billing period
  success_url: string;
  cancel_url: string;
}): Promise<{
  checkout_url?: string;
  session_id?: string;
  is_upgrade?: boolean;
  message?: string;
  tier?: string;
  old_tier?: string;
}> => {
  const response = await api.post<{
    checkout_url?: string;
    session_id?: string;
    is_upgrade?: boolean;
    message?: string;
    tier?: string;
    old_tier?: string;
  }>('/payments/create-checkout/', data);
  return response.data;
},
```

**Changes:**
- Add `billing_period?: 'monthly' | 'yearly'` to request data type
- Make it optional to maintain backwards compatibility
- No changes to response type (backend response unchanged)

---

### Step 6: Update Frontend - Pricing Page

**File:** `frontend/app/pricing/page.tsx`

The pricing page already has the billing period toggle UI implemented (lines 37, 129, 186-190, 286-319), but it's not connected to the API yet.

**Change 1: Pass billing_period to API (lines 206-210)**

**Current Code:**
```typescript
const response = await apiClient.payments.createCheckout({
  tier,
  success_url: `${window.location.origin}/account?payment=success`,
  cancel_url: `${window.location.origin}/pricing?payment=cancelled`,
});
```

**Updated Code:**
```typescript
const response = await apiClient.payments.createCheckout({
  tier,
  billing_period: billingPeriod,  // NEW: pass current billing period selection
  success_url: `${window.location.origin}/account?payment=success`,
  cancel_url: `${window.location.origin}/pricing?payment=cancelled`,
});
```

**Change 2: Update pricing display calculations (lines 413-425)**

**Current Code:**
```typescript
<Box sx={{ display: 'flex', alignItems: 'baseline', gap: 0.5 }}>
  <Typography variant="h3" sx={{ fontWeight: 700 }}>
    ${billingPeriod === 'monthly' ? tierTemplate.monthlyPrice : tierTemplate.annualPrice}
  </Typography>
  <Typography variant="body2" color="text.secondary">
    /{billingPeriod === 'monthly' ? 'month' : 'year'}
  </Typography>
</Box>
{billingPeriod === 'annual' && (
  <Typography variant="caption" color="text.secondary">
    ${(tierTemplate.annualPrice / 12).toFixed(2)}/month billed annually
  </Typography>
)}
```

**No changes needed** - This is already correctly implemented! The UI already:
- Shows monthly price when `billingPeriod === 'monthly'`
- Shows annual price when `billingPeriod === 'annual'`
- Displays per-month calculation for annual billing

**Change 3: Update subscription button text (line 509)**

**Current Code:**
```typescript
`Subscribe for $${billingPeriod === 'monthly' ? tierTemplate.monthlyPrice : tierTemplate.annualPrice}`
```

**No changes needed** - Already correctly shows price based on billing period!

**Change 4: Update confirmation dialog pricing (lines 642, 658)**

**Current Code (line 642):**
```typescript
{currentTierDetails?.name || currentTier} - ${billingPeriod === 'monthly' ? currentTierDetails?.monthlyPrice : currentTierDetails?.annualPrice}/mo
```

**Update to:**
```typescript
{currentTierDetails?.name || currentTier} - ${billingPeriod === 'monthly' ? currentTierDetails?.monthlyPrice : currentTierDetails?.annualPrice}/{billingPeriod === 'monthly' ? 'mo' : 'yr'}
```

**Current Code (line 658):**
```typescript
{newTierDetails?.name} - ${billingPeriod === 'monthly' ? newTierDetails?.monthlyPrice : newTierDetails?.annualPrice}/mo
```

**Update to:**
```typescript
{newTierDetails?.name} - ${billingPeriod === 'monthly' ? newTierDetails?.monthlyPrice : newTierDetails?.annualPrice}/{billingPeriod === 'monthly' ? 'mo' : 'yr'}
```

**Analysis:**
- The pricing page already has a complete UI for billing period selection
- The `billingPeriod` state variable is already defined and managed
- The toggle between Monthly/Annual is already implemented
- The "Save up to 25%" badge is already shown for annual billing
- The only missing piece is passing `billingPeriod` to the API call

**Summary of Required Changes:**
1. Update API client type definition (1 line change)
2. Pass `billingPeriod` to API call (1 line change)
3. Fix confirmation dialog price labels to show '/yr' for annual (2 line changes)

---

### Step 7: Frontend Tests

**File:** `frontend/__tests__/lib/api.test.ts`

**Add new test cases:**

```typescript
describe('apiClient.payments.createCheckout', () => {
  it('should create checkout with monthly billing by default', async () => {
    const mockResponse = {
      checkout_url: 'https://checkout.stripe.com/session_123',
      session_id: 'cs_test_123',
      is_upgrade: false,
    };

    mock.onPost('/payments/create-checkout/').reply(200, mockResponse);

    const result = await apiClient.payments.createCheckout({
      tier: 'starter',
      success_url: 'https://example.com/success',
      cancel_url: 'https://example.com/cancel',
    });

    expect(result).toEqual(mockResponse);
    expect(mock.history.post[0].data).toContain('"tier":"starter"');
    // billing_period not sent = defaults to monthly on backend
  });

  it('should create checkout with yearly billing when specified', async () => {
    const mockResponse = {
      checkout_url: 'https://checkout.stripe.com/session_yearly',
      session_id: 'cs_test_yearly',
      is_upgrade: false,
    };

    mock.onPost('/payments/create-checkout/').reply(200, mockResponse);

    const result = await apiClient.payments.createCheckout({
      tier: 'pro',
      billing_period: 'yearly',
      success_url: 'https://example.com/success',
      cancel_url: 'https://example.com/cancel',
    });

    expect(result).toEqual(mockResponse);

    const requestData = JSON.parse(mock.history.post[0].data);
    expect(requestData.tier).toBe('pro');
    expect(requestData.billing_period).toBe('yearly');
  });

  it('should create checkout with monthly billing when explicitly specified', async () => {
    const mockResponse = {
      checkout_url: 'https://checkout.stripe.com/session_monthly',
      session_id: 'cs_test_monthly',
      is_upgrade: false,
    };

    mock.onPost('/payments/create-checkout/').reply(200, mockResponse);

    const result = await apiClient.payments.createCheckout({
      tier: 'starter',
      billing_period: 'monthly',
      success_url: 'https://example.com/success',
      cancel_url: 'https://example.com/cancel',
    });

    expect(result).toEqual(mockResponse);

    const requestData = JSON.parse(mock.history.post[0].data);
    expect(requestData.billing_period).toBe('monthly');
  });

  it('should handle upgrade with billing period change', async () => {
    const mockResponse = {
      is_upgrade: true,
      message: 'Subscription updated successfully',
      tier: 'starter',
      old_tier: 'starter',
    };

    mock.onPost('/payments/create-checkout/').reply(200, mockResponse);

    const result = await apiClient.payments.createCheckout({
      tier: 'starter',
      billing_period: 'yearly', // Switching from monthly to yearly
      success_url: 'https://example.com/success',
      cancel_url: 'https://example.com/cancel',
    });

    expect(result.is_upgrade).toBe(true);
  });
});
```

---

## Testing Checklist

### Unit Tests (Backend)
- [ ] Test checkout session creation with `billing_period='monthly'`
- [ ] Test checkout session creation with `billing_period='yearly'`
- [ ] Test invalid `billing_period` returns 400 error
- [ ] Test `billing_period` defaults to 'monthly' if not provided
- [ ] Test upgrade from monthly to yearly billing (same tier)
- [ ] Test webhook recognizes `STRIPE_STARTER_MONTHLY_PRICE_ID`
- [ ] Test webhook recognizes `STRIPE_STARTER_YEARLY_PRICE_ID`
- [ ] Test webhook recognizes `STRIPE_PRO_MONTHLY_PRICE_ID`
- [ ] Test webhook recognizes `STRIPE_PRO_YEARLY_PRICE_ID`
- [ ] Test subscription.updated webhook handles tier changes correctly
- [ ] Test credits allocated correctly for all 4 price IDs

### Unit Tests (Frontend)
- [ ] Test API client sends `billing_period='monthly'` when specified
- [ ] Test API client sends `billing_period='yearly'` when specified
- [ ] Test API client defaults to monthly when `billing_period` not provided
- [ ] Test API client handles upgrade responses with billing period changes

### Manual Testing (Backend)
- [ ] Create starter monthly subscription via Stripe checkout
- [ ] Create starter yearly subscription via Stripe checkout
- [ ] Create pro monthly subscription via Stripe checkout
- [ ] Create pro yearly subscription via Stripe checkout
- [ ] Upgrade from starter monthly to starter yearly
- [ ] Upgrade from starter to pro (monthly)
- [ ] Verify webhooks fire correctly for all subscription events

### Manual Testing (Frontend)
- [ ] Toggle between Monthly/Annual on pricing page
- [ ] Verify prices update correctly when toggling billing period
- [ ] Verify "Save up to 25%" badge shows for annual billing
- [ ] Click "Subscribe" button with Monthly selected → redirects to Stripe checkout
- [ ] Click "Subscribe" button with Annual selected → redirects to Stripe checkout
- [ ] Verify Stripe checkout session shows correct price (monthly vs annual)
- [ ] Complete monthly subscription → verify credits allocated
- [ ] Complete annual subscription → verify credits allocated
- [ ] In confirmation dialog, verify price labels show "/mo" for monthly and "/yr" for annual
- [ ] Test upgrade from monthly to yearly billing via pricing page
- [ ] Test downgrade from yearly to monthly billing (if supported)

---

## Risks & Mitigations

### Risk 1: Missing Price ID Configuration
**Impact:** New subscriptions fail if environment variables not set
**Mitigation:**
- Add validation in settings.py to warn if price IDs are missing
- Update deployment checklist to verify all 4 price IDs are configured
- Add health check endpoint that verifies Stripe configuration

### Risk 2: Webhook Fails to Recognize New Price IDs
**Impact:** Users pay but don't get credits/tier assigned
**Mitigation:**
- Add comprehensive logging in webhook handlers for unknown price IDs
- Add Sentry alerts for unrecognized price IDs
- Test all 4 price IDs in staging before production deploy
- Monitor StripeEvent model for `processed=True` but missing tier assignment

### Risk 3: Frontend Still Sends Old API Format
**Impact:** Frontend doesn't send `billing_period` parameter
**Mitigation:**
- Make `billing_period` optional with default value 'monthly'
- Frontend PR must update CreateCheckoutSessionView API call
- Backwards compatible: old frontend code will default to monthly

### Risk 4: Existing Tests Break Due to Old Price ID References
**Impact:** CI/CD pipeline fails
**Mitigation:**
- Update all test fixtures to use `settings.STRIPE_STARTER_MONTHLY_PRICE_ID` instead of old references
- Run full test suite locally before commit
- Update conftest.py fixtures if needed

### Risk 5: Prorated Charges on Subscription Changes
**Impact:** Users confused by unexpected charges when switching billing periods
**Mitigation:**
- Document proration behavior in frontend UI
- Add warning modal before billing period changes
- Test proration calculation in Stripe test mode
- Consider using `proration_behavior='none'` for billing period changes within same tier

---

## Implementation Order

1. ✅ **Environment Variables** - Update `.env.docker`, `.env.example`, `settings.py`
2. ✅ **Backend API** - Update `CreateCheckoutSessionView` to accept `billing_period`
3. ✅ **Webhook Handlers** - Update subscription created/updated to recognize 4 price IDs
4. ✅ **Backend Unit Tests** - Add comprehensive test coverage for backend
5. ⏸️ **Frontend API Client** - Update `lib/api.ts` to accept `billing_period` parameter
6. ⏸️ **Frontend Pricing Page** - Connect billing toggle to API calls
7. ⏸️ **Frontend Unit Tests** - Add test coverage for API client billing period
8. ⏸️ **Integration Testing** - End-to-end test of frontend → backend → Stripe flow
9. ⏸️ **Deployment** - Configure production environment variables
10. ⏸️ **Monitoring** - Add Sentry alerts for unrecognized price IDs

---

## API Contract Changes

### CreateCheckoutSessionView

**Before:**
```json
{
  "tier": "starter",
  "success_url": "...",
  "cancel_url": "..."
}
```

**After:**
```json
{
  "tier": "starter",
  "billing_period": "yearly",  // NEW: optional, defaults to "monthly"
  "success_url": "...",
  "cancel_url": "..."
}
```

**Response (unchanged):**
```json
{
  "checkout_url": "https://checkout.stripe.com/...",
  "session_id": "cs_...",
  "is_upgrade": false
}
```

---

## Stripe Dashboard Configuration

**Required Actions:**
1. ✅ Create 4 new price IDs in Stripe Dashboard (already done)
2. ⏸️ Update Stripe webhook endpoints to handle all 4 price IDs
3. ⏸️ Test webhooks in Stripe test mode with all 4 price IDs
4. ⏸️ Verify metadata is correctly passed to checkout sessions

**Price ID Verification:**
- Starter Monthly: `price_1SMJdgBOpZCPz6T21xV5B1Vj` ✅
- Starter Annual: `price_1SMJegBOpZCPz6T2ufUMeKOM` ✅
- Pro Monthly: `price_1SMJgGBOpZCPz6T2Y2UhEN9U` ✅
- Pro Annual: `price_1SMJh8BOpZCPz6T2Mjm28HFC` ✅

---

## Deployment Notes

### Pre-Deployment Checklist
- [ ] Update production `.env` with all 4 price IDs
- [ ] Test Stripe webhooks in staging environment
- [ ] Run full test suite with 100% passing
- [ ] Update API documentation with new `billing_period` parameter

### Rollback Plan
1. Revert `backend/payments/views.py` to previous version
2. Revert `backend/config/settings.py` to 2-price-ID configuration
3. No database migrations required - rollback is safe

---

## Success Criteria

- ✅ All 4 price IDs recognized by webhook handlers
- ✅ Checkout sessions created successfully for monthly and yearly billing
- ✅ Credits allocated correctly for all subscription types
- ✅ Test coverage ≥ 80% for new code
- ✅ No errors in Sentry for 48 hours post-deployment
- ✅ API documentation updated with new parameters

---

## Follow-Up Work (Future PRs)

1. **User Account Page Enhancements:**
   - Display current billing period on account page
   - Show next billing date and amount (different for monthly vs annual)
   - Add ability to switch billing period without changing tier

2. **Analytics:**
   - Track monthly vs. yearly subscription adoption rates
   - Monitor churn rates by billing period
   - A/B test different annual discount percentages

3. **Documentation:**
   - Update API documentation with billing period parameter
   - Create user guide explaining annual vs monthly billing
   - Document proration behavior for billing period changes
