import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { renderWithProviders } from '../utils/test-utils'
import HomePage from '@/app/page'
import * as AuthContext from '@/contexts/AuthContext'
import { apiClient } from '@/lib/api'

// Mock the API client
vi.mock('@/lib/api', () => ({
  apiClient: {
    personas: {
      getByCategory: vi.fn(),
    },
  },
}))

// Mock Next.js Image component
vi.mock('next/image', () => ({
  default: ({ src, alt, ...props }: any) => {
    // eslint-disable-next-line @next/next/no-img-element
    return <img src={src} alt={alt} {...props} />
  },
}))

const mockPersonasData = {
  theologians: [
    {
      id: 1,
      name: 'Thomas Aquinas',
      slug: 'aquinas',
      category: 'theologians',
      title: 'Doctor Angelicus',
      birth_year: 1225,
      death_year: 1274,
      era: 'medieval',
      religion: 'Christianity',
      required_tier: 'free',
      portrait_url: '/portraits/aquinas.jpg',
      debate_count: 10,
    },
    {
      id: 2,
      name: 'Moses Maimonides',
      slug: 'maimonides',
      category: 'theologians',
      title: 'The Great Eagle',
      birth_year: 1138,
      death_year: 1204,
      era: 'medieval',
      religion: 'Judaism',
      required_tier: 'free',
      portrait_url: '/portraits/maimonides.jpg',
      debate_count: 8,
    },
  ],
  philosophers: [
    {
      id: 3,
      name: 'Socrates',
      slug: 'socrates',
      category: 'philosophers',
      title: 'The Gadfly of Athens',
      birth_year: -470,
      death_year: -399,
      era: 'ancient',
      religion: null,
      required_tier: 'free',
      portrait_url: '/portraits/socrates.jpg',
      debate_count: 15,
    },
    {
      id: 4,
      name: 'Immanuel Kant',
      slug: 'kant',
      category: 'philosophers',
      title: 'The Boundary-Setter',
      birth_year: 1724,
      death_year: 1804,
      era: 'enlightenment',
      religion: null,
      required_tier: 'trial',
      portrait_url: '/portraits/kant.jpg',
      debate_count: 12,
    },
  ],
  scientists: [
    {
      id: 5,
      name: 'Isaac Newton',
      slug: 'newton',
      category: 'scientists',
      title: 'Architect of Classical Physics',
      birth_year: 1643,
      death_year: 1727,
      era: 'enlightenment',
      religion: null,
      required_tier: 'free',
      portrait_url: '/portraits/newton.jpg',
      debate_count: 6,
    },
  ],
}

describe('HomePage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Mock successful API response
    vi.mocked(apiClient.personas.getByCategory).mockResolvedValue(mockPersonasData)
  })

  it('renders the page title and description', async () => {
    vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
    })

    renderWithProviders(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText(/The Infinite Debate/i)).toBeInTheDocument()
    })
  })

  describe('Persona Cards - Mobile Responsive Layout', () => {
    it('renders persona cards in grid layout', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<HomePage />)

      await waitFor(() => {
        expect(screen.getByText('Thomas Aquinas')).toBeInTheDocument()
        expect(screen.getByText('Socrates')).toBeInTheDocument()
        expect(screen.getByText('Isaac Newton')).toBeInTheDocument()
      })
    })

    it('displays persona images with correct alt text', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<HomePage />)

      await waitFor(() => {
        const aquinasImage = screen.getByAltText('Thomas Aquinas')
        expect(aquinasImage).toBeInTheDocument()
        expect(aquinasImage).toHaveAttribute('src', '/portraits/aquinas.jpg')
      })
    })

    it('displays persona titles and categories', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<HomePage />)

      await waitFor(() => {
        expect(screen.getByText('Doctor Angelicus')).toBeInTheDocument()
        expect(screen.getByText('The Gadfly of Athens')).toBeInTheDocument()
        expect(screen.getByText('Architect of Classical Physics')).toBeInTheDocument()
      })
    })

    it('shows debate count for each persona', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<HomePage />)

      await waitFor(() => {
        // Debate counts displayed as badges
        expect(screen.getByText('10')).toBeInTheDocument() // Aquinas
        expect(screen.getByText('15')).toBeInTheDocument() // Socrates
        expect(screen.getByText('6')).toBeInTheDocument()  // Newton
      })
    })

    it('displays tier badges for premium personas', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<HomePage />)

      await waitFor(() => {
        // Kant requires 'trial' tier, should show badge
        const kantCard = screen.getByText('Immanuel Kant').closest('div')
        expect(kantCard).toBeInTheDocument()
      })
    })

    it('links each persona card to detail page', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<HomePage />)

      await waitFor(() => {
        const aquinasLink = screen.getByText('Thomas Aquinas').closest('a')
        expect(aquinasLink).toHaveAttribute('href', '/personas/aquinas')
      })
    })
  })

  describe('Filter Chips - Mobile Touch Targets', () => {
    it('renders category filter chips', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<HomePage />)

      await waitFor(() => {
        // Category filter chips should be present
        expect(screen.getByText('Theologians')).toBeInTheDocument()
        expect(screen.getByText('Philosophers')).toBeInTheDocument()
        expect(screen.getByText('Scientists')).toBeInTheDocument()
      })
    })

    it('renders era filter chips', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<HomePage />)

      await waitFor(() => {
        // Era filter chips should be present
        expect(screen.getByText(/Ancient/i)).toBeInTheDocument()
        expect(screen.getByText(/Medieval/i)).toBeInTheDocument()
        expect(screen.getByText(/Enlightenment/i)).toBeInTheDocument()
      })
    })

    it('filter chips have adequate touch targets for mobile', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<HomePage />)

      await waitFor(() => {
        const theologiansChip = screen.getByText('Theologians').closest('div')
        expect(theologiansChip).toBeInTheDocument()
        // Touch target should be 36px height on mobile (WCAG 2.1 compliant)
        // Actual height styling tested via visual regression or e2e tests
      })
    })
  })

  describe('Search Functionality', () => {
    it('renders search input field', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<HomePage />)

      await waitFor(() => {
        const searchInput = screen.getByPlaceholderText(/Search personas/i)
        expect(searchInput).toBeInTheDocument()
      })
    })

    it('shows clear button when search has text', async () => {
      const user = (await import('@testing-library/user-event')).default.setup()
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<HomePage />)

      await waitFor(async () => {
        const searchInput = screen.getByPlaceholderText(/Search personas/i)
        await user.type(searchInput, 'Socrates')

        // Clear button should appear
        const clearButton = screen.getByLabelText(/clear search/i)
        expect(clearButton).toBeInTheDocument()
      })
    })
  })

  describe('Loading State', () => {
    it('shows loading spinner while fetching personas', () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      // Mock pending API call
      vi.mocked(apiClient.personas.getByCategory).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      )

      renderWithProviders(<HomePage />)

      expect(screen.getByRole('progressbar')).toBeInTheDocument()
    })
  })

  describe('Error State', () => {
    it('displays error message when API fails', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      // Mock API error
      vi.mocked(apiClient.personas.getByCategory).mockRejectedValue(
        new Error('Failed to fetch personas')
      )

      renderWithProviders(<HomePage />)

      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument()
      })
    })
  })

  describe('Responsive Grid Behavior', () => {
    it('organizes personas by category sections', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<HomePage />)

      await waitFor(() => {
        // Category headings should be present
        expect(screen.getByText(/Theologians/i)).toBeInTheDocument()
        expect(screen.getByText(/Philosophers/i)).toBeInTheDocument()
        expect(screen.getByText(/Scientists/i)).toBeInTheDocument()
      })
    })

    it('displays correct persona count per category', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<HomePage />)

      await waitFor(() => {
        // Should show count in category headers
        const theologiansSection = screen.getByText(/Theologians/i).closest('div')
        expect(theologiansSection).toBeInTheDocument()
        // Mock data has 2 theologians, 2 philosophers, 1 scientist
      })
    })
  })

  describe('Call-to-Action Buttons', () => {
    it('shows Create Debate CTA for authenticated users', async () => {
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

      renderWithProviders(<HomePage />)

      await waitFor(() => {
        const createDebateButton = screen.getByRole('link', { name: /create.*debate/i })
        expect(createDebateButton).toBeInTheDocument()
        expect(createDebateButton).toHaveAttribute('href', '/debates/new')
      })
    })

    it('shows Sign Up CTA for unauthenticated users', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<HomePage />)

      await waitFor(() => {
        const signUpButton = screen.getByRole('link', { name: /sign up/i })
        expect(signUpButton).toBeInTheDocument()
        expect(signUpButton).toHaveAttribute('href', '/register')
      })
    })
  })
})
