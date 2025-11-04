'use client';

import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';
import {
  Container,
  Box,
  Typography,
  TextField,
  Button,
  Card,
  CardContent,
  Alert,
  CircularProgress,
  Divider,
} from '@mui/material';
import type { RegisterRequest } from '@/types/auth';

// Beta: Stripe imports removed - no credit card required for trial
// Uncomment when payment is re-enabled:
// import { loadStripe } from '@stripe/stripe-js';
// import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js';
// import type { StripeCardChangeEvent } from '@/types/api';
// import CreditCardIcon from '@mui/icons-material/CreditCard';
// import LockIcon from '@mui/icons-material/Lock';
// import { Paper } from '@mui/material';

// const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!);
// const CARD_ELEMENT_OPTIONS = { ... };

function RegisterForm() {
  const { register, isLoading: authLoading } = useAuth();
  // Beta: Stripe hooks removed - no credit card required
  // const stripe = useStripe();
  // const elements = useElements();

  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    password_confirm: '',
    first_name: '',
    last_name: '',
  });
  const [error, setError] = useState('');
  // Beta: Card-related state removed
  // const [cardError, setCardError] = useState('');
  // const [cardComplete, setCardComplete] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (field: string) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setFormData((prev) => ({
      ...prev,
      [field]: e.target.value,
    }));
  };

  // Beta: Card change handler removed
  // const handleCardChange = (event: StripeCardChangeEvent) => {
  //   setCardError(event.error ? event.error.message : '');
  //   setCardComplete(event.complete);
  // };

  const validateForm = (): string | null => {
    if (!formData.username || !formData.email || !formData.password || !formData.password_confirm) {
      return 'Please fill in all required fields.';
    }

    if (formData.username.length < 3) {
      return 'Username must be at least 3 characters long.';
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      return 'Please enter a valid email address.';
    }

    if (formData.password.length < 8) {
      return 'Password must be at least 8 characters long.';
    }

    if (formData.password !== formData.password_confirm) {
      return 'Passwords do not match.';
    }

    // Beta: No credit card required
    // if (!cardComplete) {
    //   return 'Please enter valid card information.';
    // }

    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    // Beta: cardError state removed
    // setCardError('');

    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    // Beta: Skip Stripe validation - no credit card required
    // if (!stripe || !elements) {
    //   setError('Stripe has not loaded yet. Please try again.');
    //   return;
    // }

    setIsLoading(true);

    try {
      // Beta: Skip Stripe payment method creation
      // No credit card required during registration
      // Users will add payment method when upgrading to paid tier

      // Submit registration WITHOUT payment method ID
      const registerData: RegisterRequest = {
        ...formData,
        // payment_method_id is now optional in backend
      };

      await register(registerData);
      // Navigation happens in the register function (after auto-login)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  if (authLoading) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(to bottom right, #eef2ff, #ffffff, #faf5ff)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        py: 4,
      }}
    >
      <Container maxWidth="sm">
        <Box sx={{ textAlign: 'center', mb: 4 }}>
          <Typography
            variant="h3"
            component="h1"
            sx={{
              fontWeight: 700,
              background: 'linear-gradient(to right, #4f46e5, #9333ea)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              mb: 1,
            }}
          >
            Create Account
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Start your philosophical journey today
          </Typography>
        </Box>

        <Card>
          <CardContent sx={{ p: 4 }}>
            {/* Trial Info Banner - Beta Simplification */}
            <Alert severity="success" sx={{ mb: 3 }}>
              <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>
                Free 7-Day Trial - No Credit Card Required
              </Typography>
              <Typography variant="caption">
                Get 10 free credits and create up to 2 debates per day. Upgrade anytime to Starter for unlimited debates.
              </Typography>
            </Alert>

            <form onSubmit={handleSubmit}>
              {error && (
                <Alert severity="error" sx={{ mb: 3 }}>
                  {error}
                </Alert>
              )}

              <TextField
                fullWidth
                label="Username"
                type="text"
                value={formData.username}
                onChange={handleChange('username')}
                disabled={isLoading}
                required
                autoComplete="username"
                autoFocus
                helperText="At least 3 characters"
                sx={{ mb: 2 }}
              />

              <TextField
                fullWidth
                label="Email"
                type="email"
                value={formData.email}
                onChange={handleChange('email')}
                disabled={isLoading}
                required
                autoComplete="email"
                sx={{ mb: 2 }}
              />

              <Divider sx={{ my: 2 }}>
                <Typography variant="caption" color="text.secondary">
                  Optional
                </Typography>
              </Divider>

              <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                <TextField
                  fullWidth
                  label="First Name"
                  type="text"
                  value={formData.first_name}
                  onChange={handleChange('first_name')}
                  disabled={isLoading}
                  autoComplete="given-name"
                />

                <TextField
                  fullWidth
                  label="Last Name"
                  type="text"
                  value={formData.last_name}
                  onChange={handleChange('last_name')}
                  disabled={isLoading}
                  autoComplete="family-name"
                />
              </Box>

              <Divider sx={{ my: 2 }} />

              <TextField
                fullWidth
                label="Password"
                type="password"
                value={formData.password}
                onChange={handleChange('password')}
                disabled={isLoading}
                required
                autoComplete="new-password"
                helperText="At least 8 characters"
                sx={{ mb: 2 }}
              />

              <TextField
                fullWidth
                label="Confirm Password"
                type="password"
                value={formData.password_confirm}
                onChange={handleChange('password_confirm')}
                disabled={isLoading}
                required
                autoComplete="new-password"
                sx={{ mb: 3 }}
              />

              {/* Beta: Credit Card Section REMOVED - No payment required for trial */}
              {/* Uncomment to re-enable post-beta:
              <Divider sx={{ my: 3 }}>
                <Typography variant="caption" color="text.secondary">
                  Payment Information
                </Typography>
              </Divider>

              <Paper
                variant="outlined"
                sx={{
                  p: 2,
                  mb: 1,
                  borderRadius: 1,
                  borderColor: cardError ? 'error.main' : 'divider',
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1.5 }}>
                  <CreditCardIcon sx={{ mr: 1, color: 'text.secondary', fontSize: 20 }} />
                  <Typography variant="body2" color="text.secondary">
                    Credit or Debit Card
                  </Typography>
                </Box>
                <CardElement
                  options={CARD_ELEMENT_OPTIONS}
                  onChange={handleCardChange}
                />
              </Paper>

              {cardError && (
                <Typography variant="caption" color="error" sx={{ display: 'block', mb: 2 }}>
                  {cardError}
                </Typography>
              )}

              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3, mt: 1 }}>
                <LockIcon sx={{ fontSize: 14, mr: 0.5, color: 'text.secondary' }} />
                <Typography variant="caption" color="text.secondary">
                  Your payment information is encrypted and secure. You won&apos;t be charged until your 7-day trial ends.
                </Typography>
              </Box>
              */}

              <Button
                fullWidth
                type="submit"
                variant="contained"
                size="large"
                disabled={isLoading}
                sx={{ mb: 2, py: 1.5 }}
              >
                {isLoading ? <CircularProgress size={24} /> : 'Create Free Account'}
              </Button>

              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="body2" color="text.secondary">
                  Already have an account?{' '}
                  <Link
                    href="/login"
                    style={{
                      color: '#4f46e5',
                      textDecoration: 'none',
                      fontWeight: 600,
                    }}
                  >
                    Sign in
                  </Link>
                </Typography>
              </Box>
            </form>
          </CardContent>
        </Card>

        <Box sx={{ textAlign: 'center', mt: 3 }}>
          <Link
            href="/"
            style={{
              color: '#6b7280',
              textDecoration: 'none',
              fontSize: '0.875rem',
            }}
          >
            Back to Home
          </Link>
        </Box>
      </Container>
    </Box>
  );
}

// Beta: Stripe Elements wrapper removed - no payment required
export default function RegisterPage() {
  return <RegisterForm />;
}

// Uncomment when payment is re-enabled:
// export default function RegisterPage() {
//   return (
//     <Elements stripe={stripePromise}>
//       <RegisterForm />
//     </Elements>
//   );
// }
