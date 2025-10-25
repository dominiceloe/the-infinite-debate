'use client';

import { memo, useRef, useEffect, useState, useCallback } from 'react';
import {
  Paper,
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  IconButton,
  Collapse,
} from '@mui/material';
import DragIndicatorIcon from '@mui/icons-material/DragIndicator';
import CloseIcon from '@mui/icons-material/Close';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import type { Persona } from '@/types';

export interface PreviewPanelProps {
  selectedPersonaDetails: Persona[];
  onRemovePersona: (id: number) => void;
  onReorderPersonas: (fromIndex: number, toIndex: number) => void;
  onClearAll: () => void;
  onSubmit: (e: React.FormEvent) => void;
  isSubmitting: boolean;
  canSubmit: boolean;
}

const PreviewPanel = memo(({
  selectedPersonaDetails,
  onRemovePersona,
  onReorderPersonas,
  onClearAll,
  onSubmit,
  isSubmitting,
  canSubmit,
}: PreviewPanelProps) => {
  const [isSticky, setIsSticky] = useState(false);
  const [isExpanded, setIsExpanded] = useState(true);
  const selectedPanelRef = useRef<HTMLDivElement>(null);
  const placeholderRef = useRef<HTMLDivElement>(null);
  const lastScrollY = useRef(0);

  // Scroll detection for sticky panel behavior
  useEffect(() => {
    let ticking = false;

    const handleScroll = () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          const currentScrollY = window.scrollY;
          const scrollingDown = currentScrollY > lastScrollY.current;
          const scrollDelta = Math.abs(currentScrollY - lastScrollY.current);

          // Only process if scroll delta is significant (reduces jitter)
          if (scrollDelta > 5) {
            const headerHeight = 64; // AppBar height

            // Check position based on current state
            if (!isSticky && selectedPanelRef.current) {
              // Not sticky yet - check panel position
              const panelTop = selectedPanelRef.current.getBoundingClientRect().top;
              if (panelTop <= headerHeight + 50) {
                setIsSticky(true);
              }
            } else if (isSticky && placeholderRef.current) {
              // Already sticky - check placeholder position to know when to un-stick
              const placeholderTop = placeholderRef.current.getBoundingClientRect().top;
              if (placeholderTop > headerHeight + 200) {
                setIsSticky(false);
                setIsExpanded(true);
              }
            }

            // When sticky, collapse/expand based on scroll direction
            if (isSticky) {
              if (scrollingDown) {
                setIsExpanded(false);
              } else {
                setIsExpanded(true);
              }
            }

            lastScrollY.current = currentScrollY;
          }

          ticking = false;
        });

        ticking = true;
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [isSticky]);

  const handleHeaderClick = useCallback(() => {
    if (isSticky) {
      setIsExpanded(!isExpanded);
    }
  }, [isSticky, isExpanded]);

  if (selectedPersonaDetails.length === 0) {
    return null;
  }

  return (
    <>
      {/* Placeholder to maintain layout when sticky */}
      {isSticky && <Box ref={placeholderRef} sx={{ height: '120px' }} />}

      <Paper
        ref={selectedPanelRef}
        elevation={isSticky ? 4 : 0}
        sx={{
          p: isExpanded ? 3 : 2,
          mb: isSticky ? 0 : 3,
          border: 2,
          borderColor: 'primary.main',
          borderRadius: isSticky ? 0 : 2,
          bgcolor: isSticky ? 'background.paper' : 'rgba(79, 70, 229, 0.04)',
          position: isSticky ? 'fixed' : 'relative',
          top: isSticky ? 64 : 'auto', // Below AppBar (64px height)
          left: isSticky ? '50%' : 'auto',
          transform: isSticky ? 'translateX(-50%)' : 'none',
          width: isSticky ? { xs: '100%', lg: '1200px' } : 'auto',
          maxWidth: isSticky ? 'calc(100% - 48px)' : 'none',
          mx: isSticky ? 'auto' : 0,
          zIndex: isSticky ? 1000 : 'auto',
          transition: 'padding 0.3s ease, box-shadow 0.3s ease, border-radius 0.3s ease',
          backdropFilter: isSticky ? 'blur(8px)' : 'none',
          maxHeight: isSticky ? '80vh' : 'none',
          overflowY: isSticky ? 'auto' : 'visible',
          // Ensure opaque background when sticky
          ...(isSticky && {
            '&::before': {
              content: '""',
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              bgcolor: 'background.paper',
              opacity: 0.98,
              zIndex: -1,
            },
          }),
        }}
      >
        {/* Header with collapse toggle */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            mb: isExpanded ? 2 : 0,
            cursor: isSticky ? 'pointer' : 'default',
          }}
          onClick={handleHeaderClick}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="h6" sx={{ fontWeight: 600, fontSize: isExpanded ? '1.25rem' : '1rem' }}>
              Selected Participants ({selectedPersonaDetails.length})
            </Typography>
            {isSticky && (
              <IconButton size="small" sx={{ ml: 1 }}>
                {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </IconButton>
            )}
          </Box>
          {isExpanded && (
            <Typography variant="caption" color="text.secondary">
              Drag to reorder turn sequence
            </Typography>
          )}
        </Box>

        {/* Collapsed view: comma-separated names */}
        {!isExpanded && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.6 }}>
              {selectedPersonaDetails.map((p, i) => (
                <span key={p.id}>
                  {i + 1}. {p.name}
                  {i < selectedPersonaDetails.length - 1 && ', '}
                </span>
              ))}
            </Typography>
          </Box>
        )}

        {/* Expanded view: draggable cards */}
        <Collapse in={isExpanded} timeout={300}>
          <Grid container spacing={2}>
            {selectedPersonaDetails.map((persona, index) => (
              <Grid key={persona.id} size={{ xs: 12, sm: 6, md: 4 }}>
                <Card
                  sx={{
                    border: 1,
                    borderColor: 'primary.main',
                    bgcolor: 'background.paper',
                    cursor: 'grab',
                    height: '100%',
                    '&:active': {
                      cursor: 'grabbing',
                    },
                  }}
                  draggable
                  onDragStart={(e) => {
                    e.dataTransfer.effectAllowed = 'move';
                    e.dataTransfer.setData('text/plain', index.toString());
                  }}
                  onDragOver={(e) => {
                    e.preventDefault();
                    e.dataTransfer.dropEffect = 'move';
                  }}
                  onDrop={(e) => {
                    e.preventDefault();
                    const fromIndex = parseInt(e.dataTransfer.getData('text/plain'), 10);
                    if (fromIndex !== index) {
                      onReorderPersonas(fromIndex, index);
                    }
                  }}
                >
                  <CardContent sx={{ p: 2, '&:last-child': { pb: 2 }, height: '100%', display: 'flex', flexDirection: 'column' }}>
                    <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, flex: 1 }}>
                      <DragIndicatorIcon sx={{ color: 'text.secondary', mt: 0.5, flexShrink: 0 }} />
                      <Box sx={{ flex: 1, minWidth: 0 }}>
                        <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>
                          {index + 1}. {persona.name}
                        </Typography>
                        <Typography
                          variant="caption"
                          color="text.secondary"
                          sx={{
                            display: '-webkit-box',
                            WebkitLineClamp: 2,
                            WebkitBoxOrient: 'vertical',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            lineHeight: 1.4,
                            minHeight: '2.8em',
                          }}
                        >
                          {persona.era}
                        </Typography>
                      </Box>
                      <IconButton
                        size="small"
                        onClick={() => onRemovePersona(persona.id)}
                        sx={{
                          color: 'error.main',
                          flexShrink: 0,
                          '&:hover': {
                            bgcolor: 'error.lighter',
                          },
                        }}
                      >
                        <CloseIcon fontSize="small" />
                      </IconButton>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Collapse>

        {/* Action buttons - always visible */}
        <Box sx={{ display: 'flex', gap: 2, mt: isExpanded ? 3 : 2, flexDirection: { xs: 'column', sm: 'row' } }}>
          <Button
            type="submit"
            variant="contained"
            onClick={onSubmit}
            disabled={!canSubmit || isSubmitting}
            sx={{
              flex: { xs: 'auto', sm: 1 },
              py: 1.5,
              fontSize: '1rem',
              fontWeight: 500,
            }}
          >
            {isSubmitting ? 'Creating...' : 'Create Debate'}
          </Button>
          {isExpanded && (
            <Button
              variant="outlined"
              onClick={onClearAll}
              sx={{
                py: 1.5,
                px: 3,
                fontSize: '1rem',
              }}
            >
              Clear All
            </Button>
          )}
        </Box>
      </Paper>
    </>
  );
});

PreviewPanel.displayName = 'PreviewPanel';

export default PreviewPanel;
