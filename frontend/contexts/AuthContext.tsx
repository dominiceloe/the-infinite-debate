'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import type {
  User,
  AuthContextType,
  RegisterRequest,
  RegisterResponse,
} from '@/types/auth';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api';

// Create axios instance with credentials enabled
const authApi = axios.create({
  baseURL: API_URL,
  withCredentials: true, // Enable cookies
  headers: {
    'Content-Type': 'application/json',
  },
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  // Fetch user profile (checks if user is authenticated via cookie)
  const fetchUserProfile = useCallback(async (): Promise<User | null> => {
    try {
      const response = await authApi.get<User>('/auth/profile/');
      return response.data;
    } catch (error) {
      console.error('Error fetching user profile:', error);
      return null;
    }
  }, []);

  // Initialize auth state by checking for valid session
  useEffect(() => {
    const initAuth = async () => {
      // Try to fetch user profile - if cookies exist and are valid, this will succeed
      const userData = await fetchUserProfile();

      if (userData) {
        setUser(userData);
      }

      setIsLoading(false);
    };

    initAuth();
  }, [fetchUserProfile]);

  // Login function
  const login = useCallback(async (username: string, password: string) => {
    try {
      const response = await authApi.post<{ user: User; message: string }>('/auth/cookie-login/', {
        username,
        password,
      });

      // Cookies are set automatically by backend
      const { user: userData } = response.data;

      // Update user state
      setUser(userData);

      // Redirect to homepage
      router.push('/');
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const message = error.response?.data?.error || error.response?.data?.detail || 'Login failed. Please check your credentials.';
        throw new Error(message);
      }
      throw new Error('An unexpected error occurred during login.');
    }
  }, [router]);

  // Register function
  const register = useCallback(async (data: RegisterRequest) => {
    try {
      await authApi.post<RegisterResponse>('/auth/register/', data);

      // After successful registration, log the user in
      await login(data.username, data.password);
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const errors = error.response?.data;
        if (errors && typeof errors === 'object') {
          // Extract error messages from validation errors
          const errorMessages = Object.entries(errors)
            .map(([, messages]) => {
              if (Array.isArray(messages)) {
                return messages.join(' ');
              }
              return String(messages);
            })
            .join(' ');
          throw new Error(errorMessages);
        }
        throw new Error('Registration failed. Please try again.');
      }
      throw new Error('An unexpected error occurred during registration.');
    }
  }, [login]);

  // Logout function
  const logout = useCallback(async () => {
    // Call logout endpoint to blacklist refresh token and clear cookies
    try {
      await authApi.post('/auth/cookie-logout/');
    } catch (error) {
      console.error('Error during logout:', error);
      // Continue with local cleanup even if API call fails
    }

    // Clear local state
    setUser(null);

    // Redirect to homepage
    router.push('/');
  }, [router]);

  // Refresh user profile (useful after updating profile or credits change)
  const refreshUser = useCallback(async () => {
    const userData = await fetchUserProfile();
    if (userData) {
      setUser(userData);
    }
  }, [fetchUserProfile]);

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// Custom hook to use auth context
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
