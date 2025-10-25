'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import type { PersonasByCategory, CreateDebateRequest } from '@/types';
import {
  Container,
  Box,
  Typography,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Card,
  CardContent,
  Grid,
  CircularProgress,
  AppBar,
  Toolbar,
  Alert,
  Paper,
} from '@mui/material';

export default function NewDebatePage() {
  const router = useRouter();
  const [title, setTitle] = useState('');
  const [topic, setTopic] = useState('');
  const [selectedPersonas, setSelectedPersonas] = useState<number[]>([]);
  const [depthLevel, setDepthLevel] = useState<'introductory' | 'intermediate' | 'advanced'>('intermediate');
  const [maxRounds, setMaxRounds] = useState(5);

  const { data, isLoading } = useQuery<PersonasByCategory>({
    queryKey: ['personas', 'by_category'],
    queryFn: () => apiClient.personas.getByCategory(),
  });

  const createMutation = useMutation({
    mutationFn: (request: CreateDebateRequest) => apiClient.debates.create(request),
    onSuccess: (debate) => {
      router.push(`/debates/${debate.slug}`);
    },
  });

  const togglePersona = (id: number) => {
    setSelectedPersonas((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id]
    );
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedPersonas.length < 2) {
      alert('Please select at least 2 participants');
      return;
    }
    if (selectedPersonas.length > 15) {
      alert('Maximum 15 participants allowed');
      return;
    }

    createMutation.mutate({
      title,
      topic,
      participant_ids: selectedPersonas,
      depth_level: depthLevel,
      max_rounds: maxRounds,
    });
  };

  const allPersonas = [
    ...(data?.theologians || []),
    ...(data?.philosophers || []),
    ...(data?.scientists || []),
  ];

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
            <Button
              component={Link}
              href="/"
              color="inherit"
              sx={{
                color: 'text.secondary',
                '&:hover': {
                  color: 'text.primary',
                },
              }}
            >
              ← Back to Home
            </Button>
          </Container>
        </Toolbar>
      </AppBar>

      {/* Main Content */}
      <Container maxWidth="lg" sx={{ py: { xs: 3, md: 6 } }}>
        <Box sx={{ maxWidth: '1200px', mx: 'auto' }}>
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
          <Typography color="text.secondary" sx={{ mb: { xs: 4, md: 5 } }}>
            Choose 2-15 historical thinkers and a topic to generate a philosophical debate.
          </Typography>

          {isLoading ? (
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', py: 10 }}>
              <Box sx={{ textAlign: 'center' }}>
                <CircularProgress size={48} sx={{ mb: 2 }} />
                <Typography color="text.secondary">Loading personas...</Typography>
              </Box>
            </Box>
          ) : (
            <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: { xs: 3, md: 4 } }}>
              {/* Basic Info */}
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
                    mb: 3,
                    fontSize: { xs: '1.25rem', md: '1.5rem' },
                  }}
                >
                  Debate Details
                </Typography>

                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                  <TextField
                    id="title"
                    label="Title"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    required
                    fullWidth
                    placeholder="e.g., The Nature of Reality"
                  />

                  <TextField
                    id="topic"
                    label="Topic / Question"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    required
                    fullWidth
                    multiline
                    rows={3}
                    placeholder="e.g., What is the nature of reality? Is it fundamentally material or spiritual?"
                  />

                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <FormControl fullWidth>
                        <InputLabel id="depth-label">Depth Level</InputLabel>
                        <Select
                          labelId="depth-label"
                          id="depth"
                          value={depthLevel}
                          label="Depth Level"
                          onChange={(e) => setDepthLevel(e.target.value as any)}
                        >
                          <MenuItem value="introductory">Introductory</MenuItem>
                          <MenuItem value="intermediate">Intermediate</MenuItem>
                          <MenuItem value="advanced">Advanced</MenuItem>
                        </Select>
                      </FormControl>
                    </Grid>

                    <Grid item xs={12} md={6}>
                      <TextField
                        id="rounds"
                        label="Max Rounds"
                        type="number"
                        value={maxRounds}
                        onChange={(e) => setMaxRounds(parseInt(e.target.value))}
                        fullWidth
                        inputProps={{
                          min: 1,
                          max: 20,
                        }}
                      />
                    </Grid>
                  </Grid>
                </Box>
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
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                  Selected: {selectedPersonas.length} / 15 (minimum 2 required)
                </Typography>

                <Grid container spacing={{ xs: 1.5, md: 2 }}>
                  {allPersonas.map((persona) => (
                    <Grid item key={persona.id} xs={6} sm={4} md={3} lg={2.4}>
                      <Card
                        onClick={() => togglePersona(persona.id)}
                        sx={{
                          cursor: 'pointer',
                          transition: 'all 0.2s',
                          border: selectedPersonas.includes(persona.id) ? 2 : 1,
                          borderColor: selectedPersonas.includes(persona.id) ? 'primary.main' : 'divider',
                          bgcolor: selectedPersonas.includes(persona.id) ? 'rgba(79, 70, 229, 0.04)' : 'background.paper',
                          boxShadow: selectedPersonas.includes(persona.id) ? 2 : 0,
                          '&:hover': {
                            borderColor: selectedPersonas.includes(persona.id) ? 'primary.main' : 'grey.400',
                            boxShadow: 1,
                          },
                        }}
                      >
                        <CardContent
                          sx={{
                            p: { xs: 1.5, md: 2 },
                            '&:last-child': { pb: { xs: 1.5, md: 2 } },
                          }}
                        >
                          <Typography
                            variant="body2"
                            sx={{
                              fontWeight: 600,
                              fontSize: { xs: '0.875rem', md: '0.875rem' },
                              color: 'text.primary',
                            }}
                          >
                            {persona.name}
                          </Typography>
                          <Typography
                            variant="caption"
                            color="text.secondary"
                            sx={{
                              mt: 0.5,
                              display: 'block',
                              fontSize: { xs: '0.75rem', md: '0.75rem' },
                            }}
                          >
                            {persona.era}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </Paper>

              {/* Submit */}
              <Box sx={{ display: 'flex', gap: 2, flexDirection: { xs: 'column', sm: 'row' } }}>
                <Button
                  type="submit"
                  variant="contained"
                  disabled={createMutation.isPending || selectedPersonas.length < 2}
                  sx={{
                    flex: { xs: 'auto', sm: 1 },
                    py: 1.5,
                    fontSize: { xs: '1rem', md: '1rem' },
                    fontWeight: 500,
                  }}
                >
                  {createMutation.isPending ? 'Creating...' : 'Create Debate'}
                </Button>
                <Button
                  component={Link}
                  href="/"
                  variant="outlined"
                  color="inherit"
                  sx={{
                    py: 1.5,
                    px: 3,
                    fontSize: { xs: '1rem', md: '1rem' },
                    color: 'text.secondary',
                    borderColor: 'divider',
                    '&:hover': {
                      borderColor: 'grey.400',
                      bgcolor: 'grey.50',
                    },
                  }}
                >
                  Cancel
                </Button>
              </Box>

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
