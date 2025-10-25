import { describe, it, expect, vi } from 'vitest'
import { screen } from '@testing-library/react'
import { renderWithProviders, userEvent } from '../utils/test-utils'
import Header from '@/components/Header'
import * as AuthContext from '@/contexts/AuthContext'

describe('Header', () => {
  it('renders the app title and subtitle', () => {
    vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
    })

    renderWithProviders(<Header />)

    expect(screen.getByText('The Infinite Debate')).toBeInTheDocument()
    expect(
      screen.getByText('AI-powered dialogues between historical thinkers')
    ).toBeInTheDocument()
  })

  it('shows login and sign up buttons when not authenticated', () => {
    vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
    })

    renderWithProviders(<Header />)

    expect(screen.getByRole('link', { name: /Login/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Sign Up/i })).toBeInTheDocument()
  })

  it('hides login/register buttons when authenticated', () => {
    vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
      user: {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        subscription_tier: 'free',
        credits_remaining: 100,
        subscription_status: 'active',
      },
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
    })

    renderWithProviders(<Header />)

    // Login/Sign Up should not be visible
    expect(screen.queryByRole('link', { name: /Login/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /Sign Up/i })).not.toBeInTheDocument()
  })

  it('displays user credits when authenticated', () => {
    vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
      user: {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        subscription_tier: 'free',
        credits_remaining: 250,
        subscription_status: 'active',
      },
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
    })

    renderWithProviders(<Header />)

    expect(screen.getByText('250')).toBeInTheDocument()
  })

  it('shows Create Debate button for authenticated users', () => {
    vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
      user: {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        subscription_tier: 'pro',
        credits_remaining: 500,
        subscription_status: 'active',
      },
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
    })

    renderWithProviders(<Header />)

    // Should show credits
    expect(screen.getByText('500')).toBeInTheDocument()

    // Should show Create Debate link
    expect(screen.getByRole('link', { name: /Create Debate/i })).toBeInTheDocument()
  })

  it('renders back button when backTo and backLabel provided', () => {
    vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
    })

    renderWithProviders(<Header backTo="/debates" backLabel="All Debates" />)

    const backButton = screen.getByRole('link', { name: /All Debates/i })
    expect(backButton).toBeInTheDocument()
    expect(backButton).toHaveAttribute('href', '/debates')
  })
})
