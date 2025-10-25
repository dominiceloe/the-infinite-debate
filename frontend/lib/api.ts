import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import type {
  Persona,
  PersonasByCategory,
  Debate,
  CreateDebateRequest,
  PaginatedResponse,
  PersonaRequest,
  CreatePersonaRequestRequest,
} from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_URL,
  withCredentials: true, // CRITICAL: Enable cookies
  headers: {
    'Content-Type': 'application/json',
  },
});

// Flag to prevent multiple refresh requests
let isRefreshing = false;
let refreshSubscribers: (() => void)[] = [];

// Subscribe to token refresh
function subscribeTokenRefresh(callback: () => void) {
  refreshSubscribers.push(callback);
}

// Notify all subscribers when token is refreshed
function onTokenRefreshed() {
  refreshSubscribers.forEach((callback) => callback());
  refreshSubscribers = [];
}

// Response interceptor to handle token refresh and rate limiting
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Handle rate limiting (429 errors)
    if (error.response?.status === 429) {
      const data = error.response.data as any;

      // Create a custom error with user-friendly message
      const throttleError = new Error(
        data.message || 'Too many requests. Please try again later.'
      ) as any;
      throttleError.isThrottled = true;
      throttleError.retryAfter = data.retry_after_display || data.retry_after_seconds;
      throttleError.retryAfterSeconds = data.retry_after_seconds;

      // Dispatch custom event for global error handling
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('api-throttled', {
          detail: {
            message: throttleError.message,
            retryAfter: throttleError.retryAfter,
            retryAfterSeconds: throttleError.retryAfterSeconds,
          }
        }));
      }

      return Promise.reject(throttleError);
    }

    // If error is 401 and we haven't retried yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // If already refreshing, wait for the refresh to complete
        return new Promise((resolve) => {
          subscribeTokenRefresh(() => {
            resolve(api(originalRequest));
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // Attempt to refresh the token (reads from cookie automatically)
        await api.post('/auth/cookie-refresh/');

        // Notify all waiting requests
        onTokenRefreshed();
        isRefreshing = false;

        // Retry the original request (with new cookie)
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed, redirect to login
        isRefreshing = false;
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// API Client
export const apiClient = {
  // Personas
  personas: {
    list: async (): Promise<Persona[]> => {
      const response = await api.get<Persona[]>('/personas/');
      return response.data;
    },

    getBySlug: async (slug: string): Promise<Persona> => {
      const response = await api.get<Persona>(`/personas/${slug}/`);
      return response.data;
    },

    getByCategory: async (): Promise<PersonasByCategory> => {
      const response = await api.get<PersonasByCategory>('/personas/by_category/');
      return response.data;
    },
  },

  // Debates
  debates: {
    list: async (): Promise<PaginatedResponse<Debate>> => {
      const response = await api.get<PaginatedResponse<Debate>>('/debates/');
      return response.data;
    },

    create: async (data: CreateDebateRequest): Promise<Debate> => {
      const response = await api.post<Debate>('/debates/', data);
      return response.data;
    },

    getBySlug: async (slug: string): Promise<Debate> => {
      const response = await api.get<Debate>(`/debates/${slug}/`);
      return response.data;
    },

    generate: async (slug: string): Promise<any> => {
      const response = await api.post(`/debates/${slug}/generate/`);
      return response.data;
    },

    export: async (slug: string): Promise<Blob> => {
      const response = await api.get(`/debates/${slug}/export/`, {
        responseType: 'blob',
      });
      return response.data;
    },
  },

  // Persona Requests
  personaRequests: {
    list: async (): Promise<PersonaRequest[]> => {
      const response = await api.get<PersonaRequest[]>('/persona-requests/');
      return response.data;
    },

    create: async (data: CreatePersonaRequestRequest): Promise<PersonaRequest> => {
      const response = await api.post<PersonaRequest>('/persona-requests/', data);
      return response.data;
    },
  },

  // Payments
  payments: {
    createCheckout: async (data: { tier: 'starter' | 'pro'; success_url: string; cancel_url: string }): Promise<{
      checkout_url?: string;
      session_id?: string;
      is_upgrade?: boolean;
      message?: string;
      tier?: string;
      old_tier?: string;
    }> => {
      const response = await api.post<{
        checkout_url?: string;
        session_id?: string;
        is_upgrade?: boolean;
        message?: string;
        tier?: string;
        old_tier?: string;
      }>('/payments/create-checkout/', data);
      return response.data;
    },

    getSubscription: async (): Promise<any> => {
      const response = await api.get('/payments/subscription/');
      return response.data;
    },

    cancelSubscription: async (): Promise<any> => {
      const response = await api.post('/payments/subscription/cancel/');
      return response.data;
    },

    getHistory: async (): Promise<any[]> => {
      const response = await api.get('/payments/history/');
      return response.data;
    },
  },
};

export default api;
