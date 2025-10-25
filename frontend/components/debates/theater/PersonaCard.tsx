'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Box, Typography, Card, Chip } from '@mui/material';
import Image from 'next/image';
import Link from 'next/link';
import type { DebateMessage, Persona } from '@/types';
import MessageContent from '../../MessageContent';

interface CitationBadgeProps {
  message: DebateMessage;
  isTyping?: boolean;
}

const CitationBadge = React.memo<CitationBadgeProps>(({ message, isTyping = false }) => {
  const citations = message.text_citations || [];

  if (citations.length === 0 || isTyping) return null;

  return (
    <Box sx={{ mt: 1.5, display: 'flex', flexDirection: 'column', gap: 0.5 }}>
      {citations.map((citation) => (
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
              bgcolor: 'rgba(34, 197, 94, 0.15)',
              border: '1px solid rgba(34, 197, 94, 0.4)',
              color: 'rgba(34, 197, 94, 1)',
              fontSize: '0.7rem',
              height: '24px',
              '&:hover': {
                bgcolor: 'rgba(34, 197, 94, 0.25)',
                borderColor: 'rgba(34, 197, 94, 0.6)',
              },
              transition: 'all 0.2s ease',
            }}
          />
        </Link>
      ))}
    </Box>
  );
});

CitationBadge.displayName = 'CitationBadge';

interface PersonaCardProps {
  persona: Persona;
  isActive: boolean;
  currentMessage: string | null;
  isTyping: boolean;
  pastMessages: DebateMessage[];
  allMessages: DebateMessage[];
  currentMessageIndex: number;
  isComplete: boolean;
}

const PersonaCard = React.memo<PersonaCardProps>(({
  persona,
  isActive,
  currentMessage,
  isTyping,
  pastMessages,
  allMessages,
  currentMessageIndex,
  isComplete,
}) => {
  const messageBoxRef = useRef<HTMLDivElement>(null);
  const [imageError, setImageError] = useState(false);
  const [autoScrollEnabled, setAutoScrollEnabled] = useState(true);

  // Handle manual scroll detection
  const handleScroll = useCallback(() => {
    if (!messageBoxRef.current) return;

    const { scrollTop, scrollHeight, clientHeight } = messageBoxRef.current;
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight;

    // If user is within 50px of bottom, resume auto-scroll
    // Otherwise, disable auto-scroll (user is reading older content)
    const shouldAutoScroll = distanceFromBottom < 50;

    // Only update state if it changed
    if (shouldAutoScroll !== autoScrollEnabled) {
      setAutoScrollEnabled(shouldAutoScroll);
    }
  }, [autoScrollEnabled]);

  // Auto-scroll message box to bottom ONLY for the active speaker and when auto-scroll is enabled
  useEffect(() => {
    if (messageBoxRef.current && isActive && autoScrollEnabled) {
      messageBoxRef.current.scrollTop = messageBoxRef.current.scrollHeight;
    }
  }, [currentMessage, pastMessages, isActive, autoScrollEnabled]);

  return (
    <Card
      sx={{
        bgcolor: isActive ? 'rgba(79, 70, 229, 0.15)' : 'rgba(255, 255, 255, 0.05)',
        border: '2px solid',
        borderColor: isActive ? '#4f46e5' : 'rgba(255, 255, 255, 0.1)',
        transition: 'all 0.3s ease',
        transform: isActive ? 'scale(1.02)' : 'scale(1)',
        opacity: isComplete ? 1 : (isActive ? 1 : 0.6),
        boxShadow: isActive ? '0 0 30px rgba(79, 70, 229, 0.5)' : 'none',
        animation: isActive && isTyping ? 'pulse 2s infinite' : 'none',
        '@keyframes pulse': {
          '0%, 100%': {
            boxShadow: '0 0 30px rgba(79, 70, 229, 0.5)',
          },
          '50%': {
            boxShadow: '0 0 50px rgba(79, 70, 229, 0.7)',
          },
        },
        p: 2.5,
        minHeight: '350px',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Portrait */}
      <Box
        sx={{
          position: 'relative',
          width: { xs: 100, md: 120 },
          height: { xs: 125, md: 150 }, // 4:5 aspect ratio
          mx: 'auto',
          mb: 1.5,
          borderRadius: 2,
          overflow: 'hidden',
          border: '3px solid',
          borderColor: isActive ? '#4f46e5' : 'rgba(255, 255, 255, 0.2)',
          transition: 'all 0.3s ease',
        }}
      >
        <Image
          src={imageError ? '/portraits/default.svg' : `/portraits/${persona.portrait_image || `${persona.slug}.png`}`}
          alt={persona.name}
          fill
          sizes="150px"
          style={{ objectFit: 'cover' }}
          onError={() => setImageError(true)}
          unoptimized
        />
      </Box>

      {/* Persona Info */}
      <Box sx={{ textAlign: 'center', mb: 2 }}>
        <Link
          href={`/personas/${persona.slug}`}
          style={{ textDecoration: 'none' }}
        >
          <Typography
            variant="h6"
            sx={{
              color: 'white',
              fontWeight: 700,
              mb: 0.5,
              fontSize: { xs: '1rem', md: '1.1rem' },
              cursor: 'pointer',
              '&:hover': {
                color: '#a78bfa',
                textDecoration: 'underline',
              },
              transition: 'all 0.2s ease',
            }}
          >
            {persona.name}
          </Typography>
        </Link>
        <Typography
          variant="caption"
          sx={{
            color: 'rgba(255, 255, 255, 0.7)',
            fontSize: '0.75rem',
          }}
        >
          {persona.era}
        </Typography>
        <Box sx={{ display: 'flex', gap: 0.5, justifyContent: 'center', mt: 0.5, flexWrap: 'wrap' }}>
          <Chip
            label={persona.category}
            size="small"
            sx={{
              bgcolor: 'rgba(255, 255, 255, 0.1)',
              color: 'rgba(255, 255, 255, 0.8)',
              fontSize: '0.65rem',
              height: '20px',
            }}
          />
          {persona.debate_count !== undefined && (
            <Chip
              label={`${persona.debate_count} debates`}
              size="small"
              sx={{
                bgcolor: 'rgba(79, 70, 229, 0.3)',
                color: 'rgba(255, 255, 255, 0.9)',
                fontSize: '0.65rem',
                height: '20px',
              }}
            />
          )}
        </Box>
      </Box>

      {/* Message Box with Past Messages and Current Message */}
      <Box
        ref={messageBoxRef}
        onScroll={handleScroll}
        sx={{
          flex: 1,
          bgcolor: 'rgba(0, 0, 0, 0.2)',
          borderRadius: 2,
          p: 1.5,
          minHeight: '120px',
          maxHeight: '250px',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: 1.5,
          '&::-webkit-scrollbar': {
            width: '6px',
          },
          '&::-webkit-scrollbar-track': {
            background: 'rgba(255, 255, 255, 0.05)',
            borderRadius: '3px',
          },
          '&::-webkit-scrollbar-thumb': {
            background: 'rgba(255, 255, 255, 0.2)',
            borderRadius: '3px',
            '&:hover': {
              background: 'rgba(255, 255, 255, 0.3)',
            },
          },
        }}
      >
        {/* Display Past Messages grouped by round */}
        {pastMessages.map((msg, index) => {
          // Show round label if this is a new round (first message or different round from previous)
          const showRoundLabel = index === 0 || msg.round_number !== pastMessages[index - 1].round_number;

          return (
            <Box key={index}>
              {showRoundLabel && (
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                    mb: 2,
                    mt: index > 0 ? 2 : 0,
                  }}
                >
                  <Typography
                    variant="caption"
                    sx={{
                      color: 'rgba(168, 85, 247, 1)',
                      fontWeight: 700,
                      textTransform: 'uppercase',
                      letterSpacing: '0.05em',
                      fontSize: '0.75rem',
                      textShadow: '0 0 10px rgba(168, 85, 247, 0.5)',
                    }}
                  >
                    Round {msg.round_number}
                  </Typography>
                  <Box
                    sx={{
                      flex: 1,
                      height: '2px',
                      bgcolor: 'rgba(168, 85, 247, 0.5)',
                      borderRadius: '1px',
                    }}
                  />
                </Box>
              )}
              <Typography
                variant="body1"
                sx={{
                  color: 'rgba(255, 255, 255, 0.8)',
                  lineHeight: 1.7,
                  whiteSpace: 'pre-wrap',
                }}
              >
                <MessageContent content={msg.content} citations={msg.text_citations} />
              </Typography>
              {/* Citations for this message */}
              <CitationBadge message={msg} />
              {/* Visual separator between messages within same round */}
              {index < pastMessages.length - 1 && msg.round_number === pastMessages[index + 1].round_number && (
                <Box
                  sx={{
                    mt: 2,
                    mb: 2,
                    height: '1px',
                    bgcolor: 'rgba(255, 255, 255, 0.15)',
                  }}
                />
              )}
            </Box>
          );
        })}

        {/* Current Typing Message */}
        {isActive && currentMessage ? (
          <Box>
            {/* Show round label for current message if it's a new round */}
            {(() => {
              const lastPastMessage = pastMessages[pastMessages.length - 1];
              const currentRound = allMessages[currentMessageIndex]?.round_number || 1;
              const showRoundLabel = !lastPastMessage || currentRound !== lastPastMessage.round_number;

              return showRoundLabel ? (
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                    mb: 2,
                    mt: pastMessages.length > 0 ? 2 : 0,
                  }}
                >
                  <Typography
                    variant="caption"
                    sx={{
                      color: 'rgba(168, 85, 247, 1)',
                      fontWeight: 700,
                      textTransform: 'uppercase',
                      letterSpacing: '0.05em',
                      fontSize: '0.75rem',
                      textShadow: '0 0 10px rgba(168, 85, 247, 0.5)',
                    }}
                  >
                    Round {currentRound}
                  </Typography>
                  <Box
                    sx={{
                      flex: 1,
                      height: '2px',
                      bgcolor: 'rgba(168, 85, 247, 0.5)',
                      borderRadius: '1px',
                    }}
                  />
                </Box>
              ) : null;
            })()}
            <Typography
              variant="body1"
              sx={{
                color: 'white',
                lineHeight: 1.7,
                whiteSpace: 'pre-wrap',
              }}
            >
              <MessageContent
                content={currentMessage}
                citations={allMessages[currentMessageIndex]?.text_citations}
              />
              {isTyping && (
                <Box
                  component="span"
                  sx={{
                    display: 'inline-block',
                    width: '8px',
                    height: '16px',
                    bgcolor: 'white',
                    ml: 0.5,
                    animation: 'blink 1s infinite',
                    '@keyframes blink': {
                      '0%, 49%': { opacity: 1 },
                      '50%, 100%': { opacity: 0 },
                    },
                  }}
                />
              )}
            </Typography>
            {/* Citations for current message (shown after typing completes) */}
            {allMessages[currentMessageIndex] && (
              <CitationBadge message={allMessages[currentMessageIndex]} isTyping={isTyping} />
            )}
          </Box>
        ) : pastMessages.length === 0 ? (
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flex: 1,
            }}
          >
            <Typography
              sx={{
                color: 'rgba(255, 255, 255, 0.4)',
                fontStyle: 'italic',
                textAlign: 'center',
              }}
            >
              {isActive ? 'Preparing to speak...' : 'Listening...'}
            </Typography>
          </Box>
        ) : null}
      </Box>
    </Card>
  );
});

PersonaCard.displayName = 'PersonaCard';

export default PersonaCard;
