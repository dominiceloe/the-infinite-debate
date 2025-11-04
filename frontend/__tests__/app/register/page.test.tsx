/**
 * Tests for registration page - Beta Simplification
 *
 * Beta Changes:
 * - Credit card field REMOVED from registration form
 * - Stripe Elements component REMOVED
 * - Registration messaging shows 10 credits (down from 15)
 * - Registration form simpler (username, email, password only)
 *
 * Tests cover:
 * - Registration form does NOT show credit card fields
 * - Stripe Elements component NOT rendered
 * - Success messaging shows 10 credits
 * - Registration succeeds without payment_method_id
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from '../../utils/test-utils'
import RegisterPage from '@/app/register/page'
import * as AuthContext from '@/contexts/AuthContext'

// Mock Next.js router
const mockPush = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: vi.fn(),
    prefetch: vi.fn(),
    back: vi.fn(),
  }),
  usePathname: () => '/register',
  useSearchParams: () => new URLSearchParams(),
}))

// Mock Stripe (should NOT be used in Beta)
vi.mock('@stripe/react-stripe-js', () => ({
  Elements: ({ children }: { children: React.ReactNode }) => <div data-testid="stripe-elements-mock">{children}</div>,
  CardElement: () => <div data-testid="card-element-mock">Card Element</div>,
  useStripe: () => null,
  useElements: () => null,
}))

describe('RegisterPage - Beta Simplification', () => {
  let mockRegister: ReturnType<typeof vi.fn>

  beforeEach(() => {
    vi.clearAllMocks()
    mockRegister = vi.fn()
  })

  describe('No Credit Card Fields', () => {
    it('does not render Stripe Elements component', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: mockRegister,
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<RegisterPage />)

      // Stripe Elements should NOT be present
      const stripeElements = screen.queryByTestId('stripe-elements-mock')
      expect(stripeElements).not.toBeInTheDocument()
    })

    it('does not render CardElement component', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: mockRegister,
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<RegisterPage />)

      // Card element should NOT be present
      const cardElement = screen.queryByTestId('card-element-mock')
      expect(cardElement).not.toBeInTheDocument()
    })

    it('does not show credit card label or instructions', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: mockRegister,
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<RegisterPage />)

      // Credit card text should NOT appear
      expect(screen.queryByText(/credit card/i)).not.toBeInTheDocument()
      expect(screen.queryByText(/payment method/i)).not.toBeInTheDocument()
      expect(screen.queryByText(/card number/i)).not.toBeInTheDocument()
    })

    it('shows only basic registration fields', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: mockRegister,
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<RegisterPage />)

      // Should have basic fields only
      expect(screen.getByLabelText(/username/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument()

      // Should NOT have card-related fields
      expect(screen.queryByText(/card/i)).not.toBeInTheDocument()
    })
  })

  describe('Registration Shows 10 Credits', () => {
    it('displays 10 credits in trial benefits messaging', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: mockRegister,
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<RegisterPage />)

      // Should mention 10 credits (Beta: down from 15)
      await waitFor(() => {
        expect(screen.getByText(/10 credits/i)).toBeInTheDocument()
      })
    })

    it('does NOT show 15 credits (old value)', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: mockRegister,
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<RegisterPage />)

      // Should NOT mention 15 credits
      expect(screen.queryByText(/15 credits/i)).not.toBeInTheDocument()
    })

    it('mentions 7-day trial period', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: mockRegister,
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<RegisterPage />)

      // Should mention trial period
      await waitFor(() => {
        expect(screen.getByText(/7.day trial/i)).toBeInTheDocument()
      })
    })

    it('shows no credit card required messaging', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: mockRegister,
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<RegisterPage />)

      // Should emphasize no card required (Beta selling point)
      await waitFor(() => {
        expect(screen.getByText(/no credit card required/i)).toBeInTheDocument()
      })
    })
  })

  describe('Registration Form Submission', () => {
    it('submits registration without payment_method_id', async () => {
      const user = userEvent.setup()

      mockRegister.mockResolvedValue(undefined)

      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: mockRegister,
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<RegisterPage />)

      // Fill in basic fields
      const usernameInput = screen.getByLabelText(/username/i)
      const emailInput = screen.getByLabelText(/email/i)
      const passwordInput = screen.getByLabelText(/^password$/i)
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i)

      await user.type(usernameInput, 'newuser')
      await user.type(emailInput, 'new@example.com')
      await user.type(passwordInput, 'SecurePass123!')
      await user.type(confirmPasswordInput, 'SecurePass123!')

      // Submit form
      const submitButton = screen.getByRole('button', { name: /sign up/i })
      await user.click(submitButton)

      // Verify registration called WITHOUT payment_method_id
      await waitFor(() => {
        expect(mockRegister).toHaveBeenCalledWith({
          username: 'newuser',
          email: 'new@example.com',
          password: 'SecurePass123!',
          password2: 'SecurePass123!',
          // NO payment_method_id field
        })
      })
    })

    it('shows success message after registration', async () => {
      const user = userEvent.setup()

      mockRegister.mockResolvedValue(undefined)

      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: mockRegister,
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<RegisterPage />)

      // Fill and submit form
      await user.type(screen.getByLabelText(/username/i), 'testuser')
      await user.type(screen.getByLabelText(/email/i), 'test@example.com')
      await user.type(screen.getByLabelText(/^password$/i), 'Password123!')
      await user.type(screen.getByLabelText(/confirm password/i), 'Password123!')

      const submitButton = screen.getByRole('button', { name: /sign up/i })
      await user.click(submitButton)

      // Should show success (redirected or message shown)
      await waitFor(() => {
        expect(mockRegister).toHaveBeenCalled()
      })
    })

    it('handles registration errors gracefully', async () => {
      const user = userEvent.setup()

      mockRegister.mockRejectedValue(new Error('Username already exists'))

      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: mockRegister,
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<RegisterPage />)

      // Fill and submit form
      await user.type(screen.getByLabelText(/username/i), 'existinguser')
      await user.type(screen.getByLabelText(/email/i), 'existing@example.com')
      await user.type(screen.getByLabelText(/^password$/i), 'Password123!')
      await user.type(screen.getByLabelText(/confirm password/i), 'Password123!')

      const submitButton = screen.getByRole('button', { name: /sign up/i })
      await user.click(submitButton)

      // Should show error message
      await waitFor(() => {
        expect(screen.getByText(/username already exists/i)).toBeInTheDocument()
      })
    })
  })

  describe('Form Validation', () => {
    it('validates password match', async () => {
      const user = userEvent.setup()

      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: mockRegister,
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<RegisterPage />)

      await user.type(screen.getByLabelText(/username/i), 'testuser')
      await user.type(screen.getByLabelText(/email/i), 'test@example.com')
      await user.type(screen.getByLabelText(/^password$/i), 'Password123!')
      await user.type(screen.getByLabelText(/confirm password/i), 'DifferentPass456!')

      const submitButton = screen.getByRole('button', { name: /sign up/i })
      await user.click(submitButton)

      // Should show validation error
      await waitFor(() => {
        expect(screen.getByText(/passwords.*match/i)).toBeInTheDocument()
      })
    })

    it('validates email format', async () => {
      const user = userEvent.setup()

      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: mockRegister,
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<RegisterPage />)

      await user.type(screen.getByLabelText(/email/i), 'invalid-email')

      const submitButton = screen.getByRole('button', { name: /sign up/i })
      await user.click(submitButton)

      // Should show email validation error
      await waitFor(() => {
        expect(screen.getByText(/valid email/i)).toBeInTheDocument()
      })
    })

    it('validates password strength', async () => {
      const user = userEvent.setup()

      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: mockRegister,
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<RegisterPage />)

      await user.type(screen.getByLabelText(/^password$/i), 'weak')

      const submitButton = screen.getByRole('button', { name: /sign up/i })
      await user.click(submitButton)

      // Should show password strength error
      await waitFor(() => {
        expect(screen.getByText(/password.*strong/i)).toBeInTheDocument()
      })
    })
  })

  describe('Redirect Behavior', () => {
    it('redirects authenticated users to home', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: {
          id: 1,
          username: 'existinguser',
          email: 'existing@example.com',
          first_name: 'Existing',
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
        register: mockRegister,
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<RegisterPage />)

      // Should redirect to home (or not render form)
      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/')
      })
    })
  })

  describe('Loading States', () => {
    it('shows loading spinner during auth check', () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: true,  // Loading state
        login: vi.fn(),
        register: mockRegister,
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<RegisterPage />)

      expect(screen.getByRole('progressbar')).toBeInTheDocument()
    })

    it('disables submit button during registration', async () => {
      const user = userEvent.setup()

      // Mock slow registration
      mockRegister.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)))

      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: mockRegister,
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<RegisterPage />)

      // Fill form
      await user.type(screen.getByLabelText(/username/i), 'testuser')
      await user.type(screen.getByLabelText(/email/i), 'test@example.com')
      await user.type(screen.getByLabelText(/^password$/i), 'Password123!')
      await user.type(screen.getByLabelText(/confirm password/i), 'Password123!')

      const submitButton = screen.getByRole('button', { name: /sign up/i })
      await user.click(submitButton)

      // Button should be disabled during submission
      await waitFor(() => {
        expect(submitButton).toBeDisabled()
      })
    })
  })
})
