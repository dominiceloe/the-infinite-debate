import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { AuthProvider, useAuth } from '@/contexts/AuthContext'
import axios from 'axios'
import { mockUser } from '../utils/test-utils'

// Mock axios
vi.mock('axios', () => {
  const mockAxiosInstance = {
    get: vi.fn(),
    post: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  }

  return {
    default: {
      create: vi.fn(() => mockAxiosInstance),
      get: vi.fn(),
      post: vi.fn(),
      isAxiosError: vi.fn(),
    },
  }
})
const mockedAxios = axios as any

// Mock Next.js router
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

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value
    },
    removeItem: (key: string) => {
      delete store[key]
    },
    clear: () => {
      store = {}
    },
  }
})()

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

describe('AuthContext', () => {
  let mockInstance: any

  beforeEach(() => {
    vi.clearAllMocks()
    localStorageMock.clear()

    // Get the mock instance that axios.create returns
    mockInstance = mockedAxios.create()
    mockInstance.get.mockReset()
    mockInstance.post.mockReset()
  })

  it('provides auth context', () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    )

    const { result } = renderHook(() => useAuth(), { wrapper })

    expect(result.current).toHaveProperty('user')
    expect(result.current).toHaveProperty('isAuthenticated')
    expect(result.current).toHaveProperty('isLoading')
    expect(result.current).toHaveProperty('login')
    expect(result.current).toHaveProperty('register')
    expect(result.current).toHaveProperty('logout')
    expect(result.current).toHaveProperty('refreshUser')
  })

  it('completes loading without token', async () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    )

    const { result } = renderHook(() => useAuth(), { wrapper })

    // Wait for loading to complete (starts as true but completes quickly)
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.user).toBeNull()
    expect(result.current.isAuthenticated).toBe(false)
  })

  it('throws error when used outside provider', () => {
    // Suppress console.error for this test
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})

    expect(() => {
      renderHook(() => useAuth())
    }).toThrow('useAuth must be used within an AuthProvider')

    consoleError.mockRestore()
  })

  it('loads user from cookies on mount', async () => {
    // Mock successful profile fetch (cookies sent automatically)
    mockInstance.get.mockResolvedValueOnce({
      data: mockUser,
    })

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    )

    const { result } = renderHook(() => useAuth(), { wrapper })

    // Wait for loading to complete
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.user).toEqual(mockUser)
    expect(result.current.isAuthenticated).toBe(true)
    expect(mockInstance.get).toHaveBeenCalledWith('/auth/profile/')
  })

  it('handles failed profile fetch (no valid cookies)', async () => {
    // Mock failed profile fetch
    mockInstance.get.mockRejectedValueOnce(new Error('Unauthorized'))

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    )

    const { result } = renderHook(() => useAuth(), { wrapper })

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.user).toBeNull()
    expect(result.current.isAuthenticated).toBe(false)
  })

  it('successfully logs in user', async () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    )

    const { result } = renderHook(() => useAuth(), { wrapper })

    // Wait for initial load
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    // Mock successful login (cookies set automatically by backend)
    mockInstance.post.mockResolvedValueOnce({
      data: {
        user: mockUser,
        message: 'Login successful.',
      },
    })

    await result.current.login('testuser', 'password123')

    // Wait for state to update after login
    await waitFor(() => {
      expect(result.current.user).toEqual(mockUser)
    })

    expect(result.current.isAuthenticated).toBe(true)
    expect(mockInstance.post).toHaveBeenCalledWith('/auth/cookie-login/', {
      username: 'testuser',
      password: 'password123',
    })
    expect(mockPush).toHaveBeenCalledWith('/')
  })

  it('handles login failure', async () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    )

    const { result } = renderHook(() => useAuth(), { wrapper })

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    // Mock axios.isAxiosError to return true
    const originalIsAxiosError = mockedAxios.isAxiosError
    mockedAxios.isAxiosError = vi.fn().mockReturnValue(true)

    // Mock failed login with AxiosError structure
    const axiosError = {
      isAxiosError: true,
      response: {
        data: {
          error: 'Invalid credentials',
        },
      },
    }
    mockInstance.post.mockRejectedValueOnce(axiosError)

    await expect(
      result.current.login('testuser', 'wrongpassword')
    ).rejects.toThrow('Invalid credentials')

    expect(result.current.user).toBeNull()
    expect(result.current.isAuthenticated).toBe(false)

    // Restore original function
    mockedAxios.isAxiosError = originalIsAxiosError
  })

  it('successfully registers user', async () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    )

    const { result } = renderHook(() => useAuth(), { wrapper })

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    // Mock successful registration and auto-login
    mockInstance.post
      .mockResolvedValueOnce({
        data: { message: 'Registration successful' },
      })
      .mockResolvedValueOnce({
        data: {
          user: mockUser,
          message: 'Login successful.',
        },
      })

    await result.current.register({
      username: 'newuser',
      email: 'new@example.com',
      password: 'password123',
      password_confirm: 'password123',  // Fixed: Changed from password2 to password_confirm
    })

    // Wait for state to update after auto-login
    await waitFor(() => {
      expect(result.current.user).toEqual(mockUser)
    })

    expect(result.current.isAuthenticated).toBe(true)
  })

  it('successfully logs out user', async () => {
    // Mock initial auth check
    mockInstance.get.mockResolvedValueOnce({ data: mockUser })

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    )

    const { result } = renderHook(() => useAuth(), { wrapper })

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true)
    })

    // Mock successful logout (clears cookies on backend)
    mockInstance.post.mockResolvedValueOnce({ data: { message: 'Logout successful.' } })

    await result.current.logout()

    // Wait for state to update after logout
    await waitFor(() => {
      expect(result.current.user).toBeNull()
    })

    expect(result.current.isAuthenticated).toBe(false)
    expect(mockInstance.post).toHaveBeenCalledWith('/auth/cookie-logout/')
    expect(mockPush).toHaveBeenCalledWith('/')
  })

  it('refreshes user profile', async () => {
    mockInstance.get
      .mockResolvedValueOnce({ data: mockUser })
      .mockResolvedValueOnce({
        data: { ...mockUser, credits_remaining: 999 },
      })

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    )

    const { result } = renderHook(() => useAuth(), { wrapper })

    await waitFor(() => {
      expect(result.current.user?.credits_remaining).toBe(100)
    })

    await result.current.refreshUser()

    await waitFor(() => {
      expect(result.current.user?.credits_remaining).toBe(999)
    })
  })

})
