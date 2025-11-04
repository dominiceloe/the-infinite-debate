import { render, RenderOptions } from '@testing-library/react'
import { ReactElement, ReactNode } from 'react'
import { AuthProvider } from '@/contexts/AuthContext'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { vi } from 'vitest'

// Create a new QueryClient for each test
export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  })
}

interface AllTheProvidersProps {
  children: ReactNode
}

function AllTheProviders({ children }: AllTheProvidersProps) {
  const queryClient = createTestQueryClient()

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>{children}</AuthProvider>
    </QueryClientProvider>
  )
}

// Custom render function that includes providers
export function renderWithProviders(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) {
  return render(ui, { wrapper: AllTheProviders, ...options })
}

// Mock localStorage
export function mockLocalStorage() {
  const storage: Record<string, string> = {}

  return {
    getItem: vi.fn((key: string) => storage[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      storage[key] = value
    }),
    removeItem: vi.fn((key: string) => {
      delete storage[key]
    }),
    clear: vi.fn(() => {
      Object.keys(storage).forEach(key => delete storage[key])
    }),
    get length() {
      return Object.keys(storage).length
    },
    key: vi.fn((index: number) => {
      const keys = Object.keys(storage)
      return keys[index] || null
    }),
  }
}

// Mock user data for tests (matches User interface from types/auth.ts)
export const mockUser = {
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
  first_name: 'Test',
  last_name: 'User',
  email_verified: true,
  subscription_tier: 'trial' as const,  // Fixed: 'free' is not a valid tier (trial/starter/pro/enterprise)
  subscription_status: 'active' as const,
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
}

export const mockPremiumUser = {
  ...mockUser,
  id: 2,
  username: 'premiumuser',
  subscription_tier: 'pro' as const,
  credits_remaining: 1000,
  trial_start_date: null,
  trial_end_date: null,
  is_trial_expired: false,
  is_on_trial: false,
  is_paid_subscriber: true,
  days_until_trial_end: null,
  credits_reset_date: '2025-02-01',
  days_until_credit_reset: 20,
}

// Re-export everything from testing library
export * from '@testing-library/react'
export { default as userEvent } from '@testing-library/user-event'
