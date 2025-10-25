'use client';

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import type { Debate } from '@/types';
import ReactMarkdown from 'react-markdown';
import { useDebateSSE } from '@/lib/hooks/useDebateSSE';
import {
  Container,
  Box,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  ToggleButtonGroup,
  ToggleButton,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import TheaterComedy from '@mui/icons-material/TheaterComedy';
import Article from '@mui/icons-material/Article';
import MessageContent from '@/components/MessageContent';
import Image from 'next/image';
import DebateTheaterView from '@/components/DebateTheaterView';
import Header from '@/components/Header';

export default function DebateViewPage() {
  const params = useParams();
  const slug = params.slug as string;
  const queryClient = useQueryClient();
  const router = useRouter();

  // View mode state (theater vs transcript) - default to theater for better generation UX
  const [viewMode, setViewMode] = useState<'transcript' | 'theater'>('theater');

  // Load view preference from localStorage
  useEffect(() => {
    const savedMode = localStorage.getItem('debate-view-mode') as 'transcript' | 'theater' | null;
    if (savedMode) {
      setViewMode(savedMode);
    }
  }, []);

  // Save view preference to localStorage
  const handleViewModeChange = (
    event: React.MouseEvent<HTMLElement>,
    newMode: 'transcript' | 'theater' | null
  ) => {
    if (newMode !== null) {
      setViewMode(newMode);
      localStorage.setItem('debate-view-mode', newMode);
    }
  };

  // Fetch debate details
  const { data: debate, isLoading, error } = useQuery<Debate>({
    queryKey: ['debate', slug],
    queryFn: () => apiClient.debates.getBySlug(slug),
  });

  // Use SSE for real-time updates when debate is generating
  const { isConnected: sseConnected } = useDebateSSE({
    slug,
    enabled: debate?.status === 'generating',
    onError: (err) => {
      console.error('SSE connection error:', err);
      // SSE will automatically fall back to polling if it fails
    },
  });

  // Fallback to polling if SSE is not connected and debate is generating
  const shouldPoll = debate?.status === 'generating' && !sseConnected;

  // Enable polling as fallback
  useEffect(() => {
    if (shouldPoll) {
      const interval = setInterval(() => {
        queryClient.invalidateQueries({ queryKey: ['debate', slug] });
      }, 2000);
      return () => clearInterval(interval);
    }
  }, [shouldPoll, slug, queryClient]);

  // Generate debate mutation
  const generateMutation = useMutation({
    mutationFn: () => apiClient.debates.generate(slug),
    onSuccess: (data) => {
      // Update the query data immediately with generating status
      queryClient.setQueryData(['debate', slug], data);
      // Force refetch to start polling
      queryClient.invalidateQueries({ queryKey: ['debate', slug] });
    },
  });

  if (isLoading) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          background: 'linear-gradient(to bottom right, #eef2ff, #ffffff, #faf5ff)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Box sx={{ textAlign: 'center' }}>
          <CircularProgress size={64} thickness={4} sx={{ mb: 2 }} />
          <Typography color="text.secondary">Loading debate...</Typography>
        </Box>
      </Box>
    );
  }

  if (error || !debate) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          background: 'linear-gradient(to bottom right, #eef2ff, #ffffff, #faf5ff)',
        }}
      >
        <Container maxWidth="lg" sx={{ py: { xs: 6, md: 12 } }}>
          <Box sx={{ maxWidth: 'md', mx: 'auto' }}>
            <Alert severity="error" sx={{ mb: 2 }}>
              <Typography variant="h6" sx={{ mb: 1 }}>
                Error Loading Debate
              </Typography>
              <Typography variant="body2">
                {error?.message || 'Debate not found'}
              </Typography>
            </Alert>
            <Button
              onClick={() => router.back()}
              variant="text"
              sx={{ color: 'primary.main' }}
            >
              ← Back
            </Button>
          </Box>
        </Container>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(to bottom right, #eef2ff, #ffffff, #faf5ff)',
      }}
    >
      <Header
        backTo="/debates"
        backLabel="Back to Debates"
        breadcrumbs={[
          { label: 'Debates', href: '/debates' },
          { label: debate.title }
        ]}
      />

      {/* Main Content */}
      <Container maxWidth="lg" sx={{ py: { xs: 6, md: 12 } }}>
        <Box sx={{ maxWidth: '1024px', mx: 'auto' }}>
          {/* Title and Status */}
          <Box sx={{ mb: 4 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2, mb: 2, flexWrap: 'wrap' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap' }}>
                <Typography
                  variant="h1"
                  sx={{
                    fontSize: { xs: '1.875rem', md: '2.25rem' },
                    fontWeight: 700,
                    color: 'text.primary',
                  }}
                >
                  {debate.title}
                </Typography>
                <StatusBadge status={debate.status} />
              </Box>
              {(debate.status === 'generating' || debate.status === 'completed') && debate.messages && debate.messages.length > 0 && (
                <ToggleButtonGroup
                  value={viewMode}
                  exclusive
                  onChange={handleViewModeChange}
                  size="small"
                  sx={{
                    bgcolor: 'white',
                    '& .MuiToggleButton-root': {
                      px: { xs: 1.5, sm: 2 },
                      py: 0.5,
                      fontSize: { xs: '0.75rem', sm: '0.875rem' },
                      border: '1px solid',
                      borderColor: 'grey.300',
                      '&.Mui-selected': {
                        bgcolor: 'primary.main',
                        color: 'white',
                        '&:hover': {
                          bgcolor: 'primary.dark',
                        },
                      },
                    },
                  }}
                >
                  <ToggleButton value="transcript">
                    <Article sx={{ fontSize: '1rem', mr: 0.5 }} />
                    Transcript
                  </ToggleButton>
                  <ToggleButton value="theater">
                    <TheaterComedy sx={{ fontSize: '1rem', mr: 0.5 }} />
                    Theater
                  </ToggleButton>
                </ToggleButtonGroup>
              )}
            </Box>
            <Typography
              variant="h6"
              color="text.secondary"
              sx={{ mb: 2, fontSize: { xs: '1rem', md: '1.125rem' }, fontWeight: 400 }}
            >
              {debate.topic}
            </Typography>

            {/* Metadata */}
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, fontSize: '0.875rem', color: 'text.secondary' }}>
              <Box>
                <Typography component="span" sx={{ fontWeight: 500 }}>
                  Participants:
                </Typography>{' '}
                {debate.participant_names || debate.participants?.length}
              </Box>
              <Box>
                <Typography component="span" sx={{ fontWeight: 500 }}>
                  Depth:
                </Typography>{' '}
                {debate.depth_level}
              </Box>
              <Box>
                <Typography component="span" sx={{ fontWeight: 500 }}>
                  Rounds:
                </Typography>{' '}
                {debate.rounds_completed}/{debate.max_rounds}
              </Box>
            </Box>
          </Box>

          {/* Participants List */}
          {debate.participants && debate.participants.length > 0 && (
            <Box sx={{ mb: 4 }}>
              <Typography variant="h5" sx={{ fontWeight: 600, mb: 2 }}>
                Participants
              </Typography>
              {debate.participants.map((persona) => (
                <ParticipantAccordion key={persona.id} persona={persona} />
              ))}
            </Box>
          )}

          {/* Status-based Content */}
          {debate.status === 'pending' && (
            <PendingState debate={debate} generateMutation={generateMutation} />
          )}

          {(debate.status === 'generating' || debate.status === 'completed') && viewMode === 'theater' && debate.messages && debate.messages.length > 0 ? (
            <DebateTheaterView debate={debate} />
          ) : (
            <>
              {debate.status === 'generating' && (
                <GeneratingState debate={debate} viewMode={viewMode} />
              )}

              {debate.status === 'completed' && (
                <CompletedState debate={debate} viewMode={viewMode} />
              )}
            </>
          )}

          {debate.status === 'failed' && (
            <FailedState debate={debate} generateMutation={generateMutation} />
          )}
        </Box>
      </Container>
    </Box>
  );
}

function StatusBadge({ status }: { status: string }) {
  const statusConfig = {
    pending: { color: 'default' as const, label: 'pending' },
    generating: { color: 'info' as const, label: 'generating' },
    completed: { color: 'success' as const, label: 'completed' },
    failed: { color: 'error' as const, label: 'failed' },
  };

  const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending;

  return (
    <Chip
      label={config.label}
      color={config.color}
      size="small"
      sx={{ fontWeight: 500, textTransform: 'capitalize' }}
    />
  );
}

function PendingState({ generateMutation }: { debate: Debate; generateMutation: ReturnType<typeof useMutation> }) {
  return (
    <Card>
      <CardContent sx={{ p: { xs: 4, md: 6 }, textAlign: 'center' }}>
        <Box sx={{ maxWidth: 'md', mx: 'auto' }}>
          <Typography variant="h4" sx={{ fontWeight: 700, mb: 2 }}>
            Ready to Generate
          </Typography>
          <Typography color="text.secondary" sx={{ mb: 3 }}>
            This debate is configured and ready. Click the button below to generate the philosophical dialogue between these thinkers.
          </Typography>
          <Button
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending}
            variant="contained"
            fullWidth
            sx={{
              py: 1.5,
              fontWeight: 500,
              fontSize: '1rem',
              '&:disabled': {
                bgcolor: 'grey.400',
                cursor: 'not-allowed',
              },
            }}
          >
            {generateMutation.isPending ? 'Starting Generation...' : 'Generate Debate'}
          </Button>
          {generateMutation.isError && (
            <Alert severity="error" sx={{ mt: 2 }}>
              <Typography variant="body2">
                Error: {generateMutation.error?.message || 'Failed to start generation'}
              </Typography>
            </Alert>
          )}
        </Box>
      </CardContent>
    </Card>
  );
}

function GeneratingState({ debate }: { debate: Debate; viewMode: 'transcript' | 'theater' }) {
  // Auto-scroll to bottom when transcript updates
  React.useEffect(() => {
    if (debate.transcript) {
      window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
    }
  }, [debate.transcript]);

  return (
    <Card>
      <CardContent sx={{ p: { xs: 4, md: 6 } }}>
        {/* Show transcript immediately without disabled overlay */}
        {debate.transcript && (
          <Box sx={{ mb: 3 }}>
            <ReactMarkdown
              components={{
                h1: ({ children }) => (
                  <Typography variant="h2" sx={{ fontWeight: 700, mb: 2, mt: 0 }}>
                    {children}
                  </Typography>
                ),
                h2: ({ children }) => (
                  <Typography variant="h3" sx={{ fontWeight: 700, mt: 4, mb: 2 }}>
                    {children}
                  </Typography>
                ),
                h3: ({ children }) => (
                  <Typography
                    variant="h4"
                    sx={{
                      fontWeight: 600,
                      color: 'primary.main',
                      mt: 3,
                      mb: 1.5,
                    }}
                  >
                    {children}
                  </Typography>
                ),
                p: ({ children }) => (
                  <Typography
                    sx={{
                      color: 'text.primary',
                      mb: 2,
                      lineHeight: 1.7,
                    }}
                  >
                    {children}
                  </Typography>
                ),
                ul: ({ children }) => (
                  <Box
                    component="ul"
                    sx={{
                      pl: 3,
                      mb: 2,
                      color: 'text.primary',
                      listStyleType: 'disc',
                    }}
                  >
                    {children}
                  </Box>
                ),
                li: ({ children }) => (
                  <Typography component="li" sx={{ mb: 0.5 }}>
                    {children}
                  </Typography>
                ),
              }}
            >
              {debate.transcript}
            </ReactMarkdown>
          </Box>
        )}

        {/* Compact status indicator at bottom */}
        <Box
          sx={{
            position: 'sticky',
            bottom: 16,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 1.5,
            bgcolor: 'primary.main',
            color: 'white',
            borderRadius: 50,
            px: 3,
            py: 1.5,
            boxShadow: 3,
            mx: 'auto',
          }}
        >
          <CircularProgress size={20} thickness={5} sx={{ color: 'white' }} />
          <Typography sx={{ fontWeight: 500 }}>
            Generating... Round {debate.rounds_completed} of {debate.max_rounds}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
}

function CompletedState({ debate }: { debate: Debate; viewMode: 'transcript' | 'theater' }) {
  const messages = debate.messages || [];
  const hasMessages = messages.length > 0;
  const [exportLoading, setExportLoading] = useState(false);

  const handleExportPDF = async () => {
    setExportLoading(true);
    try {
      const blob = await apiClient.debates.export(debate.slug);

      // Create a download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${debate.slug}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export PDF:', error);
      alert('Failed to export PDF. Please try again.');
    } finally {
      setExportLoading(false);
    }
  };

  return (
    <Card>
      <CardContent sx={{ p: { xs: 4, md: 6 } }}>
        <Box sx={{ mb: 3, pb: 3, borderBottom: 1, borderColor: 'divider' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
            <Box>
              <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
                Debate Complete
              </Typography>
              <Typography color="text.secondary">
                Generated on {new Date(debate.completed_at!).toLocaleString()}
              </Typography>
            </Box>
            <Button
              onClick={handleExportPDF}
              disabled={exportLoading}
              variant="outlined"
              sx={{
                fontWeight: 500,
                px: 3,
              }}
            >
              {exportLoading ? 'Exporting...' : 'Export PDF'}
            </Button>
          </Box>
        </Box>

        {/* AI-Generated Summary */}
        {debate.summary && (
          <Box sx={{ mb: 4 }}>
            <Box
              sx={{
                bgcolor: 'primary.light',
                borderRadius: 2,
                p: 3,
                mb: 3,
                border: 2,
                borderColor: 'primary.main',
              }}
            >
              <Typography
                variant="h5"
                sx={{
                  fontWeight: 700,
                  mb: 2,
                  color: 'primary.dark',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                }}
              >
                📋 Debate Summary
              </Typography>
              <ReactMarkdown
                components={{
                  p: ({ children }) => (
                    <Typography
                      sx={{
                        color: 'text.primary',
                        mb: 2,
                        lineHeight: 1.7,
                      }}
                    >
                      {children}
                    </Typography>
                  ),
                  strong: ({ children }) => (
                    <Typography
                      component="span"
                      sx={{
                        fontWeight: 700,
                        color: 'primary.dark',
                      }}
                    >
                      {children}
                    </Typography>
                  ),
                  ul: ({ children }) => (
                    <Box
                      component="ul"
                      sx={{
                        pl: 3,
                        mb: 2,
                        color: 'text.primary',
                        listStyleType: 'disc',
                      }}
                    >
                      {children}
                    </Box>
                  ),
                  li: ({ children }) => (
                    <Typography component="li" sx={{ mb: 0.5 }}>
                      {children}
                    </Typography>
                  ),
                }}
              >
                {debate.summary}
              </ReactMarkdown>
            </Box>
          </Box>
        )}

        {/* Full Transcript */}
        <Box>
          {hasMessages ? (
            // Render individual messages with citations
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              {messages.map((msg, index) => {
                const showRoundHeader = index === 0 || msg.round_number !== messages[index - 1].round_number;

                return (
                  <Box key={msg.id}>
                    {/* Round Header */}
                    {showRoundHeader && (
                      <Typography
                        variant="h5"
                        sx={{
                          fontWeight: 700,
                          color: 'primary.main',
                          mt: index > 0 ? 3 : 0,
                          mb: 2,
                        }}
                      >
                        Round {msg.round_number}
                      </Typography>
                    )}

                    {/* Message */}
                    <Box sx={{ mb: 2 }}>
                      <Typography
                        variant="h6"
                        sx={{
                          fontWeight: 600,
                          color: 'text.primary',
                          mb: 1,
                        }}
                      >
                        {msg.persona.name}
                      </Typography>
                      <Typography
                        sx={{
                          color: 'text.primary',
                          lineHeight: 1.7,
                          whiteSpace: 'pre-wrap',
                        }}
                      >
                        <MessageContent content={msg.content} citations={msg.text_citations} />
                      </Typography>

                      {/* Citations */}
                      {msg.text_citations && msg.text_citations.length > 0 && (
                        <Box sx={{ mt: 2, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                          {msg.text_citations.map((citation) => (
                            <Link
                              key={citation.id}
                              href={`/texts/${citation.text_slug}`}
                              style={{ textDecoration: 'none' }}
                            >
                              <Chip
                                label={`📚 ${citation.text_title} by ${citation.text_author}`}
                                size="small"
                                clickable
                                sx={{
                                  bgcolor: 'rgba(34, 197, 94, 0.1)',
                                  border: '1px solid rgba(34, 197, 94, 0.3)',
                                  color: 'rgb(22, 163, 74)',
                                  fontSize: '0.75rem',
                                  '&:hover': {
                                    bgcolor: 'rgba(34, 197, 94, 0.2)',
                                    borderColor: 'rgba(34, 197, 94, 0.5)',
                                  },
                                }}
                              />
                            </Link>
                          ))}
                        </Box>
                      )}
                    </Box>
                  </Box>
                );
              })}
            </Box>
          ) : (
            // Fallback to markdown transcript if messages not available
            <ReactMarkdown
              components={{
                h1: ({ children }) => (
                  <Typography variant="h2" sx={{ fontWeight: 700, mb: 2, mt: 0 }}>
                    {children}
                  </Typography>
                ),
                h2: ({ children }) => (
                  <Typography variant="h3" sx={{ fontWeight: 700, mt: 4, mb: 2 }}>
                    {children}
                  </Typography>
                ),
                h3: ({ children }) => (
                  <Typography
                    variant="h4"
                    sx={{
                      fontWeight: 600,
                      color: 'primary.main',
                      mt: 3,
                      mb: 1.5,
                    }}
                  >
                    {children}
                  </Typography>
                ),
                p: ({ children }) => (
                  <Typography
                    sx={{
                      color: 'text.primary',
                      mb: 2,
                      lineHeight: 1.7,
                    }}
                  >
                    {children}
                  </Typography>
                ),
                ul: ({ children }) => (
                  <Box
                    component="ul"
                    sx={{
                      pl: 3,
                      mb: 2,
                      color: 'text.primary',
                      listStyleType: 'disc',
                    }}
                  >
                    {children}
                  </Box>
                ),
                li: ({ children }) => (
                  <Typography component="li" sx={{ mb: 0.5 }}>
                    {children}
                  </Typography>
                ),
              }}
            >
              {debate.transcript}
            </ReactMarkdown>
          )}
        </Box>
      </CardContent>
    </Card>
  );
}

function FailedState({ debate, generateMutation }: { debate: Debate; generateMutation: ReturnType<typeof useMutation> }) {
  return (
    <Card sx={{ bgcolor: 'error.light', borderColor: 'error.main' }}>
      <CardContent sx={{ p: { xs: 4, md: 6 } }}>
        <Box sx={{ textAlign: 'center', maxWidth: 'md', mx: 'auto' }}>
          <Typography variant="h4" sx={{ fontWeight: 700, color: 'error.dark', mb: 2 }}>
            Generation Failed
          </Typography>
          <Typography sx={{ color: 'error.dark', mb: 3 }}>
            {debate.error_message || 'An unknown error occurred during generation.'}
          </Typography>
          <Button
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending}
            variant="contained"
            fullWidth
            sx={{
              py: 1.5,
              fontWeight: 500,
              '&:disabled': {
                bgcolor: 'grey.400',
                cursor: 'not-allowed',
              },
            }}
          >
            {generateMutation.isPending ? 'Retrying...' : 'Retry Generation'}
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
}

function ParticipantAccordion({ persona }: { persona: Debate['participants'][0] }) {
  const [imageError, setImageError] = useState(false);

  return (
    <Accordion>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
          <Typography variant="body1" sx={{ fontWeight: 600 }}>
            {persona.name}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            • {persona.era}
          </Typography>
        </Box>
      </AccordionSummary>
      <AccordionDetails>
        <Grid container spacing={3}>
          {/* Portrait */}
          <Grid size={{ xs: 12, md: 3 }}>
            <Box
              sx={{
                position: 'relative',
                width: '100%',
                paddingTop: '100%', // 1:1 square aspect ratio
                bgcolor: 'grey.100',
                borderRadius: 2,
                overflow: 'hidden',
                mb: 2,
              }}
            >
              <Image
                src={imageError ? '/portraits/default.svg' : `/portraits/${persona.portrait_image || `${persona.slug}.png`}`}
                alt={persona.name}
                fill
                style={{ objectFit: 'cover' }}
                onError={() => setImageError(true)}
              />
            </Box>

            {/* View full profile button */}
            <Button
              component={Link}
              href={`/personas/${persona.slug}`}
              variant="outlined"
              size="small"
              fullWidth
            >
              View Full Profile →
            </Button>
          </Grid>

          {/* Bio Info */}
          <Grid size={{ xs: 12, md: 9 }}>
            <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 1 }}>
              {persona.title}
            </Typography>

            {/* Brief summary from core positions (first 100 words) */}
            {persona.core_positions && (
              <Box sx={{ mb: 2 }}>
                <ReactMarkdown
                  components={{
                    p: ({ children }) => (
                      <Typography variant="body2" sx={{ mb: 1, lineHeight: 1.6, color: 'text.primary' }}>
                        {children}
                      </Typography>
                    ),
                    strong: ({ children }) => (
                      <Box component="strong" sx={{ fontWeight: 700 }}>
                        {children}
                      </Box>
                    ),
                    em: ({ children }) => (
                      <Box component="em" sx={{ fontStyle: 'italic' }}>
                        {children}
                      </Box>
                    ),
                  }}
                >
                  {persona.core_positions.split(' ').slice(0, 100).join(' ') + (persona.core_positions.split(' ').length > 100 ? '...' : '')}
                </ReactMarkdown>
              </Box>
            )}

            {/* Representative quote */}
            {persona.representative_quotes && (
              <Box
                sx={{
                  borderLeft: 3,
                  borderColor: 'primary.main',
                  pl: 2,
                  py: 1,
                  mb: 2,
                  bgcolor: 'grey.50',
                }}
              >
                <Typography variant="body2" sx={{ fontStyle: 'italic', color: 'text.secondary' }}>
                  {persona.representative_quotes.split('\n')[0]}
                </Typography>
              </Box>
            )}
          </Grid>
        </Grid>
      </AccordionDetails>
    </Accordion>
  );
}
