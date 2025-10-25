import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import PersonaCard from '@/components/debates/theater/PersonaCard';
import type { Persona, DebateMessage } from '@/types';

// Mock Next.js Image component
vi.mock('next/image', () => ({
  default: ({ src, alt }: { src: string; alt: string }) => <img src={src} alt={alt} />,
}));

// Mock Next.js Link component
vi.mock('next/link', () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

// Mock MessageContent component
vi.mock('@/components/MessageContent', () => ({
  default: ({ content }: { content: string }) => <span>{content}</span>,
}));

describe('PersonaCard', () => {
  const mockPersona: Persona = {
    id: 1,
    name: 'Socrates',
    slug: 'socrates',
    title: 'The Gadfly of Athens',
    category: 'philosophers',
    era: '470-399 BCE',
    birth_year: -470,
    death_year: -399,
    religion_worldview: 'Ancient Greek Philosophy',
    debate_count: 5,
  };

  const mockMessage: DebateMessage = {
    id: 1,
    persona: mockPersona,
    round_number: 1,
    content: 'Test message content',
    created_at: '2024-01-01',
  };

  it('renders persona information correctly', () => {
    render(
      <PersonaCard
        persona={mockPersona}
        isActive={false}
        currentMessage={null}
        isTyping={false}
        pastMessages={[]}
        allMessages={[]}
        currentMessageIndex={0}
        isComplete={false}
      />
    );

    expect(screen.getByText('Socrates')).toBeInTheDocument();
    expect(screen.getByText('470-399 BCE')).toBeInTheDocument();
    expect(screen.getByText('philosophers')).toBeInTheDocument();
    expect(screen.getByText('5 debates')).toBeInTheDocument();
  });

  it('displays current message when active and typing', () => {
    render(
      <PersonaCard
        persona={mockPersona}
        isActive={true}
        currentMessage="Currently speaking..."
        isTyping={true}
        pastMessages={[]}
        allMessages={[mockMessage]}
        currentMessageIndex={0}
        isComplete={false}
      />
    );

    expect(screen.getByText('Currently speaking...')).toBeInTheDocument();
  });

  it('displays past messages', () => {
    render(
      <PersonaCard
        persona={mockPersona}
        isActive={false}
        currentMessage={null}
        isTyping={false}
        pastMessages={[mockMessage]}
        allMessages={[mockMessage]}
        currentMessageIndex={1}
        isComplete={false}
      />
    );

    expect(screen.getByText('Test message content')).toBeInTheDocument();
  });

  it('shows "Listening..." when not active and no past messages', () => {
    render(
      <PersonaCard
        persona={mockPersona}
        isActive={false}
        currentMessage={null}
        isTyping={false}
        pastMessages={[]}
        allMessages={[]}
        currentMessageIndex={0}
        isComplete={false}
      />
    );

    expect(screen.getByText('Listening...')).toBeInTheDocument();
  });

  it('shows "Preparing to speak..." when active but no message yet', () => {
    render(
      <PersonaCard
        persona={mockPersona}
        isActive={true}
        currentMessage={null}
        isTyping={false}
        pastMessages={[]}
        allMessages={[]}
        currentMessageIndex={0}
        isComplete={false}
      />
    );

    expect(screen.getByText('Preparing to speak...')).toBeInTheDocument();
  });

  it('renders portrait image with correct src', () => {
    render(
      <PersonaCard
        persona={mockPersona}
        isActive={false}
        currentMessage={null}
        isTyping={false}
        pastMessages={[]}
        allMessages={[]}
        currentMessageIndex={0}
        isComplete={false}
      />
    );

    const image = screen.getByAltText('Socrates');
    expect(image).toHaveAttribute('src', '/portraits/socrates.png');
  });
});
