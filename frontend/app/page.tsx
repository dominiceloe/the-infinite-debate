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
  Popover,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import ClearIcon from '@mui/icons-material/Clear';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

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
  const [categoryAnchor, setCategoryAnchor] = React.useState<HTMLButtonElement | null>(null);
  const [eraAnchor, setEraAnchor] = React.useState<HTMLButtonElement | null>(null);

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

  // Calculate total filtered count for display
  const totalFilteredCount = React.useMemo(() => {
    if (!filteredData) return 0;
    return Object.values(filteredData).reduce((sum, personas) => sum + personas.length, 0);
  }, [filteredData]);

  const hasActiveFilters = searchQuery || selectedCategories.length > 0 || selectedEras.length > 0 || showOnlyAvailable;

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
            {/* Introduction - Compact */}
            <Box sx={{ textAlign: 'center', mb: { xs: 2, md: 3 }, px: 1 }}>
              <Typography
                variant="body2"
                sx={{
                  fontStyle: 'italic',
                  color: 'text.secondary',
                  mb: 1,
                  fontSize: { xs: '0.875rem', md: '1rem' },
                }}
              >
                {hookText}
              </Typography>
              <Typography
                variant="h4"
                component="h2"
                sx={{
                  fontWeight: 700,
                  mb: 0.5,
                  fontSize: { xs: '1.25rem', md: '1.75rem' },
                }}
              >
                Choose Your Thinkers
              </Typography>
              <Typography
                variant="body2"
                color="text.secondary"
              >
                {Object.values(data || {}).reduce((sum, personas) => sum + personas.length, 0)} historical figures
              </Typography>
            </Box>

            {/* Compact Search + Filters */}
            <Box sx={{ mb: 3 }}>
              {/* Search bar + filter buttons inline */}
              <Box
                sx={{
                  display: 'flex',
                  flexDirection: { xs: 'column', md: 'row' },
                  alignItems: { xs: 'stretch', md: 'center' },
                  gap: { xs: 1.5, md: 2 },
                  mb: 2,
                }}
              >
                {/* Search */}
                <TextField
                  placeholder="Search personas..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  size="small"
                  slotProps={{
                    input: {
                      startAdornment: (
                        <InputAdornment position="start">
                          <SearchIcon color="action" fontSize="small" />
                        </InputAdornment>
                      ),
                      endAdornment: searchQuery ? (
                        <InputAdornment position="end">
                          <IconButton size="small" onClick={() => setSearchQuery('')}>
                            <ClearIcon fontSize="small" />
                          </IconButton>
                        </InputAdornment>
                      ) : null,
                    }
                  }}
                  sx={{ flex: 1, minWidth: { xs: '100%', md: 200 } }}
                />

                {/* Filter buttons */}
                <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
                  {/* Categories Popover */}
                  <Button
                    size="small"
                    variant={selectedCategories.length > 0 ? 'contained' : 'outlined'}
                    onClick={(e) => setCategoryAnchor(e.currentTarget)}
                    endIcon={<ExpandMoreIcon />}
                    sx={{ textTransform: 'none', minWidth: 'auto' }}
                  >
                    Categories{selectedCategories.length > 0 && ` (${selectedCategories.length})`}
                  </Button>
                  <Popover
                    open={Boolean(categoryAnchor)}
                    anchorEl={categoryAnchor}
                    onClose={() => setCategoryAnchor(null)}
                    anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
                  >
                    <Box sx={{ p: 2, maxHeight: 350, overflow: 'auto', minWidth: 220 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="subtitle2">Categories</Typography>
                        {selectedCategories.length > 0 && (
                          <Button size="small" onClick={() => setSelectedCategories([])} sx={{ p: 0, minWidth: 'auto' }}>
                            Clear
                          </Button>
                        )}
                      </Box>
                      {data && Object.keys(data).sort().map((categoryKey) => {
                        const categoryInfo = getCategoryInfo(categoryKey);
                        return (
                          <FormControlLabel
                            key={categoryKey}
                            control={
                              <Checkbox
                                size="small"
                                checked={selectedCategories.includes(categoryKey)}
                                onChange={() => toggleCategoryFilter(categoryKey)}
                              />
                            }
                            label={<Typography variant="body2">{categoryInfo.title}</Typography>}
                            sx={{ display: 'flex', m: 0, py: 0.25 }}
                          />
                        );
                      })}
                    </Box>
                  </Popover>

                  {/* Eras Popover */}
                  <Button
                    size="small"
                    variant={selectedEras.length > 0 ? 'contained' : 'outlined'}
                    onClick={(e) => setEraAnchor(e.currentTarget)}
                    endIcon={<ExpandMoreIcon />}
                    sx={{ textTransform: 'none', minWidth: 'auto' }}
                  >
                    Eras{selectedEras.length > 0 && ` (${selectedEras.length})`}
                  </Button>
                  <Popover
                    open={Boolean(eraAnchor)}
                    anchorEl={eraAnchor}
                    onClose={() => setEraAnchor(null)}
                    anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
                  >
                    <Box sx={{ p: 2, minWidth: 220 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="subtitle2">Eras</Typography>
                        {selectedEras.length > 0 && (
                          <Button size="small" onClick={() => setSelectedEras([])} sx={{ p: 0, minWidth: 'auto' }}>
                            Clear
                          </Button>
                        )}
                      </Box>
                      {(Object.keys(ERA_INFO) as Era[]).map((era) => {
                        const eraInfo = ERA_INFO[era];
                        return (
                          <FormControlLabel
                            key={era}
                            control={
                              <Checkbox
                                size="small"
                                checked={selectedEras.includes(era)}
                                onChange={() => toggleEraFilter(era)}
                              />
                            }
                            label={<Typography variant="body2">{eraInfo.label}</Typography>}
                            sx={{ display: 'flex', m: 0, py: 0.25 }}
                          />
                        );
                      })}
                    </Box>
                  </Popover>

                  {/* Available checkbox */}
                  <FormControlLabel
                    control={
                      <Checkbox
                        size="small"
                        checked={showOnlyAvailable}
                        onChange={(e) => setShowOnlyAvailable(e.target.checked)}
                      />
                    }
                    label={<Typography variant="body2">Available</Typography>}
                    sx={{ m: 0, ml: { xs: 0, md: 1 } }}
                  />

                  {/* Clear all */}
                  {hasActiveFilters && (
                    <Button
                      size="small"
                      onClick={clearFilters}
                      sx={{ textTransform: 'none', minWidth: 'auto' }}
                    >
                      Clear all
                    </Button>
                  )}
                </Box>
              </Box>

              {/* Result count + active filter chips */}
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                  flexWrap: 'wrap',
                  minHeight: 28,
                }}
                role="status"
                aria-live="polite"
              >
                <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
                  {totalFilteredCount} {totalFilteredCount === 1 ? 'persona' : 'personas'}
                </Typography>
                {selectedCategories.map((cat) => (
                  <Chip
                    key={cat}
                    label={getCategoryInfo(cat).title}
                    size="small"
                    onDelete={() => toggleCategoryFilter(cat)}
                    sx={{ height: 24 }}
                  />
                ))}
                {selectedEras.map((era) => (
                  <Chip
                    key={era}
                    label={ERA_INFO[era].label}
                    size="small"
                    color="secondary"
                    onDelete={() => toggleEraFilter(era)}
                    sx={{ height: 24 }}
                  />
                ))}
                {showOnlyAvailable && (
                  <Chip
                    label="Available only"
                    size="small"
                    color="primary"
                    onDelete={() => setShowOnlyAvailable(false)}
                    sx={{ height: 24 }}
                  />
                )}
              </Box>
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

      <Grid container spacing={{ xs: 1, sm: 1.5, md: 2 }}>
        {sortedPersonas.map((persona) => {
          const hasAccess = hasPersonaAccess(user?.subscription_tier, persona.required_tier);
          const badge = getTierBadge(persona.required_tier, user?.subscription_tier);
          const isLocked = !hasAccess;

          return (
            <Grid key={persona.id} size={{ xs: 6, sm: 6, md: 4, lg: 3 }}>
              <Card sx={{ opacity: isLocked ? 0.6 : 1 }}>
                <CardActionArea component={Link} href={`/personas/${persona.slug}`}>
                  <CardContent sx={{ display: 'flex', alignItems: 'center', gap: { xs: 1.5, sm: 2 }, p: { xs: 1.5, sm: 2 } }}>
                    <Box
                      sx={{
                        position: 'relative',
                        width: { xs: 48, sm: 56 },
                        height: { xs: 48, sm: 56 },
                        minWidth: { xs: 48, sm: 56 },
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
                            fontSize: { xs: '0.875rem', sm: '1rem', md: '1.125rem' },
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
                          fontSize: { xs: '0.75rem', sm: '0.875rem' },
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
