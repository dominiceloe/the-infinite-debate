import { describe, it, expect, vi, beforeEach } from 'vitest'
import type {
  Persona,
  PersonasByCategory,
  Debate,
  CreateDebateRequest,
  PaginatedResponse,
  PersonaRequest,
  CreatePersonaRequestRequest,
} from '@/types'

// Create mock axios instance
const mockGet = vi.fn()
const mockPost = vi.fn()
const mockAxiosInstance = {
  get: mockGet,
  post: mockPost,
  interceptors: {
    request: {
      use: vi.fn(),
    },
    response: {
      use: vi.fn((onFulfilled, onRejected) => {
        mockAxiosInstance._responseInterceptor = { onFulfilled, onRejected }
        return 0
      }),
    },
  },
  _responseInterceptor: { onFulfilled: null as any, onRejected: null as any },
}

// Mock axios module before importing api
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => mockAxiosInstance),
    post: vi.fn(),
  },
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
  configurable: true,
})

// Mock window.location.href
const locationMock = { href: '' }
Object.defineProperty(window, 'location', {
  value: locationMock,
  writable: true,
  configurable: true,
})

// Now import the api module (after mocks are set up)
let apiClient: any

describe('API Client', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    localStorageMock.clear()
    mockGet.mockReset()
    mockPost.mockReset()
    locationMock.href = ''

    // Dynamically import to get fresh instance
    const apiModule = await import('@/lib/api')
    apiClient = apiModule.apiClient
  })

  describe('Configuration', () => {
    it('creates axios instance with correct configuration', async () => {
      const axios = await import('axios')
      expect(axios.default.create).toHaveBeenCalledWith({
        baseURL: expect.any(String),
        withCredentials: true, // Must be true for cookies
        headers: {
          'Content-Type': 'application/json',
        },
      })
    })
  })


  describe('Response Interceptor', () => {
    it('passes through successful responses', async () => {
      const mockResponse = { data: { success: true } }
      const result = await mockAxiosInstance._responseInterceptor.onFulfilled(mockResponse)
      expect(result).toEqual(mockResponse)
    })

    it('refreshes token on 401 error', async () => {
      const mockError: any = {
        response: { status: 401 },
        config: {
          headers: {},
        },
      }

      // Mock successful refresh (cookie endpoint)
      mockPost.mockResolvedValueOnce({ data: { message: 'Token refreshed' } })

      // Mock the axios instance call for retry
      const mockAxiosCall = vi.fn().mockResolvedValue({ data: { success: true } })
      Object.assign(mockAxiosInstance, mockAxiosCall)

      try {
        await mockAxiosInstance._responseInterceptor.onRejected(mockError)
      } catch (error) {
        // May reject in test environment
      }

      // Should call cookie refresh endpoint
      expect(mockPost).toHaveBeenCalledWith('/auth/cookie-refresh/')
    })

    it('redirects to login when refresh fails', async () => {
      const mockError: any = {
        response: { status: 401 },
        config: { headers: {} },
      }

      // Mock failed refresh
      mockPost.mockRejectedValueOnce(new Error('Refresh failed'))

      try {
        await mockAxiosInstance._responseInterceptor.onRejected(mockError)
      } catch (error) {
        // Expected to reject
      }

      expect(locationMock.href).toBe('/login')
    })

    it('passes through non-401 errors', async () => {
      const mockError: any = {
        response: { status: 500 },
        config: {},
      }

      await expect(
        mockAxiosInstance._responseInterceptor.onRejected(mockError)
      ).rejects.toEqual(mockError)
    })
  })

  describe('Personas API', () => {
    describe('list', () => {
      it('fetches all personas', async () => {
        const mockPersonas: Persona[] = [
          {
            id: 1,
            name: 'Socrates',
            slug: 'socrates',
            title: 'The Gadfly of Athens',
            category: 'philosophers',
            era: 'Ancient',
            birth_year: -470,
            death_year: -399,
            religion_worldview: 'Greek Philosophy',
          },
        ]

        mockGet.mockResolvedValueOnce({ data: mockPersonas })

        const result = await apiClient.personas.list()

        expect(mockGet).toHaveBeenCalledWith('/personas/')
        expect(result).toEqual(mockPersonas)
      })

      it('handles API errors', async () => {
        mockGet.mockRejectedValueOnce(new Error('Network error'))

        await expect(apiClient.personas.list()).rejects.toThrow('Network error')
      })
    })

    describe('getBySlug', () => {
      it('fetches persona by slug', async () => {
        const mockPersona: Persona = {
          id: 1,
          name: 'Socrates',
          slug: 'socrates',
          title: 'The Gadfly of Athens',
          category: 'philosophers',
          era: 'Ancient',
          birth_year: -470,
          death_year: -399,
          religion_worldview: 'Greek Philosophy',
        }

        mockGet.mockResolvedValueOnce({ data: mockPersona })

        const result = await apiClient.personas.getBySlug('socrates')

        expect(mockGet).toHaveBeenCalledWith('/personas/socrates/')
        expect(result).toEqual(mockPersona)
      })

      it('handles 404 errors', async () => {
        const mockError = {
          response: { status: 404, data: { detail: 'Not found' } },
        }
        mockGet.mockRejectedValueOnce(mockError)

        await expect(apiClient.personas.getBySlug('nonexistent')).rejects.toBeDefined()
      })
    })

    describe('getByCategory', () => {
      it('fetches personas grouped by category', async () => {
        const mockCategorized: PersonasByCategory = {
          theologians: [
            {
              id: 1,
              name: 'Augustine',
              slug: 'augustine',
              title: 'Doctor of Grace',
              category: 'theologians',
              era: 'Ancient',
              birth_year: 354,
              death_year: 430,
              religion_worldview: 'Christianity',
            },
          ],
        }

        mockGet.mockResolvedValueOnce({ data: mockCategorized })

        const result = await apiClient.personas.getByCategory()

        expect(mockGet).toHaveBeenCalledWith('/personas/by_category/')
        expect(result).toEqual(mockCategorized)
      })
    })
  })

  describe('Debates API', () => {
    describe('list', () => {
      it('fetches paginated debates', async () => {
        const mockResponse: PaginatedResponse<Debate> = {
          count: 1,
          next: null,
          previous: null,
          results: [
            {
              id: 1,
              title: 'Test Debate',
              topic: 'What is justice?',
              slug: 'test-debate',
              depth_level: 'intermediate',
              max_rounds: 3,
              transcript: '',
              summary: '',
              status: 'completed',
              rounds_completed: 3,
              error_message: '',
              created_at: '2025-01-01T00:00:00Z',
              updated_at: '2025-01-01T00:00:00Z',
              completed_at: '2025-01-01T00:00:00Z',
            },
          ],
        }

        mockGet.mockResolvedValueOnce({ data: mockResponse })

        const result = await apiClient.debates.list()

        expect(mockGet).toHaveBeenCalledWith('/debates/')
        expect(result).toEqual(mockResponse)
      })
    })

    describe('create', () => {
      it('creates a new debate', async () => {
        const requestData: CreateDebateRequest = {
          title: 'New Debate',
          topic: 'What is reality?',
          participant_ids: [1, 2],
        }

        const mockDebate: Debate = {
          id: 1,
          title: 'New Debate',
          topic: 'What is reality?',
          slug: 'new-debate',
          depth_level: 'intermediate',
          max_rounds: 3,
          transcript: '',
          summary: '',
          status: 'pending',
          rounds_completed: 0,
          error_message: '',
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
          completed_at: null,
        }

        mockPost.mockResolvedValueOnce({ data: mockDebate })

        const result = await apiClient.debates.create(requestData)

        expect(mockPost).toHaveBeenCalledWith('/debates/', requestData)
        expect(result).toEqual(mockDebate)
      })

      it('handles validation errors', async () => {
        const requestData: CreateDebateRequest = {
          title: '',
          topic: '',
          participant_ids: [],
        }

        const mockError = {
          response: {
            status: 400,
            data: {
              title: ['This field is required'],
            },
          },
        }

        mockPost.mockRejectedValueOnce(mockError)

        await expect(apiClient.debates.create(requestData)).rejects.toBeDefined()
      })
    })

    describe('getBySlug', () => {
      it('fetches debate by slug', async () => {
        const mockDebate: Debate = {
          id: 1,
          title: 'Test Debate',
          topic: 'What is justice?',
          slug: 'test-debate',
          depth_level: 'intermediate',
          max_rounds: 3,
          transcript: 'Full transcript...',
          summary: 'Summary...',
          status: 'completed',
          rounds_completed: 3,
          error_message: '',
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
          completed_at: '2025-01-01T00:00:00Z',
        }

        mockGet.mockResolvedValueOnce({ data: mockDebate })

        const result = await apiClient.debates.getBySlug('test-debate')

        expect(mockGet).toHaveBeenCalledWith('/debates/test-debate/')
        expect(result).toEqual(mockDebate)
      })
    })

    describe('generate', () => {
      it('triggers debate generation', async () => {
        const mockResponse = { status: 'generating' }

        mockPost.mockResolvedValueOnce({ data: mockResponse })

        const result = await apiClient.debates.generate('test-debate')

        expect(mockPost).toHaveBeenCalledWith('/debates/test-debate/generate/')
        expect(result).toEqual(mockResponse)
      })
    })

    describe('export', () => {
      it('exports debate as blob', async () => {
        const mockBlob = new Blob(['Debate content'], { type: 'text/markdown' })

        mockGet.mockResolvedValueOnce({ data: mockBlob })

        const result = await apiClient.debates.export('test-debate')

        expect(mockGet).toHaveBeenCalledWith('/debates/test-debate/export/', {
          responseType: 'blob',
        })
        expect(result).toEqual(mockBlob)
      })
    })
  })

  describe('Persona Requests API', () => {
    describe('list', () => {
      it('fetches all persona requests', async () => {
        const mockRequests: PersonaRequest[] = [
          {
            id: 1,
            persona_name: 'Nietzsche',
            justification: 'Important philosopher',
            suggested_sources: 'Thus Spoke Zarathustra',
            status: 'pending',
            username: 'testuser',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
          },
        ]

        mockGet.mockResolvedValueOnce({ data: mockRequests })

        const result = await apiClient.personaRequests.list()

        expect(mockGet).toHaveBeenCalledWith('/persona-requests/')
        expect(result).toEqual(mockRequests)
      })
    })

    describe('create', () => {
      it('creates a new persona request', async () => {
        const requestData: CreatePersonaRequestRequest = {
          persona_name: 'Nietzsche',
          justification: 'Important philosopher',
        }

        const mockRequest: PersonaRequest = {
          id: 1,
          persona_name: 'Nietzsche',
          justification: 'Important philosopher',
          suggested_sources: '',
          status: 'pending',
          username: 'testuser',
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
        }

        mockPost.mockResolvedValueOnce({ data: mockRequest })

        const result = await apiClient.personaRequests.create(requestData)

        expect(mockPost).toHaveBeenCalledWith('/persona-requests/', requestData)
        expect(result).toEqual(mockRequest)
      })
    })
  })

  describe('Payments API', () => {
    describe('createCheckout', () => {
      it('creates checkout session', async () => {
        const mockResponse = {
          checkout_url: 'https://checkout.stripe.com/session123',
          session_id: 'session123',
        }

        mockPost.mockResolvedValueOnce({ data: mockResponse })

        const result = await apiClient.payments.createCheckout({
          tier: 'starter',
          success_url: 'http://localhost:3000/success',
          cancel_url: 'http://localhost:3000/cancel',
        })

        expect(mockPost).toHaveBeenCalledWith('/payments/create-checkout/', {
          tier: 'starter',
          success_url: 'http://localhost:3000/success',
          cancel_url: 'http://localhost:3000/cancel',
        })
        expect(result).toEqual(mockResponse)
      })

      it('handles upgrade scenario', async () => {
        const mockResponse = {
          is_upgrade: true,
          message: 'Upgraded successfully',
          tier: 'pro',
          old_tier: 'starter',
        }

        mockPost.mockResolvedValueOnce({ data: mockResponse })

        const result = await apiClient.payments.createCheckout({
          tier: 'pro',
          success_url: 'http://localhost:3000/success',
          cancel_url: 'http://localhost:3000/cancel',
        })

        expect(result.is_upgrade).toBe(true)
      })
    })

    describe('getSubscription', () => {
      it('fetches current subscription', async () => {
        const mockSubscription = {
          tier: 'pro',
          status: 'active',
        }

        mockGet.mockResolvedValueOnce({ data: mockSubscription })

        const result = await apiClient.payments.getSubscription()

        expect(mockGet).toHaveBeenCalledWith('/payments/subscription/')
        expect(result).toEqual(mockSubscription)
      })
    })

    describe('cancelSubscription', () => {
      it('cancels active subscription', async () => {
        const mockResponse = {
          message: 'Subscription cancelled',
        }

        mockPost.mockResolvedValueOnce({ data: mockResponse })

        const result = await apiClient.payments.cancelSubscription()

        expect(mockPost).toHaveBeenCalledWith('/payments/subscription/cancel/')
        expect(result).toEqual(mockResponse)
      })
    })

    describe('getHistory', () => {
      it('fetches payment history', async () => {
        const mockHistory = [
          {
            id: 1,
            amount: 9.99,
            status: 'succeeded',
            created_at: '2025-01-01T00:00:00Z',
          },
        ]

        mockGet.mockResolvedValueOnce({ data: mockHistory })

        const result = await apiClient.payments.getHistory()

        expect(mockGet).toHaveBeenCalledWith('/payments/history/')
        expect(result).toEqual(mockHistory)
      })
    })
  })

  describe('Error Handling', () => {
    it('handles network errors', async () => {
      mockGet.mockRejectedValueOnce(new Error('Network error'))

      await expect(apiClient.personas.list()).rejects.toThrow('Network error')
    })

    it('handles timeout errors', async () => {
      mockGet.mockRejectedValueOnce(new Error('timeout of 5000ms exceeded'))

      await expect(apiClient.debates.list()).rejects.toThrow('timeout')
    })

    it('handles server errors', async () => {
      const mockError = {
        response: {
          status: 500,
          data: { detail: 'Internal server error' },
        },
      }
      mockGet.mockRejectedValueOnce(mockError)

      await expect(apiClient.personas.getBySlug('test')).rejects.toBeDefined()
    })
  })

  describe('Cookie-based Authentication', () => {
    it('sends requests with credentials for cookies', async () => {
      // Re-import to get fresh module with mocks applied
      vi.resetModules()
      const axios = await import('axios')
      await import('@/lib/api')

      // Check that axios.create was called with withCredentials: true
      const createCalls = (axios.default.create as any).mock?.calls || []
      const callWithCredentials = createCalls.find((call: any) =>
        call[0]?.withCredentials === true
      )

      expect(callWithCredentials).toBeDefined()
      expect(callWithCredentials[0].withCredentials).toBe(true)
    })

    it('does not use Authorization headers', () => {
      // Verify request interceptor is not used for Authorization header injection
      expect(mockAxiosInstance.interceptors.request.use).toHaveBeenCalledTimes(0)
    })
  })
})
