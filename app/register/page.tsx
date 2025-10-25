'use client';

import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';
import type { RegisterRequest } from '@/types/auth';
import {
  Container,
  Box,
  Typography,
  TextField,
  Button,
  Alert,
  Card,
  CardContent,
} from '@mui/material';

export default function RegisterPage() {
  const { register } = useAuth();
  const [formData, setFormData] = useState<RegisterRequest>({
    username: '',
    email: '',
    password: '',
    password_confirm: '',
    first_name: '',
    last_name: '',
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (field: keyof RegisterRequest) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [field]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Validation
    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    if (formData.password !== formData.password_confirm) {
      setError('Passwords do not match');
      return;
    }

    setIsLoading(true);

    try {
      await register(formData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(to bottom right, #eef2ff, #ffffff, #faf5ff)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        py: { xs: 4, md: 8 },
      }}
    >
      <Container maxWidth="sm">
        <Card elevation={0} sx={{ border: 1, borderColor: 'divider' }}>
          <CardContent sx={{ p: { xs: 3, md: 4 } }}>
            <Box sx={{ textAlign: 'center', mb: 3 }}>
              <Typography
                variant="h4"
                component="h1"
                sx={{
                  fontWeight: 700,
                  mb: 1,
                  background: 'linear-gradient(to right, #4f46e5, #9333ea)',
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                Create Account
              </Typography>
              <Typography color="text.secondary">
                Start your philosophical journey
              </Typography>
            </Box>

            <Alert severity="info" sx={{ mb: 3 }}>
              <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>
                Start with a free trial!
              </Typography>
              <Typography variant="caption">
                Get 15 credits for 7 days to explore The Infinite Debate
              </Typography>
            </Alert>

            {error && (
              <Alert severity="error" sx={{ mb: 3 }}>
                {error}
              </Alert>
            )}

            <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <TextField
                label="Username"
                value={formData.username}
                onChange={handleChange('username')}
                required
                fullWidth
                autoComplete="username"
              />

              <TextField
                label="Email"
                type="email"
                value={formData.email}
                onChange={handleChange('email')}
                required
                fullWidth
                autoComplete="email"
              />

              <Box sx={{ display: 'flex', gap: 2 }}>
                <TextField
                  label="First Name (Optional)"
                  value={formData.first_name}
                  onChange={handleChange('first_name')}
                  fullWidth
                  autoComplete="given-name"
                />

                <TextField
                  label="Last Name (Optional)"
                  value={formData.last_name}
                  onChange={handleChange('last_name')}
                  fullWidth
                  autoComplete="family-name"
                />
              </Box>

              <TextField
                label="Password"
                type="password"
                value={formData.password}
                onChange={handleChange('password')}
                required
                fullWidth
                autoComplete="new-password"
                helperText="Minimum 8 characters"
              />

              <TextField
                label="Confirm Password"
                type="password"
                value={formData.password_confirm}
                onChange={handleChange('password_confirm')}
                required
                fullWidth
                autoComplete="new-password"
              />

              <Button
                type="submit"
                variant="contained"
                size="large"
                fullWidth
                disabled={isLoading}
                sx={{ mt: 1, py: 1.5 }}
              >
                {isLoading ? 'Creating account...' : 'Create Account'}
              </Button>
            </Box>

            <Box sx={{ mt: 3, textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                Already have an account?{' '}
                <Link href="/login" style={{ color: '#4f46e5', textDecoration: 'none', fontWeight: 500 }}>
                  Sign in
                </Link>
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </Container>
    </Box>
  );
}
