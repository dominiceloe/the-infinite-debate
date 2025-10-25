'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import Link from 'next/link';
import type { Debate, PaginatedResponse } from '@/types';
import {
  Container,
  Box,
  Typography,
  Button,
  Card,
  CardActionArea,
  CircularProgress,
  AppBar,
  Toolbar,
  Chip,
  Alert,
  AlertTitle,
} from '@mui/material';

export default function DebatesListPage() {
  const { data, isLoading, error } = useQuery<PaginatedResponse<Debate>>({
    queryKey: ['debates'],
    queryFn: () => apiClient.debates.list(),
  });

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(to bottom right, #eef2ff, #ffffff, #faf5ff)',
      }}
    >
      {/* Header */}
      <AppBar position="sticky" color="transparent">
        <Toolbar>
          <Container maxWidth="lg" sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', px: { xs: 2, sm: 3 } }}>
            <Typography
              component={Link}
              href="/"
              variant="h5"
              sx={{
                fontWeight: 700,
                background: 'linear-gradient(to right, #4f46e5, #9333ea)',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                textDecoration: 'none',
                fontSize: { xs: '1.5rem', md: '1.875rem' },
              }}
            >
              Philosophical Debates
            </Typography>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                component={Link}
                href="/debates/new"
                variant="contained"
                sx={{ px: 3, py: 1.5, fontWeight: 500 }}
              >
                Create Debate
              </Button>
              <Button
                component={Link}
                href="/"
                variant="text"
                sx={{ color: 'text.secondary', '&:hover': { color: 'text.primary' } }}
              >
                ← Back to Home
              </Button>
            </Box>
          </Container>
        </Toolbar>
      </AppBar>

      {/* Main Content */}
      <Container maxWidth="lg" sx={{ py: { xs: 4, md: 6 } }}>
        <Box sx={{ maxWidth: '1152px', mx: 'auto' }}>
          <Typography variant="h1" sx={{ fontWeight: 700, color: 'text.primary', mb: 1 }}>
            All Debates
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
            Browse and view philosophical debates between historical thinkers.
          </Typography>

          {isLoading ? (
            <Box sx={{ textAlign: 'center', py: 10 }}>
              <CircularProgress size={48} sx={{ mb: 2 }} />
              <Typography color="text.secondary">Loading debates...</Typography>
            </Box>
          ) : error ? (
            <Alert severity="error" sx={{ borderRadius: 2 }}>
              <AlertTitle sx={{ fontWeight: 600 }}>Error Loading Debates</AlertTitle>
              {error.message}
            </Alert>
          ) : !data?.results || data.results.length === 0 ? (
            <Card sx={{ p: 6, textAlign: 'center' }}>
              <Typography color="text.secondary" sx={{ mb: 2 }}>
                No debates yet. Create your first one!
              </Typography>
              <Button
                component={Link}
                href="/debates/new"
                variant="contained"
                sx={{ px: 4, py: 2, fontWeight: 500 }}
              >
                Create Debate
              </Button>
            </Card>
          ) : (
            <>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {data.results.map((debate) => (
                  <DebateCard key={debate.id} debate={debate} />
                ))}
              </Box>

              {/* Pagination */}
              {(data.next || data.previous) && (
                <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mt: 4 }}>
                  {data.previous && (
                    <Button
                      variant="outlined"
                      sx={{
                        px: 3,
                        py: 1.5,
                        color: 'text.secondary',
                        borderColor: 'divider',
                        '&:hover': {
                          bgcolor: 'grey.50',
                          borderColor: 'divider',
                        },
                      }}
                    >
                      Previous
                    </Button>
                  )}
                  {data.next && (
                    <Button
                      variant="outlined"
                      sx={{
                        px: 3,
                        py: 1.5,
                        color: 'text.secondary',
                        borderColor: 'divider',
                        '&:hover': {
                          bgcolor: 'grey.50',
                          borderColor: 'divider',
                        },
                      }}
                    >
                      Next
                    </Button>
                  )}
                </Box>
              )}
            </>
          )}
        </Box>
      </Container>
    </Box>
  );
}

function DebateCard({ debate }: { debate: Debate }) {
  const statusColors = {
    pending: { bgcolor: '#f3f4f6', color: '#374151' },
    generating: { bgcolor: '#dbeafe', color: '#1e40af' },
    completed: { bgcolor: '#dcfce7', color: '#166534' },
    failed: { bgcolor: '#fee2e2', color: '#991b1b' },
  };

  const statusColor = statusColors[debate.status as keyof typeof statusColors] || statusColors.pending;

  return (
    <Card
      sx={{
        transition: 'all 0.2s ease-in-out',
        '&:hover': {
          borderColor: '#c7d2fe',
          boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
        },
      }}
    >
      <CardActionArea component={Link} href={`/debates/${debate.slug}`} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 1.5 }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h5" sx={{ fontWeight: 700, color: 'text.primary', mb: 0.5 }}>
              {debate.title}
            </Typography>
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                display: '-webkit-box',
                WebkitLineClamp: 2,
                WebkitBoxOrient: 'vertical',
              }}
            >
              {debate.topic}
            </Typography>
          </Box>
          <Chip
            label={debate.status}
            size="small"
            sx={{
              ml: 2,
              bgcolor: statusColor.bgcolor,
              color: statusColor.color,
              fontWeight: 500,
              fontSize: '0.875rem',
              whiteSpace: 'nowrap',
            }}
          />
        </Box>

        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, fontSize: '0.875rem', color: 'text.secondary' }}>
          <Box>
            <Typography component="span" sx={{ fontWeight: 500 }}>Participants:</Typography>{' '}
            {debate.participant_names || `${debate.participant_count} thinkers`}
          </Box>
          <Box>
            <Typography component="span" sx={{ fontWeight: 500 }}>Rounds:</Typography>{' '}
            {debate.rounds_completed}/{debate.max_rounds}
          </Box>
          <Box>
            <Typography component="span" sx={{ fontWeight: 500 }}>Created:</Typography>{' '}
            {new Date(debate.created_at).toLocaleDateString()}
          </Box>
        </Box>
      </CardActionArea>
    </Card>
  );
}
