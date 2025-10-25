import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import DebateSummary from '@/components/debates/theater/DebateSummary';
import type { Debate } from '@/types';

describe('DebateSummary', () => {
  const mockDebate: Debate = {
    id: 1,
    title: 'Test Debate',
    topic: 'Test Topic',
    slug: 'test-debate',
    depth_level: 'intermediate',
    max_rounds: 5,
    transcript: '',
    summary: 'This is a **bold** test summary.',
    status: 'completed',
    rounds_completed: 5,
    error_message: '',
    created_at: '2024-01-01',
    updated_at: '2024-01-01',
    completed_at: '2024-01-01',
  };

  it('renders summary when debate has summary', () => {
    render(<DebateSummary debate={mockDebate} messagesCount={10} />);

    expect(screen.getByText('Debate Complete')).toBeInTheDocument();
    expect(screen.getByText('All 10 exchanges have been presented')).toBeInTheDocument();
    expect(screen.getByText('📋 Debate Summary')).toBeInTheDocument();
  });

  it('does not render when debate has no summary', () => {
    const debateWithoutSummary = { ...mockDebate, summary: '' };
    const { container } = render(
      <DebateSummary debate={debateWithoutSummary} messagesCount={10} />
    );

    expect(container.firstChild).toBeNull();
  });

  it('renders markdown content correctly', () => {
    render(<DebateSummary debate={mockDebate} messagesCount={10} />);

    // Should render bold text
    const boldElement = screen.getByText('bold');
    expect(boldElement.tagName).toBe('SPAN');
  });
});
