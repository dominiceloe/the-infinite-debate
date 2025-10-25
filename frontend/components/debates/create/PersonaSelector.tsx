'use client';

import { useState, useMemo, memo } from 'react';
import {
  Box,
  Typography,
  TextField,
  Card,
  CardContent,
  Grid,
  Chip,
  InputAdornment,
  IconButton,
  Button,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import ClearIcon from '@mui/icons-material/Clear';
import { getCategoryInfo, sortPersonasByTime } from '@/lib/categories';
import { hasPersonaAccess, getTierBadge } from '@/lib/tiers';
import type { PersonasByCategory } from '@/types';

export interface PersonaSelectorProps {
  data: PersonasByCategory | undefined;
  selectedPersonas: number[];
  onTogglePersona: (id: number) => void;
  maxParticipants: number;
  user: {
    subscription_tier?: string;
  };
}

const PersonaSelector = memo(({
  data,
  selectedPersonas,
  onTogglePersona,
  maxParticipants,
  user
}: PersonaSelectorProps) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);

  const toggleCategoryFilter = (category: string) => {
    setSelectedCategories((prev) =>
      prev.includes(category)
        ? prev.filter(c => c !== category)
        : [...prev, category]
    );
  };

  const clearFilters = () => {
    setSearchQuery('');
    setSelectedCategories([]);
  };

  const filteredData = useMemo(() => {
    if (!data) return null;

    return Object.entries(data).reduce((acc, [categoryKey, personas]) => {
      if (selectedCategories.length > 0 && !selectedCategories.includes(categoryKey)) {
        return acc;
      }

      const filtered = personas.filter((persona) => {
        if (!searchQuery) return true;
        const query = searchQuery.toLowerCase();
        return (
          persona.name.toLowerCase().includes(query) ||
          persona.title.toLowerCase().includes(query) ||
          persona.era.toLowerCase().includes(query)
        );
      });

      if (filtered.length > 0) {
        acc[categoryKey] = filtered;
      }

      return acc;
    }, {} as PersonasByCategory);
  }, [data, searchQuery, selectedCategories]);

  return (
    <>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Selected: {selectedPersonas.length} / {maxParticipants} (minimum 2 required)
      </Typography>

      {/* Search and Filter */}
      <Box sx={{ mb: 3 }}>
        <TextField
          fullWidth
          placeholder="Search by name, title, or era..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          slotProps={{
            input: {
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon color="action" />
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
          sx={{ mb: 2 }}
        />

        {/* Category filters */}
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
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
                sx={{
                  fontSize: { xs: '0.75rem', md: '0.875rem' },
                  '&:hover': {
                    bgcolor: isSelected ? 'primary.dark' : 'action.hover',
                  },
                }}
              />
            );
          })}
        </Box>

        {/* Active filters summary */}
        {(searchQuery || selectedCategories.length > 0) && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="caption" color="text.secondary">
              {searchQuery && `Searching: "${searchQuery}"`}
              {searchQuery && selectedCategories.length > 0 && ' • '}
              {selectedCategories.length > 0 && `${selectedCategories.length} categories selected`}
            </Typography>
            <Button
              size="small"
              onClick={clearFilters}
              sx={{ fontSize: '0.75rem', textTransform: 'none' }}
            >
              Clear all
            </Button>
          </Box>
        )}
      </Box>

      {/* Dynamically render all categories */}
      {filteredData && Object.entries(filteredData).map(([categoryKey, personas], categoryIndex) => {
        if (!personas || personas.length === 0) return null;

        const categoryInfo = getCategoryInfo(categoryKey);
        const sortedPersonas = sortPersonasByTime(personas);
        const isLast = categoryIndex === Object.keys(filteredData).length - 1;

        return (
          <Box key={categoryKey} sx={{ mb: isLast ? 0 : 4 }}>
            <Typography
              variant="h6"
              sx={{
                fontWeight: 700,
                mb: 2,
                background: categoryInfo.color,
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                fontSize: { xs: '1rem', md: '1.125rem' },
              }}
            >
              {categoryInfo.title}
            </Typography>
            <Grid container spacing={{ xs: 1.5, md: 2 }}>
              {sortedPersonas.map((persona) => {
                const hasAccess = hasPersonaAccess(user?.subscription_tier, persona.required_tier);
                const badge = getTierBadge(persona.required_tier, user?.subscription_tier);
                const isLocked = !hasAccess;
                const isSelected = selectedPersonas.includes(persona.id);

                return (
                  <Grid key={persona.id} size={{ xs: 6, sm: 4, md: 3, lg: 2.4 }}>
                    <Card
                      onClick={() => !isLocked && onTogglePersona(persona.id)}
                      sx={{
                        cursor: isLocked ? 'not-allowed' : 'pointer',
                        transition: 'all 0.2s',
                        border: isSelected ? 2 : 1,
                        borderColor: isSelected ? 'primary.main' : 'divider',
                        bgcolor: isSelected ? 'rgba(79, 70, 229, 0.04)' : 'background.paper',
                        boxShadow: isSelected ? 2 : 0,
                        opacity: isLocked ? 0.5 : 1,
                        '&:hover': {
                          borderColor: isLocked ? 'divider' : (isSelected ? 'primary.main' : 'grey.400'),
                          boxShadow: isLocked ? 0 : 1,
                        },
                      }}
                    >
                      <CardContent
                        sx={{
                          p: { xs: 1.5, md: 2 },
                          '&:last-child': { pb: { xs: 1.5, md: 2 } },
                        }}
                      >
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 0.5 }}>
                          <Typography
                            variant="body2"
                            sx={{
                              fontWeight: 600,
                              fontSize: { xs: '0.875rem', md: '0.875rem' },
                              color: 'text.primary',
                              flex: 1,
                            }}
                          >
                            {persona.name}
                          </Typography>
                          {badge && (
                            <Chip
                              label={badge.label}
                              size="small"
                              sx={{
                                height: 18,
                                fontSize: '0.6rem',
                                fontWeight: 600,
                                bgcolor: badge.color,
                                color: 'white',
                                ml: 0.5,
                              }}
                            />
                          )}
                        </Box>
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
                );
              })}
            </Grid>
          </Box>
        );
      })}
    </>
  );
});

PersonaSelector.displayName = 'PersonaSelector';

export default PersonaSelector;
