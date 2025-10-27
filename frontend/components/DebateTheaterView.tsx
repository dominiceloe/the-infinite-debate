'use client';

import React, { useState, useRef, useCallback } from 'react';
import { Box } from '@mui/material';
import type { Debate } from '@/types';
import { useTypewriter } from '@/hooks/useTypewriter';
import ProgressIndicator from './debates/theater/ProgressIndicator';
import PersonaGrid from './debates/theater/PersonaGrid';
import DebateSummary from './debates/theater/DebateSummary';

interface DebateTheaterViewProps {
  debate: Debate;
}

export default function DebateTheaterView({ debate }: DebateTheaterViewProps) {
  const messages = debate.messages || [];

  // Track if we've ever seen this debate in 'generating' status (watching live)
  const wasEverGenerating = useRef(debate.status === 'generating');

  // Update the ref if we see 'generating' status
  if (debate.status === 'generating') {
    wasEverGenerating.current = true;
  }

  // If debate was completed when first opened AND we never saw it generating, show all messages immediately
  // Otherwise start from 0 and animate as messages come in
  const [currentMessageIndex, setCurrentMessageIndex] = useState(
    debate.status === 'completed' && !wasEverGenerating.current ? messages.length : 0
  );

  const currentMessage = messages[currentMessageIndex];
  const isComplete = currentMessageIndex >= messages.length;

  // Typewriter animation continues naturally through all messages during live viewing
  // No force-jump when status changes - the ref tracks whether we're watching live

  // Get current round number
  const currentRound = currentMessage?.round_number || 1;
  const maxRounds = debate.max_rounds;

  // Handle message completion
  const handleMessageComplete = useCallback(() => {
    // Move to next message after a brief pause
    setTimeout(() => {
      setCurrentMessageIndex((prev) => prev + 1);
    }, 500);
  }, []);

  // Typewriter effect for current message
  const { displayedText, isTyping } = useTypewriter({
    text: currentMessage?.content || '',
    speed: 400, // 500 words per minute
    enabled: !isComplete && currentMessageIndex < messages.length,
    onComplete: handleMessageComplete,
  });

  return (
    <Box
      sx={{
        minHeight: '70vh',
        background: 'linear-gradient(to bottom, #0f172a, #1e293b)',
        borderRadius: { xs: 0, md: 2 },
        overflow: 'hidden',
        position: 'relative',
      }}
    >
      {/* Round Counter */}
      <ProgressIndicator
        currentRound={currentRound}
        maxRounds={maxRounds}
        isComplete={isComplete}
        isTyping={isTyping}
      />

      {/* Theater Stage */}
      <PersonaGrid
        personas={debate.participants || []}
        messages={messages}
        currentMessageIndex={currentMessageIndex}
        displayedText={displayedText}
        isTyping={isTyping}
        isComplete={isComplete}
      />

      {/* Completion Message and Summary */}
      {isComplete && (
        <DebateSummary
          debate={debate}
          messagesCount={messages.length}
        />
      )}
    </Box>
  );
}
