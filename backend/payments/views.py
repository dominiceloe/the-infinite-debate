import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .models import StripeEvent, StripePayment, StripeSubscriptionHistory
from datetime import datetime, timedelta
from django.utils import timezone

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


@extend_schema(
    summary="Create checkout session",
    description=(
        "Create a Stripe Checkout session for subscription payment. "
        "Returns a checkout URL to redirect the user to Stripe's payment page. "
        "Supports upgrade/downgrade of existing subscriptions with automatic prorating."
    ),
    tags=["Payments"],
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
    },
    responses={
        200: {
            "type": "object",
            "properties": {
                "checkout_url": {"type": "string"},
                "session_id": {"type": "string"},
                "is_upgrade": {"type": "boolean"}
            }
        }
    },
)
class CreateCheckoutSessionView(APIView):
    """
    Create a Stripe Checkout Session for subscription payment.
    """
    permission_classes = [IsAuthenticated]

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

        try:
            # Check if user has an existing active subscription
            if user.stripe_subscription_id:
                # Handle subscription upgrade/downgrade
                try:
                    subscription = stripe.Subscription.retrieve(user.stripe_subscription_id)

                    # Only modify if subscription is active or past_due
                    if subscription['status'] in ['active', 'past_due', 'trialing']:
                        # Get the current subscription item
                        subscription_item_id = subscription['items']['data'][0]['id']

                        # Modify the subscription to the new price
                        updated_subscription = stripe.Subscription.modify(
                            user.stripe_subscription_id,
                            items=[{
                                'id': subscription_item_id,
                                'price': price_id,  # Use dynamically selected price_id
                            }],
                            proration_behavior='create_prorations',  # Prorate the charge
                        )

                        # Update user tier immediately (webhook will also update this)
                        old_tier = user.subscription_tier
                        user.subscription_tier = tier
                        if tier == 'starter':
                            user.credits_remaining = 30
                        elif tier == 'pro':
                            user.credits_remaining = 100
                        user.save()

                        # Log the change
                        StripeSubscriptionHistory.objects.create(
                            user=user,
                            subscription_id=user.stripe_subscription_id,
                            action='updated',
                            tier=tier,
                            status=user.subscription_status,
                            metadata={'old_tier': old_tier, 'new_tier': tier}
                        )

                        return Response({
                            'message': 'Subscription updated successfully',
                            'tier': tier,
                            'is_upgrade': True,
                            'old_tier': old_tier,
                        })
                    else:
                        # Subscription is cancelled or inactive, create new one
                        user.stripe_subscription_id = ''
                        user.save()
                except stripe.StripeError as e:
                    # If subscription doesn't exist, clear it and create new checkout
                    user.stripe_subscription_id = ''
                    user.save()

            # Create or get Stripe customer
            if not user.stripe_customer_id:
                customer = stripe.Customer.create(
                    email=user.email,
                    metadata={
                        'user_id': user.id,
                        'username': user.username,
                    }
                )
                user.stripe_customer_id = customer.id
                user.save()
            else:
                customer_id = user.stripe_customer_id

            # Create checkout session for new subscription
            checkout_session = stripe.checkout.Session.create(
                customer=user.stripe_customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,  # Use dynamically selected price_id
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=request.data.get('success_url', 'http://localhost:3001/account?payment=success'),
                cancel_url=request.data.get('cancel_url', 'http://localhost:3001/pricing?payment=cancelled'),
                metadata={
                    'user_id': user.id,
                    'tier': tier,
                    'billing_period': billing_period,
                }
            )

            return Response({
                'checkout_url': checkout_session.url,
                'session_id': checkout_session.id,
                'is_upgrade': False,
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema(exclude=True)  # Exclude from API docs (webhook endpoint)
@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    """
    Handle Stripe webhook events.
    """
    permission_classes = []  # No auth required for webhooks

    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        webhook_secret = settings.STRIPE_WEBHOOK_SECRET

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except ValueError:
            return Response({'error': 'Invalid payload'}, status=400)
        except stripe.SignatureVerificationError:
            return Response({'error': 'Invalid signature'}, status=400)

        # Log the event
        stripe_event, created = StripeEvent.objects.get_or_create(
            event_id=event['id'],
            defaults={
                'event_type': event['type'],
                'data': event['data'],
            }
        )

        if not created:
            # Already processed this event
            return Response({'status': 'already processed'})

        # Handle the event
        try:
            if event['type'] == 'checkout.session.completed':
                self._handle_checkout_completed(event)
            elif event['type'] == 'customer.subscription.created':
                self._handle_subscription_created(event)
            elif event['type'] == 'customer.subscription.updated':
                self._handle_subscription_updated(event)
            elif event['type'] == 'customer.subscription.deleted':
                self._handle_subscription_deleted(event)
            elif event['type'] == 'invoice.payment_succeeded':
                self._handle_payment_succeeded(event)
            elif event['type'] == 'invoice.payment_failed':
                self._handle_payment_failed(event)

            # Mark as processed
            stripe_event.processed = True
            stripe_event.save()

        except Exception as e:
            stripe_event.error = str(e)
            stripe_event.save()
            return Response({'error': str(e)}, status=500)

        return Response({'status': 'success'})

    def _handle_checkout_completed(self, event):
        """Handle successful checkout session."""
        session = event['data']['object']
        user_id = session['metadata'].get('user_id')
        tier = session['metadata'].get('tier')

        from users.models import User
        try:
            user = User.objects.get(id=user_id)
            user.stripe_customer_id = session['customer']

            # Update subscription info (will be fully updated when subscription.created fires)
            if tier:
                user.subscription_tier = tier
                user.subscription_status = 'active'

            user.save()
        except User.DoesNotExist:
            pass

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

    def _handle_subscription_deleted(self, event):
        """Handle subscription cancellation."""
        subscription = event['data']['object']
        customer_id = subscription['customer']

        from users.models import User
        try:
            user = User.objects.get(stripe_customer_id=customer_id)
            user.subscription_status = 'cancelled'
            user.save()

            StripeSubscriptionHistory.objects.create(
                user=user,
                subscription_id=subscription['id'],
                action='canceled',
                tier=user.subscription_tier,
                status='cancelled'
            )

        except User.DoesNotExist:
            pass

    def _handle_payment_succeeded(self, event):
        """Handle successful payment."""
        invoice = event['data']['object']
        customer_id = invoice['customer']

        from users.models import User
        try:
            user = User.objects.get(stripe_customer_id=customer_id)

            # Create payment record
            StripePayment.objects.create(
                user=user,
                payment_intent_id=invoice.get('payment_intent', f"invoice_{invoice['id']}"),
                amount=invoice['amount_paid'] / 100,  # Convert cents to dollars
                currency=invoice['currency'],
                status='succeeded',
                subscription_id=invoice.get('subscription', ''),
                description=f"Payment for {invoice.get('lines', {}).get('data', [{}])[0].get('description', 'subscription')}"
            )

        except User.DoesNotExist:
            pass

    def _handle_payment_failed(self, event):
        """Handle failed payment."""
        invoice = event['data']['object']
        customer_id = invoice['customer']

        from users.models import User
        try:
            user = User.objects.get(stripe_customer_id=customer_id)
            user.subscription_status = 'past_due'
            user.save()

            StripePayment.objects.create(
                user=user,
                payment_intent_id=invoice.get('payment_intent', f"invoice_{invoice['id']}"),
                amount=invoice['amount_due'] / 100,
                currency=invoice['currency'],
                status='failed',
                subscription_id=invoice.get('subscription', ''),
                description="Failed payment attempt"
            )

        except User.DoesNotExist:
            pass


@extend_schema(
    summary="Get subscription details",
    description=(
        "Retrieve current user's subscription information from Stripe, "
        "including tier, status, credits, and billing period."
    ),
    tags=["Payments"],
    responses={200: OpenApiTypes.OBJECT},
)
class GetSubscriptionView(APIView):
    """
    Get current user's subscription information.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        subscription_data = {
            'tier': user.subscription_tier,
            'status': user.subscription_status,
            'credits_remaining': user.credits_remaining,
            'credits_reset_date': user.credits_reset_date,
            'stripe_customer_id': user.stripe_customer_id,
            'stripe_subscription_id': user.stripe_subscription_id,
        }

        # If user has Stripe subscription, fetch latest info
        if user.stripe_subscription_id:
            try:
                subscription = stripe.Subscription.retrieve(user.stripe_subscription_id)
                subscription_data['stripe_status'] = subscription['status']
                subscription_data['current_period_end'] = datetime.fromtimestamp(
                    subscription['current_period_end']
                ).isoformat()
                subscription_data['cancel_at_period_end'] = subscription['cancel_at_period_end']
            except Exception as e:
                subscription_data['stripe_error'] = str(e)

        return Response(subscription_data)


@extend_schema(
    summary="Cancel subscription",
    description=(
        "Cancel the user's subscription at the end of the current billing period. "
        "Access and credits remain until the period ends."
    ),
    tags=["Payments"],
    responses={
        200: {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "cancel_at": {"type": "string", "format": "date-time"}
            }
        }
    },
)
class CancelSubscriptionView(APIView):
    """
    Cancel user's subscription.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if not user.stripe_subscription_id:
            return Response(
                {'error': 'No active subscription found'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Cancel at period end (don't immediately revoke access)
            subscription = stripe.Subscription.modify(
                user.stripe_subscription_id,
                cancel_at_period_end=True
            )

            return Response({
                'message': 'Subscription will be cancelled at the end of the billing period',
                'cancel_at': datetime.fromtimestamp(subscription['current_period_end']).isoformat()
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema(
    summary="Get payment history",
    description="Retrieve the authenticated user's complete payment history.",
    tags=["Payments"],
    responses={200: OpenApiTypes.OBJECT},
)
class PaymentHistoryView(APIView):
    """
    Get user's payment history.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Get all payments for this user, ordered by most recent
        payments = StripePayment.objects.filter(user=user).order_by('-created_at')

        # Serialize payment data
        payment_data = [{
            'id': payment.id,
            'amount': str(payment.amount),
            'currency': payment.currency,
            'status': payment.status,
            'description': payment.description,
            'created_at': payment.created_at.isoformat(),
            'payment_intent_id': payment.payment_intent_id,
        } for payment in payments]

        return Response(payment_data)
