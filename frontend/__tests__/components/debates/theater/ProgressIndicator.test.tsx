import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import ProgressIndicator from '@/components/debates/theater/ProgressIndicator';

describe('ProgressIndicator', () => {
  it('renders round information correctly', () => {
    render(
      <ProgressIndicator
        currentRound={3}
        maxRounds={5}
        isComplete={false}
        isTyping={false}
      />
    );

    expect(screen.getByText('Round 3 of 5')).toBeInTheDocument();
  });

  it('displays "Speaking..." when typing', () => {
    render(
      <ProgressIndicator
        currentRound={1}
        maxRounds={5}
        isComplete={false}
        isTyping={true}
      />
    );

    expect(screen.getByText('Speaking...')).toBeInTheDocument();
  });

  it('displays "Listening..." when not typing and not complete', () => {
    render(
      <ProgressIndicator
        currentRound={1}
        maxRounds={5}
        isComplete={false}
        isTyping={false}
      />
    );

    expect(screen.getByText('Listening...')).toBeInTheDocument();
  });

  it('displays "Complete" when debate is finished', () => {
    render(
      <ProgressIndicator
        currentRound={5}
        maxRounds={5}
        isComplete={true}
        isTyping={false}
      />
    );

    expect(screen.getByText('Complete')).toBeInTheDocument();
  });
});
