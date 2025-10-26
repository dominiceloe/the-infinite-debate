'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { getCategoryInfo, sortPersonasByTime, getPersonaEra, ERA_INFO, type Era } from '@/lib/categories';
import { hasPersonaAccess, getTierBadge } from '@/lib/tiers';
import { useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';
import Image from 'next/image';
import type { PersonasByCategory } from '@/types';
import Header from '@/components/Header';
import {
  Container,
  Box,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  CardActionArea,
  CircularProgress,
  TextField,
  InputAdornment,
  IconButton,
  Chip,
  FormControlLabel,
  Checkbox,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import ClearIcon from '@mui/icons-material/Clear';

// Rotating engaging hooks for the homepage
const ENGAGING_HOOKS = [
  // What if hypotheticals
  "What if Einstein explained relativity to Newton?",
  "What if Burke and Plato could debate about his Republic?",
  "What if Hume challenged Descartes on 'I think, therefore I am'?",
  "What if Aristotle could critique Kant's categorical imperative?",
  "What if Confucius debated Rousseau about the social contract?",
  "What if Darwin discussed natural selection with Aristotle?",
  "What if Sartre and the Stoics debated free will?",

  // Direct questions
  "Can Socrates' method withstand Nietzsche's critique?",
  "Does quantum mechanics prove Eastern philosophy right?",
  "Would Plato approve of modern democracy?",
  "Can ancient ethics solve modern dilemmas?",

  // Hypotheses/Premises
  "Hegel meets Hume: dialectics versus empiricism.",
  "The Stoics debate the Existentialists on meaning.",
  "Newton's mechanics face Einstein's spacetime.",
  "Mill's utilitarianism meets Kant's duty ethics.",

  // Provocative pairings
  "What if Beauvoir challenged Aristotle on women and virtue?",
  "What if Bohr and Einstein could finish their quantum debate?",
  "What if Kierkegaard cross-examined Hegel's Absolute?",
  "What if Aquinas encountered Darwin's Origin of Species?",

  // Cross-cultural
  "What if Laozi and Heraclitus discussed the nature of change?",
  "What if Nagarjuna debated Wittgenstein on language?",
  "What if Confucian harmony met Nietzschean power?",

  // Modern relevance
  "Can Descartes and Turing settle the AI consciousness question?",
  "What would the Epicureans say about modern anxiety?",
  "Does neuroscience vindicate Hume's theory of mind?",
];

export default function Home() {
  const { user } = useAuth();
  const [searchQuery, setSearchQuery] = React.useState('');
  const [selectedCategories, setSelectedCategories] = React.useState<string[]>([]);
  const [selectedEras, setSelectedEras] = React.useState<Era[]>([]);
  const [showOnlyAvailable, setShowOnlyAvailable] = React.useState(false);
  const [hookText] = React.useState(() =>
    ENGAGING_HOOKS[Math.floor(Math.random() * ENGAGING_HOOKS.length)]
  );

  const { data, isLoading, error } = useQuery<PersonasByCategory>({
    queryKey: ['personas', 'by_category'],
    queryFn: () => apiClient.personas.getByCategory(),
  });

  const toggleCategoryFilter = (category: string) => {
    setSelectedCategories((prev) =>
      prev.includes(category)
        ? prev.filter(c => c !== category)
        : [...prev, category]
    );
  };

  const toggleEraFilter = (era: Era) => {
    setSelectedEras((prev) =>
      prev.includes(era)
        ? prev.filter(e => e !== era)
        : [...prev, era]
    );
  };

  const clearFilters = () => {
    setSearchQuery('');
    setSelectedCategories([]);
    setSelectedEras([]);
    setShowOnlyAvailable(false);
  };

  // Filter data based on search, category selection, era, and tier access
  const filteredData = React.useMemo(() => {
    if (!data) return null;

    return Object.entries(data).reduce((acc, [categoryKey, personas]) => {
      // Filter by category selection
      if (selectedCategories.length > 0 && !selectedCategories.includes(categoryKey)) {
        return acc;
      }

      // Filter by search query, era, and tier access
      const filtered = personas.filter((persona) => {
        // Search filter
        if (searchQuery) {
          const query = searchQuery.toLowerCase();
          const matchesSearch = (
            persona.name.toLowerCase().includes(query) ||
            persona.title.toLowerCase().includes(query) ||
            persona.era.toLowerCase().includes(query)
          );
          if (!matchesSearch) return false;
        }

        // Era filter
        if (selectedEras.length > 0) {
          const personaEra = getPersonaEra(persona.birth_year);
          if (!personaEra || !selectedEras.includes(personaEra)) {
            return false;
          }
        }

        // Tier access filter
        if (showOnlyAvailable) {
          return hasPersonaAccess(user?.subscription_tier, persona.required_tier);
        }

        return true;
      });

      if (filtered.length > 0) {
        acc[categoryKey] = filtered;
      }

      return acc;
    }, {} as PersonasByCategory);
  }, [data, selectedCategories, selectedEras, searchQuery, showOnlyAvailable, user?.subscription_tier]);

  if (error) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          px: 2,
        }}
      >
        <Box sx={{ textAlign: 'center', maxWidth: 'md' }}>
          <Typography variant="h4" color="error" gutterBottom>
            Error Loading Personas
          </Typography>
          <Typography color="text.secondary" sx={{ mb: 1 }}>
            Make sure the backend server is running on port 8002
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ wordBreak: 'break-word' }}>
            {String(error)}
          </Typography>
        </Box>
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
      <Header />

      {/* Main Content */}
      <Container maxWidth="lg" sx={{ py: { xs: 3, md: 6 } }}>
        {isLoading ? (
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', py: 10 }}>
            <Box sx={{ textAlign: 'center' }}>
              <CircularProgress size={48} sx={{ mb: 2 }} />
              <Typography color="text.secondary">Loading personas...</Typography>
            </Box>
          </Box>
        ) : (
          <>
            {/* Introduction */}
            <Box sx={{ textAlign: 'center', mb: { xs: 4, md: 6 }, px: 1 }}>
              {/* Engaging question hook */}
              <Typography
                variant="body1"
                sx={{
                  fontStyle: 'italic',
                  color: 'text.secondary',
                  mb: { xs: 2, md: 3 },
                  fontSize: { xs: '0.95rem', sm: '1.05rem', md: '1.15rem' },
                  maxWidth: '900px',
                  mx: 'auto',
                }}
              >
                {hookText}
              </Typography>

              {/* Main heading */}
              <Typography
                variant="h2"
                component="h2"
                sx={{
                  fontWeight: 700,
                  mb: { xs: 1.5, md: 2 },
                  fontSize: { xs: '1.5rem', sm: '1.875rem', md: '2.25rem' },
                }}
              >
                Choose Your Thinkers
              </Typography>

              {/* Descriptive text */}
              <Typography
                variant="h6"
                color="text.secondary"
                sx={{
                  maxWidth: '2xl',
                  mx: 'auto',
                  fontSize: { xs: '1rem', sm: '1.125rem', md: '1.25rem' },
                  fontWeight: 400,
                }}
              >
                Select from {Object.values(data || {}).reduce((sum, personas) => sum + personas.length, 0)} historical figures to create philosophical debates.
              </Typography>
            </Box>

            {/* Search and Filter */}
            <Box sx={{ mb: { xs: 4, md: 5 } }}>
              {/* Search bar */}
              <TextField
                fullWidth
                placeholder="Search by name, title, or era..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                inputProps={{
                  'aria-label': 'Search personas by name, title, or era',
                }}
                slotProps={{
                  input: {
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchIcon color="action" />
                      </InputAdornment>
                    ),
                    endAdornment: searchQuery ? (
                      <InputAdornment position="end">
                        <IconButton
                          size="small"
                          onClick={() => setSearchQuery('')}
                          aria-label="Clear search"
                        >
                          <ClearIcon fontSize="small" />
                        </IconButton>
                      </InputAdornment>
                    ) : null,
                  }
                }}
                sx={{ mb: 3 }}
              />

              {/* Available to Me filter toggle - Enhanced visibility */}
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: 'center',
                  mb: 4,
                  p: 2,
                  borderRadius: 2,
                  bgcolor: showOnlyAvailable ? 'primary.50' : 'grey.50',
                  border: 1,
                  borderColor: showOnlyAvailable ? 'primary.main' : 'divider',
                  transition: 'all 0.3s ease',
                }}
                role="region"
                aria-label="Persona availability filter"
              >
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={showOnlyAvailable}
                      onChange={(e) => setShowOnlyAvailable(e.target.checked)}
                      size="medium"
                      inputProps={{
                        'aria-label': 'Show only personas available to my subscription tier',
                      }}
                    />
                  }
                  label={
                    <Box>
                      <Typography
                        variant="body1"
                        sx={{
                          fontSize: { xs: '0.95rem', md: '1.05rem' },
                          fontWeight: showOnlyAvailable ? 600 : 500,
                        }}
                      >
                        Available to Me
                      </Typography>
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        sx={{ display: 'block', mt: 0.25 }}
                      >
                        {showOnlyAvailable
                          ? `Showing personas for your ${user?.subscription_tier || 'free'} tier`
                          : 'Filter to show only accessible personas'
                        }
                      </Typography>
                    </Box>
                  }
                />
              </Box>

              {/* Filter section with visual divider */}
              <Box
                sx={{
                  pt: 3,
                  borderTop: 2,
                  borderColor: 'divider',
                }}
              >
                {/* Category filters */}
                <Box
                  sx={{ mb: 3 }}
                  role="group"
                  aria-label="Filter personas by category"
                >
                  <Typography
                    variant="subtitle2"
                    sx={{
                      display: 'block',
                      textAlign: 'center',
                      mb: 2,
                      color: 'text.primary',
                      fontWeight: 600,
                      fontSize: { xs: '0.875rem', md: '1rem' },
                    }}
                  >
                    By Category
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, justifyContent: 'center' }}>
                    {data && Object.keys(data).map((categoryKey) => {
                      const categoryInfo = getCategoryInfo(categoryKey);
                      const isSelected = selectedCategories.includes(categoryKey);
                      return (
                        <Chip
                          key={categoryKey}
                          label={categoryInfo.title}
                          onClick={() => toggleCategoryFilter(categoryKey)}
                          color={isSelected ? 'primary' : 'default'}
                          variant={isSelected ? 'filled' : 'outlined'}
                          aria-pressed={isSelected}
                          aria-label={`Filter by ${categoryInfo.title} category`}
                          sx={{
                            fontSize: { xs: '0.75rem', md: '0.875rem' },
                            '&:hover': {
                              bgcolor: isSelected ? 'primary.dark' : 'action.hover',
                            },
                            '&:focus-visible': {
                              outline: '2px solid',
                              outlineColor: 'primary.main',
                              outlineOffset: '2px',
                            },
                          }}
                        />
                      );
                    })}
                  </Box>
                </Box>

                {/* Visual divider between filter sections */}
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                  <Box sx={{ flex: 1, height: 1, bgcolor: 'divider' }} />
                  <Typography
                    variant="caption"
                    sx={{ px: 2, color: 'text.disabled', fontWeight: 500 }}
                  >
                    AND
                  </Typography>
                  <Box sx={{ flex: 1, height: 1, bgcolor: 'divider' }} />
                </Box>

                {/* Era/Time Period filters */}
                <Box
                  sx={{ mb: 2 }}
                  role="group"
                  aria-label="Filter personas by historical era"
                >
                  <Typography
                    variant="subtitle2"
                    sx={{
                      display: 'block',
                      textAlign: 'center',
                      mb: 2,
                      color: 'text.primary',
                      fontWeight: 600,
                      fontSize: { xs: '0.875rem', md: '1rem' },
                    }}
                  >
                    By Era
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, justifyContent: 'center' }}>
                    {(Object.keys(ERA_INFO) as Era[]).map((era) => {
                      const eraInfo = ERA_INFO[era];
                      const isSelected = selectedEras.includes(era);
                      return (
                        <Chip
                          key={era}
                          label={`${eraInfo.label} (${eraInfo.range})`}
                          onClick={() => toggleEraFilter(era)}
                          color={isSelected ? 'secondary' : 'default'}
                          variant={isSelected ? 'filled' : 'outlined'}
                          aria-pressed={isSelected}
                          aria-label={`Filter by ${eraInfo.label} era, ${eraInfo.range}`}
                          sx={{
                            fontSize: { xs: '0.75rem', md: '0.875rem' },
                            '&:hover': {
                              bgcolor: isSelected ? 'secondary.dark' : 'action.hover',
                            },
                            '&:focus-visible': {
                              outline: '2px solid',
                              outlineColor: 'secondary.main',
                              outlineOffset: '2px',
                            },
                          }}
                        />
                      );
                    })}
                  </Box>
                </Box>
              </Box>

              {/* Active filters summary */}
              {(searchQuery || selectedCategories.length > 0 || selectedEras.length > 0 || showOnlyAvailable) && (
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                    justifyContent: 'center',
                    mt: 3,
                    pt: 2,
                    borderTop: 1,
                    borderColor: 'divider',
                  }}
                  role="status"
                  aria-live="polite"
                  aria-label="Active filters"
                >
                  <Typography variant="caption" color="text.secondary">
                    {searchQuery && `Searching: "${searchQuery}"`}
                    {searchQuery && (selectedCategories.length > 0 || selectedEras.length > 0 || showOnlyAvailable) && ' • '}
                    {selectedCategories.length > 0 && `${selectedCategories.length} categories`}
                    {selectedCategories.length > 0 && (selectedEras.length > 0 || showOnlyAvailable) && ' • '}
                    {selectedEras.length > 0 && `${selectedEras.length} eras`}
                    {selectedEras.length > 0 && showOnlyAvailable && ' • '}
                    {showOnlyAvailable && 'Available only'}
                  </Typography>
                  <Button
                    size="small"
                    onClick={clearFilters}
                    aria-label="Clear all active filters"
                    sx={{ fontSize: '0.75rem', textTransform: 'none' }}
                  >
                    Clear all
                  </Button>
                </Box>
              )}
            </Box>

            {/* Dynamically render all categories */}
            {filteredData && Object.entries(filteredData).map(([categoryKey, personas]) => {
              if (!personas || personas.length === 0) return null;

              // Get category display info
              const categoryInfo = getCategoryInfo(categoryKey);

              return (
                <PersonaCategory
                  key={categoryKey}
                  title={categoryInfo.title}
                  description={categoryInfo.description}
                  personas={personas}
                  gradient={categoryInfo.color}
                />
              );
            })}
          </>
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
          <Typography
            variant="body2"
            color="text.secondary"
            align="center"
            sx={{ fontSize: { xs: '0.875rem', md: '1rem' } }}
          >
            Built with AI • Powered by Claude • Open to exploration
          </Typography>
        </Container>
      </Box>
    </Box>
  );
}

interface PersonaCategoryProps {
  title: string;
  description: string;
  personas: Array<{
    id: number;
    name: string;
    slug: string;
    title: string;
    era: string;
    category: string;
    birth_year?: number | null;
    required_tier?: string;
    debate_count?: number;
  }>;
  gradient: string;
}

function PersonaCategory({ title, description, personas, gradient }: PersonaCategoryProps) {
  const { user } = useAuth();
  const [imageErrors, setImageErrors] = React.useState<Set<number>>(new Set());

  const handleImageError = (personaId: number) => {
    setImageErrors(prev => new Set(prev).add(personaId));
  };

  // Sort personas by birth year (time period), then by name alphabetically
  const sortedPersonas = sortPersonasByTime(personas);

  return (
    <Box component="section" sx={{ mb: { xs: 5, md: 8 } }}>
      <Box sx={{ mb: { xs: 2, md: 3 } }}>
        <Typography
          variant="h4"
          sx={{
            fontWeight: 700,
            background: gradient,
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            fontSize: { xs: '1.25rem', md: '1.5rem' },
          }}
        >
          {title}
        </Typography>
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ mt: 0.5, fontSize: { xs: '0.875rem', md: '1rem' } }}
        >
          {description}
        </Typography>
      </Box>

      <Grid container spacing={{ xs: 1.5, md: 2 }}>
        {sortedPersonas.map((persona) => {
          const hasAccess = hasPersonaAccess(user?.subscription_tier, persona.required_tier);
          const badge = getTierBadge(persona.required_tier, user?.subscription_tier);
          const isLocked = !hasAccess;

          return (
            <Grid key={persona.id} size={{ xs: 12, sm: 6, lg: 4, xl: 3 }}>
              <Card sx={{ opacity: isLocked ? 0.6 : 1 }}>
                <CardActionArea component={Link} href={`/personas/${persona.slug}`}>
                  <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 2 }}>
                    <Box
                      sx={{
                        position: 'relative',
                        width: 56,
                        height: 56,
                        minWidth: 56,
                        borderRadius: '50%',
                        bgcolor: 'grey.100',
                        overflow: 'hidden',
                      }}
                    >
                      <Image
                        src={imageErrors.has(persona.id) ? '/portraits/default.svg' : `/portraits/${persona.slug}.png`}
                        alt={persona.name}
                        fill
                        style={{ objectFit: 'cover' }}
                        onError={() => handleImageError(persona.id)}
                      />
                    </Box>
                    <Box sx={{ flex: 1, minWidth: 0 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.25 }}>
                        <Typography
                          variant="h6"
                          component="h4"
                          sx={{
                            fontWeight: 600,
                            color: 'text.primary',
                            fontSize: { xs: '1rem', md: '1.125rem' },
                            transition: 'color 0.2s',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                            flex: 1,
                            '&:hover': {
                              color: 'primary.main',
                            },
                          }}
                        >
                          {persona.name}
                        </Typography>
                        {badge && (
                          <Chip
                            label={badge.label}
                            size="small"
                            sx={{
                              height: 20,
                              fontSize: '0.65rem',
                              fontWeight: 600,
                              bgcolor: badge.color,
                              color: 'white',
                            }}
                          />
                        )}
                      </Box>
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{
                          mt: 0.25,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {persona.title}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                        <Typography
                          variant="caption"
                          color="text.disabled"
                          sx={{
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          {persona.era}
                        </Typography>
                        {persona.debate_count !== undefined && persona.debate_count > 0 && (
                          <>
                            <Typography variant="caption" color="text.disabled">
                              •
                            </Typography>
                            <Chip
                              label={`${persona.debate_count} debates`}
                              size="small"
                              sx={{
                                height: 18,
                                fontSize: '0.6rem',
                                fontWeight: 500,
                                bgcolor: 'action.hover',
                                color: 'text.secondary',
                                '& .MuiChip-label': {
                                  px: 0.75,
                                },
                              }}
                            />
                          </>
                        )}
                      </Box>
                    </Box>
                  </CardContent>
                </CardActionArea>
              </Card>
            </Grid>
          );
        })}
      </Grid>
    </Box>
  );
}
