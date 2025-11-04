// Authentication types based on backend API responses

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  email_verified: boolean;
  subscription_tier: 'trial' | 'starter' | 'pro' | 'enterprise';
  subscription_status: 'active' | 'expired' | 'cancelled';
  credits_remaining: number;
  credits_reset_date: string | null;
  trial_start_date: string | null;
  trial_end_date: string | null;
  is_trial_expired: boolean;
  is_on_trial: boolean;
  is_paid_subscriber: boolean;
  days_until_trial_end: number | null;
  days_until_credit_reset: number | null;
  created_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  password_confirm: string;
  payment_method_id?: string;  // Beta: Optional - no credit card required for trial
  first_name?: string;
  last_name?: string;
}

export interface RegisterResponse {
  user: User;
  message: string;
}

export interface RefreshTokenRequest {
  refresh: string;
}

export interface RefreshTokenResponse {
  access: string;
  refresh: string;
}

export interface SubscriptionStatus {
  tier: 'trial' | 'starter' | 'pro' | 'enterprise';
  status: 'active' | 'expired' | 'cancelled';
  credits_remaining: number;
  credits_reset_date: string | null;
  is_trial: boolean;
  trial_end_date: string | null;
  is_trial_expired: boolean;
  days_until_trial_end?: number;
  days_until_credit_reset?: number;
  can_create_debates: boolean;
}

export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}
