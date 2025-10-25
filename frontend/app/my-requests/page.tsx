'use client';

import React from 'react';
import {
  Container,
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Alert,
  Grid,
} from '@mui/material';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import ProtectedRoute from '@/components/ProtectedRoute';
import Header from '@/components/Header';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import type { PersonaRequest } from '@/types';
import AddIcon from '@mui/icons-material/Add';
import PendingIcon from '@mui/icons-material/Pending';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import TaskAltIcon from '@mui/icons-material/TaskAlt';

function MyRequestsPageContent() {
  const { user } = useAuth();

  const { data: requests, isLoading, isError, error } = useQuery<PersonaRequest[]>({
    queryKey: ['personaRequests'],
    queryFn: () => apiClient.personaRequests.list(),
    enabled: !!user,
  });

  if (!user) {
    return null;
  }

  // Format date helper
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  // Get status color and icon
  const getStatusInfo = (status: PersonaRequest['status']) => {
    switch (status) {
      case 'pending':
        return {
          color: 'info' as const,
          label: 'Pending Review',
          icon: <PendingIcon fontSize="small" />,
        };
      case 'approved':
        return {
          color: 'success' as const,
          label: 'Approved',
          icon: <CheckCircleIcon fontSize="small" />,
        };
      case 'rejected':
        return {
          color: 'error' as const,
          label: 'Rejected',
          icon: <CancelIcon fontSize="small" />,
        };
      case 'completed':
        return {
          color: 'success' as const,
          label: 'Completed',
          icon: <TaskAltIcon fontSize="small" />,
        };
      default:
        return {
          color: 'default' as const,
          label: status,
          icon: null,
        };
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(to bottom right, #eef2ff, #ffffff, #faf5ff)',
      }}
    >
      <Header backTo="/" backLabel="Back to Home" />

      {/* Main Content */}
      <Container maxWidth="lg" sx={{ py: { xs: 4, md: 6 }, px: { xs: 2, sm: 3 } }}>
        {/* Page Title */}
        <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 2 }}>
          <Box>
            <Typography
              variant="h3"
              sx={{
                fontWeight: 700,
                mb: 1,
                fontSize: { xs: '1.75rem', md: '2.5rem' },
              }}
            >
              My Persona Requests
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Track the status of your persona suggestions
            </Typography>
          </Box>
          <Button
            component={Link}
            href="/request-persona"
            variant="contained"
            startIcon={<AddIcon />}
            sx={{
              py: 1.5,
              px: 3,
              fontSize: '1rem',
              fontWeight: 600,
            }}
          >
            Request a Persona
          </Button>
        </Box>

        {/* Loading State */}
        {isLoading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 10 }}>
            <Box sx={{ textAlign: 'center' }}>
              <CircularProgress size={48} sx={{ mb: 2 }} />
              <Typography color="text.secondary">Loading your requests...</Typography>
            </Box>
          </Box>
        )}

        {/* Error State */}
        {isError && (
          <Alert severity="error" sx={{ mb: 3 }}>
            <Typography variant="body1" sx={{ fontWeight: 600, mb: 0.5 }}>
              Error loading requests
            </Typography>
            <Typography variant="body2">
              {String(error)}
            </Typography>
          </Alert>
        )}

        {/* Empty State */}
        {!isLoading && !isError && requests && requests.length === 0 && (
          <Card
            sx={{
              textAlign: 'center',
              py: { xs: 6, md: 10 },
              px: { xs: 3, md: 4 },
              border: '2px dashed',
              borderColor: 'divider',
              bgcolor: 'transparent',
            }}
          >
            <CardContent>
              <Typography
                variant="h5"
                sx={{
                  fontWeight: 600,
                  mb: 2,
                  color: 'text.secondary',
                }}
              >
                You haven&apos;t submitted any persona requests yet.
              </Typography>
              <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
                Help us expand the platform by suggesting historical figures, philosophers, or thinkers you&apos;d like to see added.
              </Typography>
              <Button
                component={Link}
                href="/request-persona"
                variant="contained"
                size="large"
                startIcon={<AddIcon />}
                sx={{
                  py: 1.5,
                  px: 4,
                  fontSize: '1.1rem',
                  fontWeight: 600,
                }}
              >
                Request a Persona
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Requests List */}
        {!isLoading && !isError && requests && requests.length > 0 && (
          <Grid container spacing={3}>
            {requests.map((request) => {
              const statusInfo = getStatusInfo(request.status);
              return (
                <Grid item xs={12} key={request.id}>
                  <Card
                    sx={{
                      transition: 'all 0.2s',
                      '&:hover': {
                        boxShadow: 3,
                      },
                    }}
                  >
                    <CardContent sx={{ p: { xs: 3, md: 4 } }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 2, mb: 2 }}>
                        <Box sx={{ flex: 1, minWidth: 0 }}>
                          <Typography
                            variant="h5"
                            sx={{
                              fontWeight: 700,
                              mb: 0.5,
                              fontSize: { xs: '1.25rem', md: '1.5rem' },
                            }}
                          >
                            {request.persona_name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Submitted on {formatDate(request.created_at)}
                          </Typography>
                        </Box>
                        <Chip
                          icon={statusInfo.icon}
                          label={statusInfo.label}
                          color={statusInfo.color}
                          sx={{
                            fontWeight: 600,
                            fontSize: '0.875rem',
                            height: 32,
                          }}
                        />
                      </Box>

                      <Box sx={{ mb: 2 }}>
                        <Typography
                          variant="body2"
                          sx={{
                            fontWeight: 600,
                            mb: 1,
                            color: 'text.secondary',
                          }}
                        >
                          Justification:
                        </Typography>
                        <Typography
                          variant="body1"
                          sx={{
                            color: 'text.primary',
                            whiteSpace: 'pre-wrap',
                          }}
                        >
                          {request.justification}
                        </Typography>
                      </Box>

                      {request.suggested_sources && (
                        <Box sx={{ mb: 2 }}>
                          <Typography
                            variant="body2"
                            sx={{
                              fontWeight: 600,
                              mb: 1,
                              color: 'text.secondary',
                            }}
                          >
                            Suggested Sources:
                          </Typography>
                          <Typography
                            variant="body2"
                            sx={{
                              color: 'text.secondary',
                              whiteSpace: 'pre-wrap',
                            }}
                          >
                            {request.suggested_sources}
                          </Typography>
                        </Box>
                      )}

                      <Box
                        sx={{
                          pt: 2,
                          borderTop: 1,
                          borderColor: 'divider',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          flexWrap: 'wrap',
                          gap: 1,
                        }}
                      >
                        <Typography variant="caption" color="text.secondary">
                          Last updated: {formatDate(request.updated_at)}
                        </Typography>
                        {request.status === 'completed' && (
                          <Button
                            component={Link}
                            href="/"
                            variant="outlined"
                            size="small"
                          >
                            View Persona
                          </Button>
                        )}
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              );
            })}
          </Grid>
        )}

        {/* Info Box */}
        {!isLoading && !isError && requests && requests.length > 0 && (
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
            <Typography variant="body2" sx={{ fontWeight: 600, mb: 1.5 }}>
              Request Status Guide:
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
              <Typography variant="caption" color="text.secondary">
                <strong>Pending:</strong> Your request is awaiting review by our team
              </Typography>
              <Typography variant="caption" color="text.secondary">
                <strong>Approved:</strong> Your request has been approved and is being researched
              </Typography>
              <Typography variant="caption" color="text.secondary">
                <strong>Completed:</strong> The persona has been created and is available for debates
              </Typography>
              <Typography variant="caption" color="text.secondary">
                <strong>Rejected:</strong> Your request was not approved (we may reach out with more information)
              </Typography>
            </Box>
          </Box>
        )}
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

export default function MyRequestsPage() {
  return (
    <ProtectedRoute>
      <MyRequestsPageContent />
    </ProtectedRoute>
  );
}
