import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { renderWithProviders } from '../utils/test-utils'
import ProtectedRoute from '@/components/ProtectedRoute'
import * as AuthContext from '@/contexts/AuthContext'

// Mock the useRouter hook
const mockPush = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: vi.fn(),
    prefetch: vi.fn(),
    back: vi.fn(),
  }),
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
}))

describe('ProtectedRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading state while checking authentication', () => {
    vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: true,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
    })

    renderWithProviders(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    )

    expect(screen.getByText('Checking authentication...')).toBeInTheDocument()
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('redirects to login when not authenticated', async () => {
    vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
    })

    renderWithProviders(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    )

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/login')
    })

    expect(screen.getByText('Redirecting to login...')).toBeInTheDocument()
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('renders children when authenticated', () => {
    vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
      user: {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        first_name: 'Test',
        last_name: 'User',
        email_verified: true,
        subscription_tier: 'trial',
        subscription_status: 'active',
        credits_remaining: 100,
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

    renderWithProviders(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    )

    expect(screen.getByText('Protected Content')).toBeInTheDocument()
    expect(screen.queryByText('Checking authentication...')).not.toBeInTheDocument()
    expect(screen.queryByText('Redirecting to login...')).not.toBeInTheDocument()
    expect(mockPush).not.toHaveBeenCalled()
  })
})
