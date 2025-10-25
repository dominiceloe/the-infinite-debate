import { describe, it, expect } from 'vitest'
import { hasPersonaAccess, getTierBadge, getDebateLimits } from '@/lib/tiers'

describe('Tier Utilities', () => {
  describe('hasPersonaAccess', () => {
    it('allows access to free personas for everyone', () => {
      expect(hasPersonaAccess(undefined, 'free')).toBe(true)
      expect(hasPersonaAccess('free', 'free')).toBe(true)
      expect(hasPersonaAccess('starter', 'free')).toBe(true)
      expect(hasPersonaAccess('pro', 'free')).toBe(true)
      expect(hasPersonaAccess('enterprise', 'free')).toBe(true)
    })

    it('allows access to personas with no required tier', () => {
      expect(hasPersonaAccess('free', undefined)).toBe(true)
      expect(hasPersonaAccess(undefined, undefined)).toBe(true)
    })

    it('denies access when user has no tier but persona requires one', () => {
      expect(hasPersonaAccess(undefined, 'starter')).toBe(false)
      expect(hasPersonaAccess(undefined, 'pro')).toBe(false)
      expect(hasPersonaAccess(undefined, 'enterprise')).toBe(false)
    })

    it('allows access when user tier matches required tier', () => {
      expect(hasPersonaAccess('starter', 'starter')).toBe(true)
      expect(hasPersonaAccess('pro', 'pro')).toBe(true)
      expect(hasPersonaAccess('enterprise', 'enterprise')).toBe(true)
    })

    it('allows access when user tier is higher than required', () => {
      expect(hasPersonaAccess('pro', 'starter')).toBe(true)
      expect(hasPersonaAccess('enterprise', 'starter')).toBe(true)
      expect(hasPersonaAccess('enterprise', 'pro')).toBe(true)
    })

    it('denies access when user tier is lower than required', () => {
      expect(hasPersonaAccess('free', 'starter')).toBe(false)
      expect(hasPersonaAccess('free', 'pro')).toBe(false)
      expect(hasPersonaAccess('starter', 'pro')).toBe(false)
      expect(hasPersonaAccess('starter', 'enterprise')).toBe(false)
      expect(hasPersonaAccess('pro', 'enterprise')).toBe(false)
    })

    it('treats trial tier same as free tier', () => {
      expect(hasPersonaAccess('trial', 'free')).toBe(true)
      expect(hasPersonaAccess('trial', 'starter')).toBe(false)
    })
  })

  describe('getTierBadge', () => {
    it('returns null when user has access to persona', () => {
      expect(getTierBadge('free', 'free')).toBeNull()
      expect(getTierBadge('starter', 'starter')).toBeNull()
      expect(getTierBadge('pro', 'pro')).toBeNull()
      expect(getTierBadge('starter', 'pro')).toBeNull()
      expect(getTierBadge('starter', 'enterprise')).toBeNull()
    })

    it('returns starter badge for locked starter personas', () => {
      const badge = getTierBadge('starter', 'free')
      expect(badge).toEqual({ label: 'Starter', color: '#10b981' })
    })

    it('returns pro badge for locked pro personas', () => {
      const badge = getTierBadge('pro', 'free')
      expect(badge).toEqual({ label: 'Pro', color: '#6366f1' })

      const badge2 = getTierBadge('pro', 'starter')
      expect(badge2).toEqual({ label: 'Pro', color: '#6366f1' })
    })

    it('returns enterprise badge for locked enterprise personas', () => {
      const badge = getTierBadge('enterprise', 'free')
      expect(badge).toEqual({ label: 'Enterprise', color: '#8b5cf6' })

      const badge2 = getTierBadge('enterprise', 'pro')
      expect(badge2).toEqual({ label: 'Enterprise', color: '#8b5cf6' })
    })

    it('returns null for free personas', () => {
      expect(getTierBadge('free', undefined)).toBeNull()
      expect(getTierBadge(undefined, 'free')).toBeNull()
    })
  })

  describe('getDebateLimits', () => {
    it('returns correct limits for free tier', () => {
      const limits = getDebateLimits('free')
      expect(limits).toEqual({
        maxParticipants: 2,
        maxRounds: 3,
        allowedDepths: ['introductory'],
      })
    })

    it('returns correct limits for trial tier', () => {
      const limits = getDebateLimits('trial')
      expect(limits).toEqual({
        maxParticipants: 2,
        maxRounds: 3,
        allowedDepths: ['introductory'],
      })
    })

    it('returns correct limits for starter tier', () => {
      const limits = getDebateLimits('starter')
      expect(limits).toEqual({
        maxParticipants: 6,
        maxRounds: 7,
        allowedDepths: ['introductory', 'intermediate'],
      })
    })

    it('returns correct limits for pro tier', () => {
      const limits = getDebateLimits('pro')
      expect(limits).toEqual({
        maxParticipants: 10,
        maxRounds: 10,
        allowedDepths: ['introductory', 'intermediate', 'advanced'],
      })
    })

    it('returns correct limits for enterprise tier', () => {
      const limits = getDebateLimits('enterprise')
      expect(limits).toEqual({
        maxParticipants: 15,
        maxRounds: 15,
        allowedDepths: ['introductory', 'intermediate', 'advanced'],
      })
    })

    it('returns free tier limits when tier is undefined', () => {
      const limits = getDebateLimits(undefined)
      expect(limits).toEqual({
        maxParticipants: 2,
        maxRounds: 3,
        allowedDepths: ['introductory'],
      })
    })
  })
})
