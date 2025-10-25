'use client';

import React from 'react';
import { Box, Typography, Card } from '@mui/material';
import ReactMarkdown from 'react-markdown';
import type { Debate } from '@/types';

interface DebateSummaryProps {
  debate: Debate;
  messagesCount: number;
}

const DebateSummary = React.memo<DebateSummaryProps>(({
  debate,
  messagesCount,
}) => {
  if (!debate.summary) return null;

  return (
    <Box
      sx={{
        mt: 6,
        textAlign: 'center',
        py: 4,
      }}
    >
      <Typography
        variant="h4"
        sx={{
          color: 'white',
          fontWeight: 700,
          mb: 1,
        }}
      >
        Debate Complete
      </Typography>
      <Typography
        sx={{
          color: 'rgba(255, 255, 255, 0.7)',
          mb: 4,
        }}
      >
        All {messagesCount} exchanges have been presented
      </Typography>

      <Card
        sx={{
          bgcolor: 'rgba(79, 70, 229, 0.15)',
          border: '2px solid rgba(79, 70, 229, 0.5)',
          borderRadius: 3,
          p: 4,
          mt: 4,
          textAlign: 'left',
          maxWidth: '900px',
          mx: 'auto',
        }}
      >
        <Typography
          variant="h5"
          sx={{
            fontWeight: 700,
            mb: 3,
            color: 'white',
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            justifyContent: 'center',
          }}
        >
          📋 Debate Summary
        </Typography>
        <ReactMarkdown
          components={{
            p: ({ children }) => (
              <Typography
                sx={{
                  color: 'rgba(255, 255, 255, 0.9)',
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
                  color: 'white',
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
                  color: 'rgba(255, 255, 255, 0.9)',
                  listStyleType: 'disc',
                }}
              >
                {children}
              </Box>
            ),
            li: ({ children }) => (
              <Typography component="li" sx={{ mb: 0.5, color: 'rgba(255, 255, 255, 0.9)' }}>
                {children}
              </Typography>
            ),
          }}
        >
          {debate.summary}
        </ReactMarkdown>
      </Card>
    </Box>
  );
});

DebateSummary.displayName = 'DebateSummary';

export default DebateSummary;
