# HttpOnly Cookie Authentication - Frontend Integration Guide

## Overview

The Django backend now supports secure HttpOnly cookie-based JWT authentication alongside the existing localStorage-based authentication. This implementation protects against XSS attacks by storing JWT tokens in HttpOnly cookies that are not accessible to JavaScript.

## Implementation Summary

### Backend Changes

**Files Created:**
- `/backend/users/authentication.py` - Custom `CookieJWTAuthentication` class
- `/backend/users/tests/test_cookie_auth.py` - Comprehensive test suite (29 tests, all passing)

**Files Modified:**
- `/backend/users/views.py` - Added 3 new cookie-based views
- `/backend/users/urls.py` - Added 3 new endpoints
- `/backend/config/settings.py` - Updated authentication classes, CORS, and cookie settings

### New API Endpoints

All endpoints are prefixed with `/api/auth/`

#### 1. Cookie Login
```
POST /api/auth/cookie-login/

Request Body:
{
    "username": "johndoe",  // or email
    "password": "SecurePass123!"
}

Response (200 OK):
{
    "user": {
        "id": 1,
        "username": "johndoe",
        "email": "john@example.com",
        "subscription_tier": "trial",
        "credits_remaining": 15,
        ...
    },
    "message": "Login successful."
}

Sets Cookies:
- jwt_access_token (HttpOnly, Secure, SameSite=Lax, 15 min)
- jwt_refresh_token (HttpOnly, Secure, SameSite=Lax, 7 days)
```

**Important:** Tokens are NOT returned in response body - only in HttpOnly cookies.

#### 2. Cookie Logout
```
POST /api/auth/cookie-logout/

Request Body: (none - reads from cookies)

Response (200 OK):
{
    "message": "Logout successful."
}

Clears Cookies:
- jwt_access_token
- jwt_refresh_token
```

**Authentication Required:** Must be called with valid access token cookie.

#### 3. Cookie Refresh
```
POST /api/auth/cookie-refresh/

Request Body: (none - reads refresh token from cookie)

Response (200 OK):
{
    "message": "Token refreshed successfully."
}

Updates Cookies:
- jwt_access_token (new token)
- jwt_refresh_token (new token due to rotation)
```

**Token Rotation:** Old refresh token is blacklisted after successful refresh.

### Cookie Specifications

**Access Token Cookie:**
- Name: `jwt_access_token`
- Max Age: 900 seconds (15 minutes)
- HttpOnly: `true` (not accessible to JavaScript)
- Secure: `true` in production, `false` in development
- SameSite: `Lax`
- Path: `/`

**Refresh Token Cookie:**
- Name: `jwt_refresh_token`
- Max Age: 604800 seconds (7 days)
- HttpOnly: `true`
- Secure: `true` in production, `false` in development
- SameSite: `Lax`
- Path: `/`

### CORS Configuration

CORS is configured to allow credentials from:
- `http://localhost:3000` (existing frontend)
- `http://localhost:3001` (new frontend port)
- `http://127.0.0.1:3000`
- `http://127.0.0.1:3001`

**Production:** Update `CORS_ALLOWED_ORIGINS` to include `https://theinfinitedebate.com`

### Authentication Flow

The backend now supports **dual authentication**:

1. **Cookie-based (recommended):** Checks for `jwt_access_token` cookie first
2. **Header-based (fallback):** Falls back to `Authorization: Bearer <token>` header

This ensures backward compatibility with existing frontend code.

## Frontend Integration

### axios Configuration

Configure axios to send cookies with requests:

```javascript
import axios from 'axios';

const apiClient = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api',
    withCredentials: true,  // CRITICAL: Enable cookies
    headers: {
        'Content-Type': 'application/json',
    },
});

export default apiClient;
```

### Login Flow

```javascript
// Login function
async function login(username, password) {
    try {
        const response = await apiClient.post('/auth/cookie-login/', {
            username,
            password,
        });

        // Cookies are automatically set by browser
        // No need to manually store tokens

        return response.data.user;
    } catch (error) {
        console.error('Login failed:', error.response?.data);
        throw error;
    }
}
```

### Authenticated Requests

```javascript
// No need to add Authorization header - cookies are sent automatically
async function getUserProfile() {
    const response = await apiClient.get('/auth/profile/');
    return response.data;
}
```

### Logout Flow

```javascript
async function logout() {
    try {
        await apiClient.post('/auth/cookie-logout/');
        // Cookies are automatically cleared by backend
    } catch (error) {
        console.error('Logout failed:', error);
        // Clear local state anyway
    }
}
```

### Token Refresh Flow

```javascript
// Axios interceptor for automatic token refresh
apiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        // If 401 error and haven't retried yet
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            try {
                // Refresh token (reads from cookie automatically)
                await apiClient.post('/auth/cookie-refresh/');

                // Retry original request
                return apiClient(originalRequest);
            } catch (refreshError) {
                // Refresh failed - redirect to login
                window.location.href = '/login';
                return Promise.reject(refreshError);
            }
        }

        return Promise.reject(error);
    }
);
```

### Auth Context Provider

```typescript
import { createContext, useContext, useState, useEffect } from 'react';
import apiClient from '@/lib/api-client';

interface User {
    id: number;
    username: string;
    email: string;
    subscription_tier: string;
    credits_remaining: number;
}

interface AuthContextType {
    user: User | null;
    loading: boolean;
    login: (username: string, password: string) => Promise<void>;
    logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    // Check auth status on mount
    useEffect(() => {
        checkAuth();
    }, []);

    async function checkAuth() {
        try {
            const response = await apiClient.get('/auth/profile/');
            setUser(response.data);
        } catch (error) {
            setUser(null);
        } finally {
            setLoading(false);
        }
    }

    async function login(username: string, password: string) {
        const response = await apiClient.post('/auth/cookie-login/', {
            username,
            password,
        });
        setUser(response.data.user);
    }

    async function logout() {
        try {
            await apiClient.post('/auth/cookie-logout/');
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            setUser(null);
        }
    }

    return (
        <AuthContext.Provider value={{ user, loading, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider');
    }
    return context;
}
```

## Security Considerations

### XSS Protection
- ✅ Tokens stored in HttpOnly cookies (not accessible to JavaScript)
- ✅ No tokens in response body for cookie-based endpoints
- ✅ SameSite=Lax prevents CSRF attacks

### CSRF Protection
- Django's CSRF middleware is active
- SameSite=Lax provides additional protection
- For mutations, ensure CSRF token is included (if needed)

### Production Checklist
- [ ] Set `DJANGO_ENV=production` in backend
- [ ] Update `CORS_ALLOWED_ORIGINS` to include production domain
- [ ] Ensure HTTPS is enabled (cookies set to `secure=true`)
- [ ] Verify `CSRF_COOKIE_SECURE=True` in production
- [ ] Test token refresh flow
- [ ] Verify cookies are HttpOnly in browser DevTools

## Backward Compatibility

The implementation maintains full backward compatibility:

- ✅ Old `/api/auth/login/` endpoint still works (returns tokens in body)
- ✅ Old `/api/auth/logout/` endpoint still works (accepts refresh token in body)
- ✅ Old `/api/auth/refresh/` endpoint still works (accepts refresh token in body)
- ✅ Header-based authentication (`Authorization: Bearer <token>`) still works

**Migration Strategy:**
1. Deploy backend with both authentication methods
2. Update frontend to use cookie-based endpoints
3. Monitor usage and gradually phase out localStorage method
4. Eventually remove localStorage endpoints (future release)

## Testing

All tests pass (135 total in users app):
- ✅ 29 new cookie authentication tests
- ✅ 58 existing authentication tests (backward compatibility)
- ✅ 48 other user tests

**Test Coverage:**
- `users/views.py`: 96.34%
- `users/authentication.py`: 94.44%
- `users/serializers.py`: 98.84%

## Troubleshooting

### Cookies not being set

**Cause:** `withCredentials: true` missing from axios config

**Solution:**
```javascript
const apiClient = axios.create({
    baseURL: 'http://localhost:8001/api',
    withCredentials: true,  // Must be true
});
```

### CORS errors

**Cause:** Frontend origin not in `CORS_ALLOWED_ORIGINS`

**Solution:** Add frontend URL to backend settings:
```python
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3001',
    # Add your frontend URL
]
```

### 401 errors on all requests

**Cause:** Cookies not being sent with requests

**Check:**
1. Verify `withCredentials: true` in axios config
2. Check cookies in browser DevTools (Application → Cookies)
3. Ensure backend and frontend domains match CORS config

### Token refresh fails

**Cause:** Refresh token cookie missing or expired

**Solution:**
- Check if refresh token exists in cookies
- Verify token hasn't been blacklisted
- Redirect user to login page

## Example: Complete Login Component

```typescript
'use client';

import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
    const { login } = useAuth();
    const router = useRouter();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            await login(username, password);
            router.push('/debates');
        } catch (err: any) {
            setError(err.response?.data?.error || 'Login failed');
        } finally {
            setLoading(false);
        }
    }

    return (
        <form onSubmit={handleSubmit}>
            {error && <div className="error">{error}</div>}

            <input
                type="text"
                placeholder="Username or email"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
            />

            <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
            />

            <button type="submit" disabled={loading}>
                {loading ? 'Logging in...' : 'Login'}
            </button>
        </form>
    );
}
```

## Verification

After integrating the frontend:

1. **Login:** Open browser DevTools → Application → Cookies
   - Should see `jwt_access_token` and `jwt_refresh_token`
   - Both should have `HttpOnly` flag

2. **Authenticated Request:** Make request to `/api/auth/profile/`
   - Should succeed without Authorization header
   - Cookies sent automatically

3. **Logout:** Call `/api/auth/cookie-logout/`
   - Cookies should be cleared from browser
   - Subsequent requests should fail with 401

4. **Security Check:** Try to access tokens from JavaScript console:
   ```javascript
   document.cookie  // Should NOT show jwt_access_token or jwt_refresh_token
   ```

   If you can see the tokens, HttpOnly is not working correctly.

## Support

For issues or questions:
- Check test file: `/backend/users/tests/test_cookie_auth.py`
- Review implementation: `/backend/users/views.py` (lines 147-348)
- Authentication class: `/backend/users/authentication.py`
