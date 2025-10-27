'use client';

import { useState, useMemo, useCallback } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { getDebateLimits } from '@/lib/tiers';
import { useAuth } from '@/contexts/AuthContext';
import ProtectedRoute from '@/components/ProtectedRoute';
import Header from '@/components/Header';
import { useRouter } from 'next/navigation';
import type { PersonasByCategory, CreateDebateRequest } from '@/types';
import {
  Container,
  Box,
  Typography,
  CircularProgress,
  Alert,
  Paper,
} from '@mui/material';

// Extracted components
import TopicSelector from '@/components/debates/create/TopicSelector';
import PersonaSelector from '@/components/debates/create/PersonaSelector';
import SettingsForm from '@/components/debates/create/SettingsForm';
import PreviewPanel from '@/components/debates/create/PreviewPanel';

function NewDebatePageContent() {
  const { user, refreshUser } = useAuth();
  const router = useRouter();

  // Form state
  const [title, setTitle] = useState('');
  const [topic, setTopic] = useState('');
  const [selectedPersonas, setSelectedPersonas] = useState<number[]>([]);
  const [depthLevel, setDepthLevel] = useState<'introductory' | 'intermediate' | 'advanced'>('introductory');
  const [maxRounds, setMaxRounds] = useState(3);

  // Get tier-based limits
  const limits = getDebateLimits(user?.subscription_tier);

  // Fetch personas data
  const { data, isLoading } = useQuery<PersonasByCategory>({
    queryKey: ['personas', 'by_category'],
    queryFn: () => apiClient.personas.getByCategory(),
  });

  // Create debate mutation
  const createMutation = useMutation({
    mutationFn: (request: CreateDebateRequest) => apiClient.debates.create(request),
    onSuccess: async (debate) => {
      // Refresh user data to get updated credit balance
      await refreshUser();
      router.push(`/debates/${debate.slug}`);
    },
  });

  // Handlers
  const togglePersona = useCallback((id: number) => {
    setSelectedPersonas((prev) => {
      if (prev.includes(id)) {
        return prev.filter((p) => p !== id);
      }
      if (prev.length >= limits.maxParticipants) {
        return prev; // Don't add if at max
      }
      return [...prev, id];
    });
  }, [limits.maxParticipants]);

  const removePersona = useCallback((id: number) => {
    setSelectedPersonas((prev) => prev.filter((p) => p !== id));
  }, []);

  const reorderPersonas = useCallback((fromIndex: number, toIndex: number) => {
    setSelectedPersonas((prev) => {
      const newOrder = [...prev];
      const [removed] = newOrder.splice(fromIndex, 1);
      newOrder.splice(toIndex, 0, removed);
      return newOrder;
    });
  }, []);

  const clearAllPersonas = useCallback(() => {
    setSelectedPersonas([]);
  }, []);

  const handleTitleChange = useCallback((newTitle: string) => {
    setTitle(newTitle);
  }, []);

  const handleTopicChange = useCallback((newTopic: string) => {
    setTopic(newTopic);
  }, []);

  const handleDepthLevelChange = useCallback((newDepthLevel: 'introductory' | 'intermediate' | 'advanced') => {
    setDepthLevel(newDepthLevel);
  }, []);

  const handleMaxRoundsChange = useCallback((newMaxRounds: number) => {
    setMaxRounds(newMaxRounds);
  }, []);

  // Get persona details for selected personas
  const selectedPersonaDetails = useMemo(() => {
    if (!data) return [];
    const allPersonas = Object.values(data).flat();
    return selectedPersonas
      .map((id) => allPersonas.find((p) => p.id === id))
      .filter((p): p is NonNullable<typeof p> => p !== undefined);
  }, [data, selectedPersonas]);

  // Check if form is valid for submission
  const canSubmit = useMemo(() => {
    return selectedPersonas.length >= 2
      && selectedPersonas.length <= limits.maxParticipants
      && title.trim().length > 0
      && topic.trim().length > 0;
  }, [selectedPersonas.length, limits.maxParticipants, title, topic]);

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();

    if (selectedPersonas.length < 2) {
      alert('Please select at least 2 participants');
      return;
    }
    if (selectedPersonas.length > limits.maxParticipants) {
      alert(`Maximum ${limits.maxParticipants} participants allowed for your tier`);
      return;
    }

    createMutation.mutate({
      title,
      topic,
      participant_ids: selectedPersonas,
      depth_level: depthLevel,
      max_rounds: maxRounds,
    });
  }, [selectedPersonas, limits.maxParticipants, title, topic, depthLevel, maxRounds, createMutation]);

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(to bottom right, #eef2ff, #ffffff, #faf5ff)',
      }}
    >
      <Header backTo="/" backLabel="Back to Home" />

      {/* Main Content */}
      <Container maxWidth="lg" sx={{ py: { xs: 3, md: 6 }, px: { xs: 2, md: 3 } }}>
        <Box sx={{ maxWidth: { xs: '100%', md: '1200px' }, mx: 'auto' }}>
          <Typography
            variant="h3"
            component="h1"
            sx={{
              fontWeight: 700,
              mb: 2,
              fontSize: { xs: '2rem', md: '2.25rem' },
            }}
          >
            Create a Debate
          </Typography>
          <Typography color="text.secondary" sx={{ mb: 2 }}>
            Choose participants and a topic to generate a philosophical debate.
          </Typography>

          {/* Credit Balance Display */}
          <Alert severity="info" sx={{ mb: { xs: 4, md: 5 }, borderRadius: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 1 }}>
              <Box>
                <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>
                  Your Credits: {user?.credits_remaining}
                </Typography>
                <Typography variant="caption">
                  Your tier ({user?.subscription_tier}): Up to {limits.maxParticipants} participants, {limits.maxRounds} rounds max
                  {user?.subscription_tier === 'trial' && ` • Trial: ${user?.days_until_trial_end} days left`}
                </Typography>
              </Box>
            </Box>
          </Alert>

          {isLoading ? (
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', py: 10 }}>
              <Box sx={{ textAlign: 'center' }}>
                <CircularProgress size={48} sx={{ mb: 2 }} />
                <Typography color="text.secondary">Loading personas...</Typography>
              </Box>
            </Box>
          ) : (
            <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: { xs: 3, md: 4 } }}>
              {/* Topic Selector */}
              <TopicSelector
                title={title}
                topic={topic}
                onTitleChange={handleTitleChange}
                onTopicChange={handleTopicChange}
              />

              {/* Settings Form - moved up to be part of Debate Details */}
              <Paper
                elevation={0}
                sx={{
                  p: { xs: 3, md: 4 },
                  border: 1,
                  borderColor: 'divider',
                  borderRadius: 2,
                  mt: -2, // Bring closer to TopicSelector
                }}
              >
                <Typography
                  variant="h6"
                  sx={{
                    fontWeight: 600,
                    mb: 3,
                    fontSize: { xs: '1.125rem', md: '1.25rem' },
                  }}
                >
                  Debate Settings
                </Typography>
                <SettingsForm
                  depthLevel={depthLevel}
                  maxRounds={maxRounds}
                  onDepthLevelChange={handleDepthLevelChange}
                  onMaxRoundsChange={handleMaxRoundsChange}
                  allowedDepths={limits.allowedDepths}
                  maxRoundsLimit={limits.maxRounds}
                />
              </Paper>

              {/* Persona Selection */}
              <Paper
                elevation={0}
                sx={{
                  p: { xs: 3, md: 4 },
                  border: 1,
                  borderColor: 'divider',
                  borderRadius: 2,
                }}
              >
                <Typography
                  variant="h5"
                  sx={{
                    fontWeight: 600,
                    mb: 1,
                    fontSize: { xs: '1.25rem', md: '1.5rem' },
                  }}
                >
                  Select Participants
                </Typography>

                {/* Preview Panel - Selected Personas */}
                <PreviewPanel
                  selectedPersonaDetails={selectedPersonaDetails}
                  onRemovePersona={removePersona}
                  onReorderPersonas={reorderPersonas}
                  onClearAll={clearAllPersonas}
                  onSubmit={handleSubmit}
                  isSubmitting={createMutation.isPending}
                  canSubmit={canSubmit}
                />

                {/* Persona Selector */}
                <PersonaSelector
                  data={data}
                  selectedPersonas={selectedPersonas}
                  onTogglePersona={togglePersona}
                  maxParticipants={limits.maxParticipants}
                  user={user}
                />
              </Paper>

              {createMutation.isError && (
                <Alert
                  severity="error"
                  sx={{
                    borderRadius: 2,
                  }}
                >
                  Error creating debate: {String(createMutation.error)}
                </Alert>
              )}
            </Box>
          )}
        </Box>
      </Container>
    </Box>
  );
}

export default function NewDebatePage() {
  return (
    <ProtectedRoute>
      <NewDebatePageContent />
    </ProtectedRoute>
  );
}
