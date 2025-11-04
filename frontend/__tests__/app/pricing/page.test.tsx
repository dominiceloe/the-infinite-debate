/**
 * Tests for pricing page - Beta Simplification
 *
 * Beta Changes:
 * - Only "Free Starter" tier shown (Pro/Enterprise hidden)
 * - Simplified pricing: Trial (free) → Starter ($10/mo)
 * - Messaging emphasizes "Try for free, upgrade later"
 *
 * Tests cover:
 * - Pricing page shows only Free/Starter tiers
 * - Pro and Enterprise tiers NOT displayed
 * - Starter tier shows correct pricing ($10/mo)
 * - Trial benefits clearly displayed (10 credits, 7 days)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { renderWithProviders } from '../../utils/test-utils'
import PricingPage from '@/app/pricing/page'
import * as AuthContext from '@/contexts/AuthContext'

// Mock Next.js router
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
    back: vi.fn(),
  }),
  usePathname: () => '/pricing',
  useSearchParams: () => new URLSearchParams(),
}))

describe('PricingPage - Beta Simplification', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Shows Only Free and Starter Tiers', () => {
    it('displays Free trial tier', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<PricingPage />)

      await waitFor(() => {
        expect(screen.getByText(/free trial/i)).toBeInTheDocument()
      })
    })

    it('displays Starter tier ($10/mo)', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<PricingPage />)

      await waitFor(() => {
        expect(screen.getByText(/starter/i)).toBeInTheDocument()
        expect(screen.getByText(/\$10/)).toBeInTheDocument()
      })
    })

    it('does NOT display Pro tier', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<PricingPage />)

      // Pro tier should NOT be present (Beta: hidden)
      await waitFor(() => {
        expect(screen.queryByText(/\$25/)).not.toBeInTheDocument()
        // Look for Pro tier label (case-insensitive, but not "Pro" in "Proprietary" etc.)
        const proTierHeadings = screen.queryAllByRole('heading', { name: /^pro$/i })
        expect(proTierHeadings).toHaveLength(0)
      })
    })

    it('does NOT display Enterprise tier', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<PricingPage />)

      // Enterprise tier should NOT be present (Beta: hidden)
      await waitFor(() => {
        expect(screen.queryByText(/enterprise/i)).not.toBeInTheDocument()
        expect(screen.queryByText(/custom pricing/i)).not.toBeInTheDocument()
        expect(screen.queryByText(/contact.*sales/i)).not.toBeInTheDocument()
      })
    })

    it('shows exactly 2 pricing tiers (Trial + Starter)', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<PricingPage />)

      await waitFor(() => {
        // Should have exactly 2 pricing cards
        const pricingCards = screen.getAllByRole('article') // Assuming cards use <article> tag
        expect(pricingCards).toHaveLength(2)
      })
    })
  })

  describe('Trial Tier Details', () => {
    it('shows 10 credits for trial tier', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<PricingPage />)

      await waitFor(() => {
        // Trial tier should mention 10 credits (Beta: down from 15)
        expect(screen.getByText(/10 credits/i)).toBeInTheDocument()
      })
    })

    it('does NOT show 15 credits (old value)', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<PricingPage />)

      // Should NOT mention old credit amount
      expect(screen.queryByText(/15 credits/i)).not.toBeInTheDocument()
    })

    it('shows 7-day trial duration', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<PricingPage />)

      await waitFor(() => {
        expect(screen.getByText(/7.day/i)).toBeInTheDocument()
      })
    })

    it('shows 2 debates per day limit', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<PricingPage />)

      await waitFor(() => {
        // Beta: Trial users limited to 2 debates/day
        expect(screen.getByText(/2.*debates.*day/i)).toBeInTheDocument()
      })
    })

    it('emphasizes no credit card required', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<PricingPage />)

      await waitFor(() => {
        expect(screen.getByText(/no credit card required/i)).toBeInTheDocument()
      })
    })
  })

  describe('Starter Tier Details', () => {
    it('shows $10/month pricing', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<PricingPage />)

      await waitFor(() => {
        expect(screen.getByText(/\$10/)).toBeInTheDocument()
        expect(screen.getByText(/month/i)).toBeInTheDocument()
      })
    })

    it('shows 30 credits per month', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<PricingPage />)

      await waitFor(() => {
        expect(screen.getByText(/30 credits/i)).toBeInTheDocument()
      })
    })

    it('shows unlimited debates per day', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<PricingPage />)

      await waitFor(() => {
        // Beta: Starter tier has unlimited debates/day
        expect(screen.getByText(/unlimited.*debates/i)).toBeInTheDocument()
      })
    })

    it('has upgrade button for trial users', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: {
          id: 1,
          username: 'trialuser',
          email: 'trial@example.com',
          first_name: 'Trial',
          last_name: 'User',
          email_verified: true,
          subscription_tier: 'trial',
          subscription_status: 'active',
          credits_remaining: 10,
          credits_reset_date: null,
          trial_start_date: '2025-01-01T00:00:00Z',
          trial_end_date: '2025-01-08T00:00:00Z',
          is_trial_expired: false,
          is_on_trial: true,
          is_paid_subscriber: false,
          days_until_trial_end: 5,
          days_until_credit_reset: null,
          created_at: '2025-01-01T00:00:00Z',
        },
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<PricingPage />)

      await waitFor(() => {
        const upgradeButton = screen.getByRole('button', { name: /upgrade/i })
        expect(upgradeButton).toBeInTheDocument()
      })
    })
  })

  describe('Call-to-Action Buttons', () => {
    it('shows "Get Started" for unauthenticated users', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<PricingPage />)

      await waitFor(() => {
        const getStartedButton = screen.getByRole('button', { name: /get started/i })
        expect(getStartedButton).toBeInTheDocument()
      })
    })

    it('shows current plan indicator for trial users', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: {
          id: 1,
          username: 'trialuser',
          email: 'trial@example.com',
          first_name: 'Trial',
          last_name: 'User',
          email_verified: true,
          subscription_tier: 'trial',
          subscription_status: 'active',
          credits_remaining: 10,
          credits_reset_date: null,
          trial_start_date: '2025-01-01T00:00:00Z',
          trial_end_date: '2025-01-08T00:00:00Z',
          is_trial_expired: false,
          is_on_trial: true,
          is_paid_subscriber: false,
          days_until_trial_end: 5,
          days_until_credit_reset: null,
          created_at: '2025-01-01T00:00:00Z',
        },
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<PricingPage />)

      await waitFor(() => {
        expect(screen.getByText(/current plan/i)).toBeInTheDocument()
      })
    })

    it('shows current plan indicator for starter users', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: {
          id: 1,
          username: 'starteruser',
          email: 'starter@example.com',
          first_name: 'Starter',
          last_name: 'User',
          email_verified: true,
          subscription_tier: 'starter',
          subscription_status: 'active',
          credits_remaining: 30,
          credits_reset_date: '2025-02-01',
          trial_start_date: null,
          trial_end_date: null,
          is_trial_expired: false,
          is_on_trial: false,
          is_paid_subscriber: true,
          days_until_trial_end: null,
          days_until_credit_reset: 20,
          created_at: '2025-01-01T00:00:00Z',
        },
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<PricingPage />)

      await waitFor(() => {
        const currentPlanBadges = screen.getAllByText(/current plan/i)
        expect(currentPlanBadges.length).toBeGreaterThan(0)
      })
    })
  })

  describe('Feature Comparison', () => {
    it('shows feature comparison table', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<PricingPage />)

      await waitFor(() => {
        // Should have a comparison table or list of features
        expect(screen.getByRole('table') || screen.getByRole('list')).toBeInTheDocument()
      })
    })

    it('highlights differences between trial and starter', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<PricingPage />)

      await waitFor(() => {
        // Key differences:
        // Trial: 10 credits, 2 debates/day, 7 days
        // Starter: 30 credits/month, unlimited debates/day
        expect(screen.getByText(/10 credits/i)).toBeInTheDocument()
        expect(screen.getByText(/30 credits/i)).toBeInTheDocument()
        expect(screen.getByText(/2.*debates.*day/i)).toBeInTheDocument()
        expect(screen.getByText(/unlimited/i)).toBeInTheDocument()
      })
    })
  })

  describe('Responsive Design', () => {
    it('renders pricing cards in responsive grid', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<PricingPage />)

      // Pricing cards should be in a grid container
      await waitFor(() => {
        const gridContainer = screen.getByTestId('pricing-grid') // Assuming testid exists
        expect(gridContainer).toBeInTheDocument()
      })
    })
  })

  describe('FAQ Section', () => {
    it('displays FAQ about no credit card requirement', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<PricingPage />)

      await waitFor(() => {
        // FAQ section should address common questions
        expect(screen.getByText(/frequently asked questions/i) || screen.getByText(/faq/i)).toBeInTheDocument()
      })
    })

    it('explains trial to paid upgrade process', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<PricingPage />)

      await waitFor(() => {
        // Should explain how to upgrade
        expect(screen.getByText(/upgrade/i)).toBeInTheDocument()
      })
    })
  })
})
