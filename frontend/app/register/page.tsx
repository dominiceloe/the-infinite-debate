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
  Paper,
} from '@mui/material';
import { loadStripe } from '@stripe/stripe-js';
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js';
import type { RegisterRequest } from '@/types/auth';
import type { StripeCardChangeEvent } from '@/types/api';
import CreditCardIcon from '@mui/icons-material/CreditCard';
import LockIcon from '@mui/icons-material/Lock';

// Initialize Stripe
const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!);

// Card Element styling
const CARD_ELEMENT_OPTIONS = {
  style: {
    base: {
      fontSize: '16px',
      color: '#424770',
      '::placeholder': {
        color: '#aab7c4',
      },
      fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    },
    invalid: {
      color: '#9e2146',
    },
  },
  hidePostalCode: false,
};

function RegisterForm() {
  const { register, isLoading: authLoading } = useAuth();
  const stripe = useStripe();
  const elements = useElements();

  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    password_confirm: '',
    first_name: '',
    last_name: '',
  });
  const [error, setError] = useState('');
  const [cardError, setCardError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [cardComplete, setCardComplete] = useState(false);

  const handleChange = (field: string) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setFormData((prev) => ({
      ...prev,
      [field]: e.target.value,
    }));
  };

  const handleCardChange = (event: StripeCardChangeEvent) => {
    setCardError(event.error ? event.error.message : '');
    setCardComplete(event.complete);
  };

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

    if (!cardComplete) {
      return 'Please enter valid card information.';
    }

    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setCardError('');

    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    if (!stripe || !elements) {
      setError('Stripe has not loaded yet. Please try again.');
      return;
    }

    setIsLoading(true);

    try {
      // Create payment method from card element
      const cardElement = elements.getElement(CardElement);
      if (!cardElement) {
        throw new Error('Card element not found');
      }

      const { error: stripeError, paymentMethod } = await stripe.createPaymentMethod({
        type: 'card',
        card: cardElement,
        billing_details: {
          name: `${formData.first_name} ${formData.last_name}`.trim() || formData.username,
          email: formData.email,
        },
      });

      if (stripeError) {
        setCardError(stripeError.message || 'Card validation failed');
        setIsLoading(false);
        return;
      }

      if (!paymentMethod) {
        throw new Error('Failed to create payment method');
      }

      // Submit registration with payment method ID
      const registerData: RegisterRequest = {
        ...formData,
        payment_method_id: paymentMethod.id,
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
            {/* Trial Info Banner - Updated */}
            <Alert severity="info" sx={{ mb: 3 }}>
              <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>
                Free 7-Day Trial
              </Typography>
              <Typography variant="caption">
                Get 15 free credits to create debates. Credit card required, but you won&apos;t be charged until trial ends.
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

              {/* Credit Card Section */}
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

              <Button
                fullWidth
                type="submit"
                variant="contained"
                size="large"
                disabled={isLoading || !stripe}
                sx={{ mb: 2, py: 1.5 }}
              >
                {isLoading ? <CircularProgress size={24} /> : 'Start Free Trial'}
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

// Wrap the form with Stripe Elements provider
export default function RegisterPage() {
  return (
    <Elements stripe={stripePromise}>
      <RegisterForm />
    </Elements>
  );
}
