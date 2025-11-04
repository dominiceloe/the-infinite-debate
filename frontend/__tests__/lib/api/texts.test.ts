import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  fetchTexts,
  fetchTextBySlug,
  fetchTextSections,
  fetchTextCitations,
  fetchTextsStats,
  fetchSection,
  type TextsFilters,
} from '@/lib/api/texts'
import type { PrimaryText, TextSection, TextCitation, TextsStats, TextsListResponse } from '@/types/texts'

// Mock fetch globally
const mockFetch = vi.fn()
global.fetch = mockFetch

describe('texts API client', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('fetchTexts', () => {
    const mockResponse: TextsListResponse = {
      count: 2,
      next: null,
      previous: null,
      results: [
        {
          id: 1,
          slug: 'republic',
          title: 'The Republic',
          author: 'Plato',
          era: 'ancient',
          category: 'philosophy',
          publication_year: -380,
          original_language: 'Greek',
          description: 'Dialogue on justice',
          source_url: 'https://example.com/republic',
          citation_count: 50,
          word_count: 100000,
          reading_difficulty: 'advanced',
          is_published: true,
          processing_status: 'ready',
          section_count: 10,
          created_at: '2024-01-01T00:00:00Z',
        },
        {
          id: 2,
          slug: 'meditations',
          title: 'Meditations',
          author: 'Marcus Aurelius',
          era: 'ancient',
          category: 'philosophy',
          publication_year: 170,
          original_language: 'Greek',
          description: 'Stoic reflections',
          source_url: 'https://example.com/meditations',
          citation_count: 30,
          word_count: 50000,
          reading_difficulty: 'intermediate',
          is_published: true,
          processing_status: 'ready',
          section_count: 5,
          created_at: '2024-01-01T00:00:00Z',
        },
      ],
    }

    it('fetches texts without filters', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await fetchTexts()

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/texts/')
      )
      expect(result).toEqual(mockResponse)
    })

    it('builds query string with category filter', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      await fetchTexts({ category: 'Philosophy' })

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('category=Philosophy')
      )
    })

    it('builds query string with era filter', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      await fetchTexts({ era: 'Ancient' })

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('era=Ancient')
      )
    })

    it('builds query string with author filter', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      await fetchTexts({ author: 'Plato' })

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('author=Plato')
      )
    })

    it('builds query string with search filter', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      await fetchTexts({ search: 'justice' })

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('search=justice')
      )
    })

    it('builds query string with ordering', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      await fetchTexts({ ordering: '-year_written' })

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('ordering=-year_written')
      )
    })

    it('builds query string with page number', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      await fetchTexts({ page: 2 })

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('page=2')
      )
    })

    it('builds query string with multiple filters', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const filters: TextsFilters = {
        category: 'Philosophy',
        era: 'Ancient',
        search: 'justice',
        ordering: '-year_written',
        page: 1,
      }

      await fetchTexts(filters)

      const url = mockFetch.mock.calls[0][0] as string
      expect(url).toContain('category=Philosophy')
      expect(url).toContain('era=Ancient')
      expect(url).toContain('search=justice')
      expect(url).toContain('ordering=-year_written')
      expect(url).toContain('page=1')
    })

    it('throws error when fetch fails', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        statusText: 'Not Found',
      })

      await expect(fetchTexts()).rejects.toThrow('Failed to fetch texts: Not Found')
    })

    it('does not add query string when no filters provided', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      await fetchTexts()

      const url = mockFetch.mock.calls[0][0] as string
      expect(url).not.toContain('?')
    })

    it('skips undefined filter values', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      await fetchTexts({ category: 'philosophy', era: undefined })

      const url = mockFetch.mock.calls[0][0] as string
      expect(url).toContain('category=Philosophy')
      expect(url).not.toContain('era=')
    })
  })

  describe('fetchTextBySlug', () => {
    const mockText: PrimaryText = {
      id: 1,
      slug: 'republic',
      title: 'The Republic',
      author: 'Plato',
      era: 'ancient',
      category: 'philosophy',
      publication_year: -380,
      original_language: 'Greek',
      description: 'Dialogue on justice',
      source_url: 'https://example.com/republic',
      citation_count: 50,
      sections: [],
      word_count: 100000,
      reading_difficulty: 'advanced',
      is_published: true,
      processing_status: 'ready',
      section_count: 10,
      created_at: '2024-01-01T00:00:00Z',
    }

    it('fetches text by slug', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockText,
      })

      const result = await fetchTextBySlug('republic')

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/texts/republic/')
      )
      expect(result).toEqual(mockText)
    })

    it('throws error when text not found', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        statusText: 'Not Found',
      })

      await expect(fetchTextBySlug('nonexistent')).rejects.toThrow(
        'Failed to fetch text: Not Found'
      )
    })

    it('handles special characters in slug', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockText,
      })

      await fetchTextBySlug('some-text-with-dashes')

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/texts/some-text-with-dashes/')
      )
    })
  })

  describe('fetchTextSections', () => {
    const mockSections: TextSection[] = [
      {
        id: 1,
        section_type: 'book',
        order_index: 1,
        title: 'Book I',
        content: 'Opening dialogue',
        word_count: 1000,
        breadcrumb: 'Republic / Book I',
        created_at: '2024-01-01T00:00:00Z',
      },
      {
        id: 2,
        section_type: 'book',
        order_index: 2,
        title: 'Book II',
        content: 'Continuation',
        word_count: 1200,
        breadcrumb: 'Republic / Book II',
        created_at: '2024-01-01T00:00:00Z',
      },
    ]

    it('fetches sections for a text', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSections,
      })

      const result = await fetchTextSections('republic')

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/texts/republic/sections/')
      )
      expect(result).toEqual(mockSections)
    })

    it('throws error when sections fetch fails', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        statusText: 'Internal Server Error',
      })

      await expect(fetchTextSections('republic')).rejects.toThrow(
        'Failed to fetch sections: Internal Server Error'
      )
    })
  })

  describe('fetchTextCitations', () => {
    const mockCitations: TextCitation[] = [
      {
        id: 1,
        debate_message: 123,
        text: 1,
        text_title: 'The Republic',
        text_author: 'Plato',
        text_section: 1,
        section_breadcrumb: 'Republic / Book I',
        citation_text: 'What is justice?',
        match_confidence: 0.95,
        match_method: 'llm',
        verified: true,
        created_at: '2024-01-01T00:00:00Z',
      },
    ]

    it('fetches citations for a text', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockCitations,
      })

      const result = await fetchTextCitations('republic')

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/texts/republic/citations/')
      )
      expect(result).toEqual(mockCitations)
    })

    it('throws error when citations fetch fails', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        statusText: 'Bad Request',
      })

      await expect(fetchTextCitations('republic')).rejects.toThrow(
        'Failed to fetch citations: Bad Request'
      )
    })
  })

  describe('fetchTextsStats', () => {
    const mockStats: TextsStats = {
      total_texts: 100,
      total_words: 1000000,
      by_category: {
        philosophy: 40,
        theology: 30,
        science: 30,
      },
      by_era: {
        ancient: 25,
        medieval: 20,
        modern: 55,
      },
    }

    it('fetches library statistics', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockStats,
      })

      const result = await fetchTextsStats()

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/texts/stats/')
      )
      expect(result).toEqual(mockStats)
    })

    it('throws error when stats fetch fails', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        statusText: 'Service Unavailable',
      })

      await expect(fetchTextsStats()).rejects.toThrow(
        'Failed to fetch stats: Service Unavailable'
      )
    })
  })

  describe('fetchSection', () => {
    const mockSection: TextSection = {
      id: 123,
      section_type: 'chapter',
      order_index: 1,
      title: 'Introduction',
      content: 'Opening remarks',
      word_count: 500,
      breadcrumb: 'Text / Introduction',
      created_at: '2024-01-01T00:00:00Z',
    }

    it('fetches section by ID', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSection,
      })

      const result = await fetchSection(123)

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/sections/123/')
      )
      expect(result).toEqual(mockSection)
    })

    it('throws error when section not found', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        statusText: 'Not Found',
      })

      await expect(fetchSection(999)).rejects.toThrow(
        'Failed to fetch section: Not Found'
      )
    })

    it('handles numeric ID correctly', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSection,
      })

      await fetchSection(456)

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/sections/456/')
      )
    })
  })

  describe('error handling', () => {
    it('handles network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      await expect(fetchTexts()).rejects.toThrow('Network error')
    })

    it('handles JSON parse errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => {
          throw new Error('Invalid JSON')
        },
      })

      await expect(fetchTexts()).rejects.toThrow('Invalid JSON')
    })
  })

  describe('API URL configuration', () => {
    it('uses environment variable for API base URL', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ count: 0, results: [] }),
      })

      await fetchTexts()

      const url = mockFetch.mock.calls[0][0] as string
      // Should contain /texts/ endpoint
      expect(url).toContain('/texts/')
      // Should be a valid URL
      expect(url).toMatch(/^https?:\/\//)
    })
  })
})
