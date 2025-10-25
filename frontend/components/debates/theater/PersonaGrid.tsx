'use client';

import React, { useMemo, useCallback } from 'react';
import { Box, Container } from '@mui/material';
import type { Persona, DebateMessage } from '@/types';
import PersonaCard from './PersonaCard';

interface PersonaGridProps {
  personas: Persona[];
  messages: DebateMessage[];
  currentMessageIndex: number;
  displayedText: string;
  isTyping: boolean;
  isComplete: boolean;
}

const PersonaGrid = React.memo<PersonaGridProps>(({
  personas,
  messages,
  currentMessageIndex,
  displayedText,
  isTyping,
  isComplete,
}) => {
  // Organize personas chronologically (sorted by birth year)
  const sortedPersonas = useMemo(() => {
    return [...personas].sort((a, b) => (a.birth_year || 0) - (b.birth_year || 0));
  }, [personas]);

  // Get messages for each persona
  const getPersonaMessages = useCallback((personaId: number) => {
    return messages.filter((msg, index) =>
      msg.persona.id === personaId && index < currentMessageIndex
    );
  }, [messages, currentMessageIndex]);

  // Determine which persona is currently speaking
  const currentMessage = messages[currentMessageIndex];
  const activeSpeakerId = currentMessage?.persona?.id;

  // Calculate grid columns based on number of participants
  const gridColumns = useMemo(() => {
    const count = sortedPersonas.length;
    if (count <= 2) return 2;
    if (count === 3) return 3;
    if (count <= 4) return 2; // 2x2 grid
    if (count <= 6) return 3; // 3x2 grid
    return 4; // 4 column grid for 7+
  }, [sortedPersonas.length]);

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: {
            xs: '1fr',
            md: `repeat(${gridColumns}, 1fr)`,
          },
          gap: 3,
          minHeight: '350px',
        }}
      >
        {/* Render a card for each persona */}
        {sortedPersonas.map((persona) => (
          <PersonaCard
            key={persona.id}
            persona={persona}
            isActive={activeSpeakerId === persona.id}
            currentMessage={activeSpeakerId === persona.id ? displayedText : null}
            isTyping={activeSpeakerId === persona.id && isTyping}
            pastMessages={getPersonaMessages(persona.id)}
            allMessages={messages}
            currentMessageIndex={currentMessageIndex}
            isComplete={isComplete}
          />
        ))}
      </Box>
    </Container>
  );
});

PersonaGrid.displayName = 'PersonaGrid';

export default PersonaGrid;
