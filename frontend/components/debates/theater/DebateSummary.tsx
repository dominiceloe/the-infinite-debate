'use client';

import React from 'react';
import { Box, Typography, Accordion, AccordionSummary, AccordionDetails } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
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

      <Accordion
        sx={{
          bgcolor: 'rgba(79, 70, 229, 0.15)',
          border: '2px solid rgba(79, 70, 229, 0.5)',
          borderRadius: { xs: 2, md: 3 },
          mt: { xs: 3, md: 4 },
          maxWidth: { xs: '100%', md: '900px' },
          mx: 'auto',
          '&:before': {
            display: 'none', // Remove default MUI accordion divider
          },
        }}
      >
        <AccordionSummary
          expandIcon={<ExpandMoreIcon sx={{ color: 'white' }} />}
          sx={{
            px: { xs: 2, md: 4 },
            py: 1.5,
          }}
        >
          <Typography
            variant="h5"
            sx={{
              fontWeight: 700,
              color: 'white',
              display: 'flex',
              alignItems: 'center',
              gap: 1,
            }}
          >
            📋 Debate Summary
          </Typography>
        </AccordionSummary>
        <AccordionDetails
          sx={{
            px: { xs: 2, md: 4 },
            pb: { xs: 2, md: 4 },
            pt: 0,
            textAlign: 'left',
          }}
        >
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
        </AccordionDetails>
      </Accordion>
    </Box>
  );
});

DebateSummary.displayName = 'DebateSummary';

export default DebateSummary;
