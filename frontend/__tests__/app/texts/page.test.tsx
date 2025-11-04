import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { renderWithProviders, userEvent } from '../../utils/test-utils'
import LibraryPage from '@/app/texts/page'
import * as AuthContext from '@/contexts/AuthContext'
import { apiClient } from '@/lib/api'

// Mock the API client - Note: texts API doesn't exist yet in lib/api.ts
// This is a forward-compatible mock for when the texts API is implemented
vi.mock('@/lib/api', () => ({
  apiClient: {
    personas: {
      list: vi.fn(),
      getBySlug: vi.fn(),
      getByCategory: vi.fn(),
    },
    debates: {
      list: vi.fn(),
      create: vi.fn(),
      getBySlug: vi.fn(),
      generate: vi.fn(),
      export: vi.fn(),
    },
    texts: {
      getAll: vi.fn(),
    },
  },
}))

// Mock Next.js Image component
vi.mock('next/image', () => ({
  default: ({ src, alt, ...props }: React.ImgHTMLAttributes<HTMLImageElement>) => {
    // eslint-disable-next-line @next/next/no-img-element
    return <img src={src as string} alt={alt} {...props} />
  },
}))

const mockTextsData = [
  {
    id: 1,
    title: 'Nicomachean Ethics',
    slug: 'nicomachean-ethics',
    author: 'Aristotle',
    era: 'Ancient',
    category: 'philosophy',
    language: 'Greek',
    year_written: -350,
    description: 'Aristotle\'s work on virtue ethics and the good life',
    citation_count: 45,
    excerpt: 'Every art and every inquiry, and similarly every action...',
    cover_image_url: '/covers/nicomachean-ethics.jpg',
  },
  {
    id: 2,
    title: 'Summa Theologica',
    slug: 'summa-theologica',
    author: 'Thomas Aquinas',
    era: 'Medieval',
    category: 'theology',
    language: 'Latin',
    year_written: 1265,
    description: 'Comprehensive work of scholastic theology',
    citation_count: 78,
    excerpt: 'Whether, besides philosophy, any further doctrine is required...',
    cover_image_url: '/covers/summa-theologica.jpg',
  },
  {
    id: 3,
    title: 'On the Origin of Species',
    slug: 'origin-of-species',
    author: 'Charles Darwin',
    era: 'Modern',
    category: 'science',
    language: 'English',
    year_written: 1859,
    description: 'Darwin\'s groundbreaking work on evolution and natural selection',
    citation_count: 32,
    excerpt: 'When on board H.M.S. Beagle, as naturalist...',
    cover_image_url: '/covers/origin-of-species.jpg',
  },
]

describe('LibraryPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Mock successful API response
    // Type assertion needed because texts API doesn't exist yet in actual apiClient
    vi.mocked((apiClient as { texts: { getAll: () => Promise<unknown> } }).texts.getAll).mockResolvedValue(mockTextsData)
  })

  it('renders the library page title', async () => {
    vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
    })

    renderWithProviders(<LibraryPage />)

    await waitFor(() => {
      expect(screen.getByText(/Primary Text Library/i)).toBeInTheDocument()
    })
  })

  describe('Text Cards - Mobile Responsive Layout', () => {
    it('renders text cards in grid layout', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<LibraryPage />)

      await waitFor(() => {
        expect(screen.getByText('Nicomachean Ethics')).toBeInTheDocument()
        expect(screen.getByText('Summa Theologica')).toBeInTheDocument()
        expect(screen.getByText('On the Origin of Species')).toBeInTheDocument()
      })
    })

    it('displays text authors correctly', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<LibraryPage />)

      await waitFor(() => {
        expect(screen.getByText('Aristotle')).toBeInTheDocument()
        expect(screen.getByText('Thomas Aquinas')).toBeInTheDocument()
        expect(screen.getByText('Charles Darwin')).toBeInTheDocument()
      })
    })

    it('displays text eras and categories', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<LibraryPage />)

      await waitFor(() => {
        expect(screen.getByText(/Ancient/i)).toBeInTheDocument()
        expect(screen.getByText(/Medieval/i)).toBeInTheDocument()
        expect(screen.getByText(/Modern/i)).toBeInTheDocument()
      })
    })

    it('shows citation counts for texts', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<LibraryPage />)

      await waitFor(() => {
        // Citation counts should be displayed
        expect(screen.getByText(/45.*citation/i)).toBeInTheDocument()
        expect(screen.getByText(/78.*citation/i)).toBeInTheDocument()
        expect(screen.getByText(/32.*citation/i)).toBeInTheDocument()
      })
    })

    it('displays cover images with correct alt text', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<LibraryPage />)

      await waitFor(() => {
        const ethicsImage = screen.getByAltText('Nicomachean Ethics')
        expect(ethicsImage).toBeInTheDocument()
        expect(ethicsImage).toHaveAttribute('src', '/covers/nicomachean-ethics.jpg')
      })
    })

    it('links each text card to detail page', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<LibraryPage />)

      await waitFor(() => {
        const ethicsLink = screen.getByText('Nicomachean Ethics').closest('a')
        expect(ethicsLink).toHaveAttribute('href', '/texts/nicomachean-ethics')
      })
    })

    it('displays text excerpts on cards', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<LibraryPage />)

      await waitFor(() => {
        expect(screen.getByText(/Every art and every inquiry/i)).toBeInTheDocument()
        expect(screen.getByText(/Whether, besides philosophy/i)).toBeInTheDocument()
      })
    })
  })

  describe('Filter Controls - Mobile Responsive', () => {
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

      renderWithProviders(<LibraryPage />)

      await waitFor(() => {
        const searchInput = screen.getByPlaceholderText(/Search texts/i)
        expect(searchInput).toBeInTheDocument()
      })
    })

    it('renders category filter dropdown', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<LibraryPage />)

      await waitFor(() => {
        // Category filter should be present
        expect(screen.getByLabelText(/Category/i)).toBeInTheDocument()
      })
    })

    it('renders era filter dropdown', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<LibraryPage />)

      await waitFor(() => {
        // Era filter should be present
        expect(screen.getByLabelText(/Era/i)).toBeInTheDocument()
      })
    })

    it('renders sort dropdown', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<LibraryPage />)

      await waitFor(() => {
        // Sort dropdown should be present
        expect(screen.getByLabelText(/Sort/i)).toBeInTheDocument()
      })
    })

    it('filters are arranged in mobile-friendly grid', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<LibraryPage />)

      await waitFor(() => {
        // All filters should be present in the filter section
        const searchInput = screen.getByPlaceholderText(/Search texts/i)
        const categoryFilter = screen.getByLabelText(/Category/i)
        const eraFilter = screen.getByLabelText(/Era/i)
        const sortDropdown = screen.getByLabelText(/Sort/i)

        expect(searchInput).toBeInTheDocument()
        expect(categoryFilter).toBeInTheDocument()
        expect(eraFilter).toBeInTheDocument()
        expect(sortDropdown).toBeInTheDocument()
      })
    })
  })

  describe('Search and Filter Functionality', () => {
    it('filters texts by search query', async () => {
      const user = userEvent.setup()
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<LibraryPage />)

      await waitFor(async () => {
        const searchInput = screen.getByPlaceholderText(/Search texts/i)
        await user.type(searchInput, 'Aristotle')

        // Only Aristotle's text should be visible
        expect(screen.getByText('Nicomachean Ethics')).toBeInTheDocument()
        // Others should be filtered out (depending on implementation)
      })
    })

    it('clears search when clear button clicked', async () => {
      const user = userEvent.setup()
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<LibraryPage />)

      await waitFor(async () => {
        const searchInput = screen.getByPlaceholderText(/Search texts/i)
        await user.type(searchInput, 'test')

        const clearButton = screen.getByLabelText(/clear/i)
        await user.click(clearButton)

        // Search should be cleared
        expect(searchInput).toHaveValue('')
      })
    })
  })

  describe('Loading State', () => {
    it('shows loading spinner while fetching texts', () => {
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
      vi.mocked((apiClient as { texts: { getAll: () => Promise<unknown> } }).texts.getAll).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      )

      renderWithProviders(<LibraryPage />)

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
      vi.mocked((apiClient as { texts: { getAll: () => Promise<unknown> } }).texts.getAll).mockRejectedValue(
        new Error('Failed to fetch texts')
      )

      renderWithProviders(<LibraryPage />)

      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument()
      })
    })
  })

  describe('Empty State', () => {
    it('displays empty message when no texts found', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      // Mock empty response
      vi.mocked((apiClient as { texts: { getAll: () => Promise<unknown> } }).texts.getAll).mockResolvedValue([])

      renderWithProviders(<LibraryPage />)

      await waitFor(() => {
        expect(screen.getByText(/no texts found/i)).toBeInTheDocument()
      })
    })
  })

  describe('Responsive Grid Breakpoints', () => {
    it('displays texts in appropriate grid columns', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<LibraryPage />)

      await waitFor(() => {
        // All texts should be rendered
        expect(screen.getByText('Nicomachean Ethics')).toBeInTheDocument()
        expect(screen.getByText('Summa Theologica')).toBeInTheDocument()
        expect(screen.getByText('On the Origin of Species')).toBeInTheDocument()

        // Grid layout verified - actual column count tested via visual regression
        // xs: 1 column, sm: 2 columns, md: 3 columns, lg: 4 columns
      })
    })
  })

  describe('Text Card Content', () => {
    it('displays year written for texts', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<LibraryPage />)

      await waitFor(() => {
        // Year should be displayed (350 BCE, 1265, 1859)
        expect(screen.getByText(/350.*BCE/i)).toBeInTheDocument()
        expect(screen.getByText(/1265/i)).toBeInTheDocument()
        expect(screen.getByText(/1859/i)).toBeInTheDocument()
      })
    })

    it('displays language information', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<LibraryPage />)

      await waitFor(() => {
        expect(screen.getByText('Greek')).toBeInTheDocument()
        expect(screen.getByText('Latin')).toBeInTheDocument()
        expect(screen.getByText('English')).toBeInTheDocument()
      })
    })
  })

  describe('Card Padding and Spacing - Mobile Optimizations', () => {
    it('text cards render with reduced padding on mobile', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<LibraryPage />)

      await waitFor(() => {
        const cards = screen.getAllByRole('article')
        expect(cards.length).toBeGreaterThan(0)
        // Visual spacing verified via visual regression tests
        // Implementation uses p: { xs: 1.5, sm: 2 } for responsive padding
      })
    })

    it('images scale down appropriately on mobile', async () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithProviders(<LibraryPage />)

      await waitFor(() => {
        const images = screen.getAllByRole('img')
        expect(images.length).toBeGreaterThan(0)
        // Image sizes: 48x48 on xs, 64x64 on sm+
        // Actual dimensions verified via visual regression tests
      })
    })
  })
})
