'use client';

import React from 'react';
import { Box, Typography, Chip, Container } from '@mui/material';

interface ProgressIndicatorProps {
  currentRound: number;
  maxRounds: number;
  isComplete: boolean;
  isTyping: boolean;
}

const ProgressIndicator = React.memo<ProgressIndicatorProps>(({
  currentRound,
  maxRounds,
  isComplete,
  isTyping,
}) => {
  const getStatusLabel = () => {
    if (isComplete) return 'Complete';
    if (isTyping) return 'Speaking...';
    return 'Listening...';
  };

  const getStatusColor = () => {
    if (isComplete) return 'success.main';
    if (isTyping) return 'warning.main';
    return 'info.main';
  };

  return (
    <Box
      sx={{
        position: 'sticky',
        top: 0,
        zIndex: 10,
        bgcolor: 'rgba(15, 23, 42, 0.95)',
        backdropFilter: 'blur(10px)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        py: 2,
      }}
    >
      <Container maxWidth="lg">
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 2 }}>
          <Typography
            variant="h6"
            sx={{
              color: 'white',
              fontWeight: 600,
              fontSize: { xs: '1rem', md: '1.25rem' },
            }}
          >
            Round {currentRound} of {maxRounds}
          </Typography>
          <Chip
            label={getStatusLabel()}
            size="small"
            sx={{
              bgcolor: getStatusColor(),
              color: 'white',
              fontWeight: 500,
            }}
          />
        </Box>
      </Container>
    </Box>
  );
});

ProgressIndicator.displayName = 'ProgressIndicator';

export default ProgressIndicator;
