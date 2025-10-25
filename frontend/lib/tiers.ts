// Subscription tier utilities

export const TIER_HIERARCHY = {
  trial: 0,
  free: 0,
  starter: 1,
  pro: 2,
  enterprise: 3,
} as const;

export type SubscriptionTier = keyof typeof TIER_HIERARCHY;

/**
 * Check if user has access to a persona based on tier
 */
export function hasPersonaAccess(
  userTier: string | undefined,
  requiredTier: string | undefined
): boolean {
  if (!requiredTier || requiredTier === 'free') return true;
  if (!userTier) return false;

  const userLevel = TIER_HIERARCHY[userTier as SubscriptionTier] ?? 0;
  const requiredLevel = TIER_HIERARCHY[requiredTier as SubscriptionTier] ?? 0;

  return userLevel >= requiredLevel;
}

/**
 * Get badge configuration for a tier
 * Only show badges for personas that are locked (above user's tier)
 */
export function getTierBadge(
  personaTier: string | undefined,
  userTier: string | undefined
): {
  label: string;
  color: string;
} | null {
  // Don't show badge if user has access
  if (hasPersonaAccess(userTier, personaTier)) {
    return null;
  }

  // Show badge for locked personas
  switch (personaTier) {
    case 'starter':
      return { label: 'Starter', color: '#10b981' }; // green
    case 'pro':
      return { label: 'Pro', color: '#6366f1' }; // indigo
    case 'enterprise':
      return { label: 'Enterprise', color: '#8b5cf6' }; // purple
    default:
      return null;
  }
}

/**
 * Get debate limits based on user tier
 */
export function getDebateLimits(userTier: string | undefined) {
  const tier = userTier || 'free';

  switch (tier) {
    case 'enterprise':
      return {
        maxParticipants: 15,
        maxRounds: 15,
        allowedDepths: ['introductory', 'intermediate', 'advanced'] as const,
      };
    case 'pro':
      return {
        maxParticipants: 10,
        maxRounds: 10,
        allowedDepths: ['introductory', 'intermediate', 'advanced'] as const,
      };
    case 'starter':
      return {
        maxParticipants: 6,
        maxRounds: 7,
        allowedDepths: ['introductory', 'intermediate'] as const,
      };
    case 'trial':
    case 'free':
    default:
      return {
        maxParticipants: 2,
        maxRounds: 3,
        allowedDepths: ['introductory'] as const,
      };
  }
}
