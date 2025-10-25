'use client';

import React, { useState } from 'react';
import {
  Container,
  Box,
  Typography,
  Button,
  TextField,
  Alert,
  CircularProgress,
  Paper,
} from '@mui/material';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import ProtectedRoute from '@/components/ProtectedRoute';
import Header from '@/components/Header';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import type { CreatePersonaRequestRequest } from '@/types';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

function RequestPersonaPageContent() {
  const { user } = useAuth();
  const [personaName, setPersonaName] = useState('');
  const [justification, setJustification] = useState('');
  const [suggestedSources, setSuggestedSources] = useState('');
  const [showSuccess, setShowSuccess] = useState(false);

  const createMutation = useMutation({
    mutationFn: (data: CreatePersonaRequestRequest) => apiClient.personaRequests.create(data),
    onSuccess: () => {
      setShowSuccess(true);
      // Clear form
      setPersonaName('');
      setJustification('');
      setSuggestedSources('');
      // Scroll to top to show success message
      window.scrollTo({ top: 0, behavior: 'smooth' });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate({
      persona_name: personaName,
      justification: justification,
      suggested_sources: suggestedSources || undefined,
    });
  };

  if (!user) {
    return null;
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(to bottom right, #eef2ff, #ffffff, #faf5ff)',
      }}
    >
      <Header backTo="/" backLabel="Back to Home" />

      {/* Main Content */}
      <Container maxWidth="md" sx={{ py: { xs: 4, md: 6 }, px: { xs: 2, sm: 3 } }}>
        {/* Page Title */}
        <Box sx={{ mb: 4 }}>
          <Typography
            variant="h3"
            sx={{
              fontWeight: 700,
              mb: 1,
              fontSize: { xs: '1.75rem', md: '2.5rem' },
            }}
          >
            Request a New Persona
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Suggest a historical figure, philosopher, or thinker you&apos;d like to see added to the platform.
          </Typography>
        </Box>

        {/* Success Message */}
        {showSuccess && (
          <Alert
            severity="success"
            icon={<CheckCircleIcon />}
            sx={{ mb: 3 }}
            onClose={() => setShowSuccess(false)}
          >
            <Typography variant="body1" sx={{ fontWeight: 600, mb: 0.5 }}>
              Request submitted successfully!
            </Typography>
            <Typography variant="body2">
              We&apos;ll review your suggestion and notify you if it&apos;s approved.{' '}
              <Link href="/my-requests" style={{ color: 'inherit', fontWeight: 600 }}>
                View all your requests
              </Link>
            </Typography>
          </Alert>
        )}

        {/* Error Message */}
        {createMutation.isError && (
          <Alert severity="error" sx={{ mb: 3 }}>
            <Typography variant="body1" sx={{ fontWeight: 600, mb: 0.5 }}>
              Error submitting request
            </Typography>
            <Typography variant="body2">
              {String(createMutation.error)}
            </Typography>
          </Alert>
        )}

        {/* Request Form */}
        <Paper
          elevation={0}
          sx={{
            p: { xs: 3, md: 4 },
            border: 1,
            borderColor: 'divider',
            borderRadius: 2,
          }}
        >
          <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <TextField
              id="persona-name"
              label="Persona Name"
              value={personaName}
              onChange={(e) => setPersonaName(e.target.value)}
              required
              fullWidth
              placeholder="e.g., Friedrich Nietzsche"
              helperText="The name of the historical figure, philosopher, or thinker"
            />

            <TextField
              id="justification"
              label="Why should this persona be added?"
              value={justification}
              onChange={(e) => setJustification(e.target.value)}
              required
              fullWidth
              multiline
              rows={5}
              placeholder="Explain the historical significance, philosophical contributions, and why debates with this persona would be valuable..."
              helperText="Please provide a detailed justification for adding this persona"
            />

            <TextField
              id="suggested-sources"
              label="Suggested Sources (Optional)"
              value={suggestedSources}
              onChange={(e) => setSuggestedSources(e.target.value)}
              fullWidth
              multiline
              rows={3}
              placeholder="Books, articles, websites, or other resources for research (optional)"
              helperText="Help us by suggesting authoritative sources about this persona"
            />

            <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
              <Button
                type="submit"
                variant="contained"
                disabled={createMutation.isPending || !personaName.trim() || !justification.trim()}
                sx={{
                  flex: 1,
                  py: 1.5,
                  fontSize: '1rem',
                  fontWeight: 600,
                }}
              >
                {createMutation.isPending ? (
                  <>
                    <CircularProgress size={20} sx={{ mr: 1 }} />
                    Submitting...
                  </>
                ) : (
                  'Submit Request'
                )}
              </Button>
              <Button
                component={Link}
                href="/my-requests"
                variant="outlined"
                sx={{
                  py: 1.5,
                  px: 3,
                  fontSize: '1rem',
                }}
              >
                View My Requests
              </Button>
            </Box>
          </Box>
        </Paper>

        {/* Info Box */}
        <Box
          sx={{
            mt: 4,
            p: 3,
            bgcolor: 'rgba(79, 70, 229, 0.04)',
            borderRadius: 2,
            border: '1px solid',
            borderColor: 'rgba(79, 70, 229, 0.2)',
          }}
        >
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 1.5 }}>
            What happens next?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            1. Our team will review your persona request
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            2. If approved, we&apos;ll research and create the persona definition
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            3. You&apos;ll be able to track the status in your requests page
          </Typography>
          <Typography variant="body2" color="text.secondary">
            4. Once completed, the persona will be available for debates!
          </Typography>
        </Box>
      </Container>

      {/* Footer */}
      <Box
        component="footer"
        sx={{
          borderTop: 1,
          borderColor: 'divider',
          mt: { xs: 6, md: 10 },
          py: { xs: 3, md: 4 },
          bgcolor: 'rgba(255, 255, 255, 0.5)',
        }}
      >
        <Container maxWidth="lg">
          <Typography variant="body2" color="text.secondary" align="center">
            Built with AI • Powered by Claude • Open to exploration
          </Typography>
        </Container>
      </Box>
    </Box>
  );
}

export default function RequestPersonaPage() {
  return (
    <ProtectedRoute>
      <RequestPersonaPageContent />
    </ProtectedRoute>
  );
}
