/**
 * TypeScript type definitions for API interactions
 * Replaces all 'any' types with proper interfaces for type safety
 */

/**
 * Rate limiting error response structure from Django REST throttling
 */
export interface ThrottleErrorResponse {
  message?: string;
  retry_after_display?: string;
  retry_after_seconds?: number;
}

/**
 * Extended error type with throttle information
 */
export interface ThrottleError extends Error {
  isThrottled: true;
  retryAfter?: string;
  retryAfterSeconds?: number;
}

/**
 * Response from debate generation endpoint
 */
export interface DebateGenerationResponse {
  status: 'generating' | 'completed' | 'failed';
  message?: string;
  debate_id?: number;
}

/**
 * Subscription details from payments API
 */
export interface SubscriptionDetails {
  tier: string;
  status: 'active' | 'canceled' | 'past_due' | 'trialing';
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  credits_remaining?: number;
}

/**
 * Payment history record from Stripe
 */
export interface PaymentRecord {
  id: number | string;
  created_at: string;
  description?: string;
  amount: string | number;
  status: 'succeeded' | 'failed' | 'pending';
}

/**
 * Stripe card change event from CardElement
 */
export interface StripeCardChangeEvent {
  complete: boolean;
  error?: {
    message: string;
  };
}

/**
 * External link structure for persona profiles
 */
export interface ExternalLink {
  label: string;
  url: string;
}
