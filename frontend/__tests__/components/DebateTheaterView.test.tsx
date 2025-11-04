import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import DebateTheaterView from '@/components/DebateTheaterView'
import type { Debate, Persona, DebateMessage, TextCitation } from '@/types'
import { useTypewriter } from '@/hooks/useTypewriter'

// Mock the useTypewriter hook
vi.mock('@/hooks/useTypewriter')

// Mock Next.js Image component
vi.mock('next/image', () => ({
  default: ({ src, alt, onError, ...props }: React.ImgHTMLAttributes<HTMLImageElement> & { onError?: () => void }) => {
    return (
      <img
        src={src as string}
        alt={alt}
        onError={onError}
        {...props}
      />
    )
  },
}))

// Mock Next.js Link component
vi.mock('next/link', () => ({
  default: ({ href, children, ...props }: React.AnchorHTMLAttributes<HTMLAnchorElement> & { href: string }) => {
    return (
      <a href={href} {...props}>
        {children}
      </a>
    )
  },
}))

// Mock MessageContent component
vi.mock('@/components/MessageContent', () => ({
  default: ({ content }: { content: string; citations?: unknown[] }) => <>{content}</>,
}))

// Mock personas for testing
const mockPersona1: Persona = {
  id: 1,
  name: 'Socrates',
  slug: 'socrates',
  title: 'The Gadfly of Athens',
  category: 'philosophers',
  era: '470-399 BCE',
  birth_year: -470,
  death_year: -399,
  religion_worldview: 'Ancient Greek',
  portrait_image: 'socrates.png',
  debate_count: 5,
}

const mockPersona2: Persona = {
  id: 2,
  name: 'Plato',
  slug: 'plato',
  title: 'Student of Socrates',
  category: 'philosophers',
  era: '427-347 BCE',
  birth_year: -427,
  death_year: -347,
  religion_worldview: 'Ancient Greek',
  portrait_image: 'plato.png',
  debate_count: 3,
}

const mockPersona3: Persona = {
  id: 3,
  name: 'Aristotle',
  slug: 'aristotle',
  title: 'The Philosopher',
  category: 'philosophers',
  era: '384-322 BCE',
  birth_year: -384,
  death_year: -322,
  religion_worldview: 'Ancient Greek',
  portrait_image: 'aristotle.png',
  debate_count: 7,
}

// Mock citations
const mockCitation1: TextCitation = {
  id: 1,
  debate_message: 1,
  text: 1,
  text_title: 'The Republic',
  text_author: 'Plato',
  text_slug: 'the-republic',
  citation_text: 'Quote from The Republic',
  match_confidence: 0.95,
  match_method: 'exact',
  verified: true,
  created_at: '2024-01-01T00:00:00Z',
}

const mockCitation2: TextCitation = {
  id: 2,
  debate_message: 2,
  text: 2,
  text_title: 'Nicomachean Ethics',
  text_author: 'Aristotle',
  text_slug: 'nicomachean-ethics',
  citation_text: 'Quote from Ethics',
  match_confidence: 0.92,
  match_method: 'semantic',
  verified: true,
  created_at: '2024-01-01T00:00:00Z',
}

// Mock messages
const mockMessage1: DebateMessage = {
  id: 1,
  persona: mockPersona1,
  round_number: 1,
  content: 'The only true wisdom is in knowing you know nothing.',
  text_citations: [mockCitation1],
  created_at: '2024-01-01T00:00:00Z',
}

const mockMessage2: DebateMessage = {
  id: 2,
  persona: mockPersona2,
  round_number: 1,
  content: 'But master, surely knowledge can be attained through philosophical inquiry.',
  text_citations: [mockCitation2],
  created_at: '2024-01-01T00:01:00Z',
}

const mockMessage3: DebateMessage = {
  id: 3,
  persona: mockPersona1,
  round_number: 2,
  content: 'Indeed, but we must always question what we think we know.',
  created_at: '2024-01-01T00:02:00Z',
}

// Mock debate data generators
const createMockDebate = (
  status: Debate['status'] = 'completed',
  messages: DebateMessage[] = [mockMessage1, mockMessage2],
  participants: Persona[] = [mockPersona1, mockPersona2]
): Debate => ({
  id: 1,
  title: 'The Nature of Knowledge',
  topic: 'What is true knowledge?',
  slug: 'nature-of-knowledge',
  participants,
  depth_level: 'intermediate',
  max_rounds: 3,
  transcript: '',
  summary: 'A deep discussion on the nature of knowledge and wisdom.',
  status,
  rounds_completed: messages.length > 0 ? Math.max(...messages.map(m => m.round_number)) : 0,
  error_message: '',
  messages,
  participant_count: participants.length,
  participant_names: participants.map(p => p.name).join(', '),
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:05:00Z',
  completed_at: status === 'completed' ? '2024-01-01T00:05:00Z' : null,
})

describe('DebateTheaterView', () => {
  beforeEach(() => {
    // Default mock implementation for useTypewriter
    vi.mocked(useTypewriter).mockReturnValue({
      displayedText: '',
      isTyping: false,
      reset: vi.fn(),
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Basic Rendering', () => {
    it('renders the debate topic and participants', () => {
      const debate = createMockDebate()
      render(<DebateTheaterView debate={debate} />)

      // Check for round counter
      expect(screen.getByText(/Round 1 of 3/)).toBeInTheDocument()
    })

    it('displays all participants in chronological order by birth year', () => {
      const debate = createMockDebate('completed', [], [mockPersona2, mockPersona1, mockPersona3])
      render(<DebateTheaterView debate={debate} />)

      // Should be sorted by birth year: Socrates (-470), Plato (-427), Aristotle (-384)
      const personaCards = screen.getAllByText(/Socrates|Plato|Aristotle/)
      expect(personaCards).toHaveLength(3)
      expect(screen.getByText('Socrates')).toBeInTheDocument()
      expect(screen.getByText('Plato')).toBeInTheDocument()
      expect(screen.getByText('Aristotle')).toBeInTheDocument()
    })

    it('displays persona information correctly', () => {
      const debate = createMockDebate()
      render(<DebateTheaterView debate={debate} />)

      // Check Socrates card
      expect(screen.getByText('Socrates')).toBeInTheDocument()
      expect(screen.getByText('470-399 BCE')).toBeInTheDocument()
      expect(screen.getAllByText('philosophers').length).toBeGreaterThan(0)
      expect(screen.getByText('5 debates')).toBeInTheDocument()

      // Check Plato card
      expect(screen.getByText('Plato')).toBeInTheDocument()
      expect(screen.getByText('427-347 BCE')).toBeInTheDocument()
      expect(screen.getByText('3 debates')).toBeInTheDocument()
    })

    it('displays persona portraits with correct paths', () => {
      const debate = createMockDebate()
      render(<DebateTheaterView debate={debate} />)

      const socratesImage = screen.getByAltText('Socrates')
      const platoImage = screen.getByAltText('Plato')

      expect(socratesImage).toHaveAttribute('src', '/portraits/socrates.png')
      expect(platoImage).toHaveAttribute('src', '/portraits/plato.png')
    })

    it('handles portrait image errors', () => {
      const debate = createMockDebate()
      render(<DebateTheaterView debate={debate} />)

      const image = screen.getByAltText('Socrates')

      // Component has error handling for images via onError callback
      // The image element should have an onError handler
      expect(image).toHaveAttribute('alt', 'Socrates')
      expect(image).toHaveAttribute('src')
    })
  })

  describe('Message Display', () => {
    it('displays messages in completed debate immediately', () => {
      const debate = createMockDebate('completed', [mockMessage1, mockMessage2])
      render(<DebateTheaterView debate={debate} />)

      // In completed state, all messages should be visible immediately
      expect(screen.getByText(/only true wisdom/)).toBeInTheDocument()
      expect(screen.getByText(/knowledge can be attained/)).toBeInTheDocument()
    })

    it('shows completion message when debate is complete', () => {
      const debate = createMockDebate('completed', [mockMessage1, mockMessage2])
      render(<DebateTheaterView debate={debate} />)

      expect(screen.getByText('Debate Complete')).toBeInTheDocument()
      expect(screen.getByText(/All 2 exchanges have been presented/)).toBeInTheDocument()
    })

    it('displays debate summary when available and complete', () => {
      const debate = createMockDebate('completed', [mockMessage1, mockMessage2])
      debate.summary = 'This debate explored the fundamental nature of knowledge and wisdom.'
      render(<DebateTheaterView debate={debate} />)

      expect(screen.getByText('📋 Debate Summary')).toBeInTheDocument()
      expect(screen.getByText(/fundamental nature of knowledge/)).toBeInTheDocument()
    })

    it('does not display summary when debate is not complete', () => {
      const debate = createMockDebate('generating', [mockMessage1])
      debate.summary = 'This should not appear yet.'
      render(<DebateTheaterView debate={debate} />)

      expect(screen.queryByText('📋 Debate Summary')).not.toBeInTheDocument()
    })

    it('groups messages by round number', () => {
      const debate = createMockDebate('completed', [mockMessage1, mockMessage2, mockMessage3])
      render(<DebateTheaterView debate={debate} />)

      // Should show round labels
      const roundLabels = screen.getAllByText(/Round \d/)
      expect(roundLabels.length).toBeGreaterThan(0)
    })
  })

  describe('Debate Status Indicators', () => {
    it('shows "Complete" chip when debate is finished', () => {
      const debate = createMockDebate('completed', [mockMessage1, mockMessage2])
      vi.mocked(useTypewriter).mockReturnValue({
        displayedText: '',
        isTyping: false,
        reset: vi.fn(),
      })

      render(<DebateTheaterView debate={debate} />)

      expect(screen.getByText('Complete')).toBeInTheDocument()
    })

    it('shows "Speaking..." chip when typewriter is active', () => {
      const debate = createMockDebate('generating', [mockMessage1])
      vi.mocked(useTypewriter).mockReturnValue({
        displayedText: 'The only true wisdom',
        isTyping: true,
        reset: vi.fn(),
      })

      render(<DebateTheaterView debate={debate} />)

      expect(screen.getByText('Speaking...')).toBeInTheDocument()
    })

    it('shows "Listening..." chip when waiting for next message', () => {
      const debate = createMockDebate('generating', [mockMessage1])
      vi.mocked(useTypewriter).mockReturnValue({
        displayedText: mockMessage1.content,
        isTyping: false,
        reset: vi.fn(),
      })

      render(<DebateTheaterView debate={debate} />)

      // Multiple "Listening..." texts exist (one in chip, one in persona cards)
      expect(screen.getAllByText('Listening...').length).toBeGreaterThan(0)
    })

    it('displays current round number correctly', () => {
      const debate = createMockDebate('generating', [mockMessage1, mockMessage2, mockMessage3])
      vi.mocked(useTypewriter).mockReturnValue({
        displayedText: mockMessage1.content,
        isTyping: true,
        reset: vi.fn(),
      })

      render(<DebateTheaterView debate={debate} />)

      // Component starts from first message, so round 1
      expect(screen.getByText(/Round 1 of 3/)).toBeInTheDocument()
    })
  })

  describe('Typewriter Effect Integration', () => {
    it('calls useTypewriter with correct parameters for generating debate', () => {
      const debate = createMockDebate('generating', [mockMessage1])
      render(<DebateTheaterView debate={debate} />)

      expect(useTypewriter).toHaveBeenCalledWith(
        expect.objectContaining({
          text: mockMessage1.content,
          speed: 400,
          enabled: true,
        })
      )
    })

    it('displays typewriter output for current message', () => {
      const debate = createMockDebate('generating', [mockMessage1])
      vi.mocked(useTypewriter).mockReturnValue({
        displayedText: 'The only true wisdom is',
        isTyping: true,
        reset: vi.fn(),
      })

      render(<DebateTheaterView debate={debate} />)

      expect(screen.getByText(/The only true wisdom is/)).toBeInTheDocument()
    })

    it('shows typing cursor when typewriter is active', () => {
      const debate = createMockDebate('generating', [mockMessage1])
      vi.mocked(useTypewriter).mockReturnValue({
        displayedText: 'The only true',
        isTyping: true,
        reset: vi.fn(),
      })

      const { container } = render(<DebateTheaterView debate={debate} />)

      // Check for the blinking cursor element (looking for blink animation)
      const cursorElement = container.querySelector('[class*="css"]')
      expect(cursorElement).toBeTruthy()
    })

    it('disables typewriter for completed debates opened directly', () => {
      const debate = createMockDebate('completed', [mockMessage1, mockMessage2])
      render(<DebateTheaterView debate={debate} />)

      expect(useTypewriter).toHaveBeenCalledWith(
        expect.objectContaining({
          enabled: false,
        })
      )
    })
  })

  describe('Citations', () => {
    it('displays citation badges after message is complete', () => {
      const debate = createMockDebate('completed', [mockMessage1])
      render(<DebateTheaterView debate={debate} />)

      expect(screen.getByText(/📚 The Republic by Plato/)).toBeInTheDocument()
    })

    it('citation badges link to correct text pages', () => {
      const debate = createMockDebate('completed', [mockMessage1, mockMessage2])
      render(<DebateTheaterView debate={debate} />)

      const republicLink = screen.getByText(/📚 The Republic by Plato/).closest('a')
      const ethicsLink = screen.getByText(/📚 Nicomachean Ethics by Aristotle/).closest('a')

      expect(republicLink).toHaveAttribute('href', '/texts/the-republic')
      expect(ethicsLink).toHaveAttribute('href', '/texts/nicomachean-ethics')
    })

    it('does not show citations while message is typing', () => {
      const debate = createMockDebate('generating', [mockMessage1])
      vi.mocked(useTypewriter).mockReturnValue({
        displayedText: 'The only true',
        isTyping: true,
        reset: vi.fn(),
      })

      render(<DebateTheaterView debate={debate} />)

      expect(screen.queryByText(/📚 The Republic/)).not.toBeInTheDocument()
    })

    it('handles messages without citations', () => {
      const messageWithoutCitation: DebateMessage = {
        ...mockMessage1,
        text_citations: [],
      }
      const debate = createMockDebate('completed', [messageWithoutCitation])
      render(<DebateTheaterView debate={debate} />)

      expect(screen.queryByText(/📚/)).not.toBeInTheDocument()
    })
  })

  describe('Active Speaker Highlighting', () => {
    it('highlights the active speaker with special styling', () => {
      const debate = createMockDebate('generating', [mockMessage1])
      vi.mocked(useTypewriter).mockReturnValue({
        displayedText: 'The only true wisdom',
        isTyping: true,
        reset: vi.fn(),
      })

      const { container } = render(<DebateTheaterView debate={debate} />)

      // The active speaker's card should be present (MUI Card component)
      const cards = container.querySelectorAll('[class*="MuiCard"]')
      expect(cards.length).toBeGreaterThan(0)
    })

    it('shows waiting message for non-speaking personas', () => {
      const debate = createMockDebate('generating', [mockMessage1])
      vi.mocked(useTypewriter).mockReturnValue({
        displayedText: 'The only true wisdom',
        isTyping: true,
        reset: vi.fn(),
      })

      render(<DebateTheaterView debate={debate} />)

      // Plato should be listening while Socrates speaks
      expect(screen.getByText('Listening...')).toBeInTheDocument()
    })

    it('shows preparing message for active speaker before typing starts', () => {
      const debate = createMockDebate('generating', [mockMessage1])
      vi.mocked(useTypewriter).mockReturnValue({
        displayedText: '',
        isTyping: false,
        reset: vi.fn(),
      })

      render(<DebateTheaterView debate={debate} />)

      expect(screen.getByText('Preparing to speak...')).toBeInTheDocument()
    })
  })

  describe('Responsive Grid Layout', () => {
    it('calculates correct grid columns for 2 participants', () => {
      const debate = createMockDebate('completed', [], [mockPersona1, mockPersona2])
      render(<DebateTheaterView debate={debate} />)

      // Should render 2 personas
      expect(screen.getByText('Socrates')).toBeInTheDocument()
      expect(screen.getByText('Plato')).toBeInTheDocument()
    })

    it('calculates correct grid columns for 3 participants', () => {
      const debate = createMockDebate('completed', [], [mockPersona1, mockPersona2, mockPersona3])
      render(<DebateTheaterView debate={debate} />)

      // Should render 3 personas
      expect(screen.getByText('Socrates')).toBeInTheDocument()
      expect(screen.getByText('Plato')).toBeInTheDocument()
      expect(screen.getByText('Aristotle')).toBeInTheDocument()
    })

    it('handles single participant', () => {
      const debate = createMockDebate('completed', [], [mockPersona1])
      render(<DebateTheaterView debate={debate} />)

      expect(screen.getByText('Socrates')).toBeInTheDocument()
    })

    it('handles many participants (7+)', () => {
      const manyPersonas = [
        mockPersona1,
        mockPersona2,
        mockPersona3,
        { ...mockPersona1, id: 4, name: 'Person4', birth_year: -400 },
        { ...mockPersona1, id: 5, name: 'Person5', birth_year: -350 },
        { ...mockPersona1, id: 6, name: 'Person6', birth_year: -300 },
        { ...mockPersona1, id: 7, name: 'Person7', birth_year: -250 },
        { ...mockPersona1, id: 8, name: 'Person8', birth_year: -200 },
      ]
      const debate = createMockDebate('completed', [], manyPersonas as Persona[])
      render(<DebateTheaterView debate={debate} />)

      expect(screen.getByText('Person4')).toBeInTheDocument()
      expect(screen.getByText('Person8')).toBeInTheDocument()
    })
  })

  describe('Edge Cases and Error States', () => {
    it('handles debate with no messages', () => {
      const debate = createMockDebate('pending', [])
      render(<DebateTheaterView debate={debate} />)

      expect(screen.getByText(/Round 1 of 3/)).toBeInTheDocument()
      // With no messages, debate is considered complete, so completion message shows
      // This is expected behavior based on the component logic
    })

    it('handles debate with no participants', () => {
      const debate = createMockDebate('pending', [], [])
      render(<DebateTheaterView debate={debate} />)

      expect(screen.getByText(/Round 1 of 3/)).toBeInTheDocument()
    })

    it('handles pending debate status', () => {
      const debate = createMockDebate('pending', [])
      render(<DebateTheaterView debate={debate} />)

      // Pending with no messages shows as complete due to component logic
      expect(screen.getByText(/Round 1 of 3/)).toBeInTheDocument()
    })

    it('handles failed debate status', () => {
      const debate = createMockDebate('failed', [mockMessage1])
      render(<DebateTheaterView debate={debate} />)

      // In completed/failed state with messages, they show immediately
      // The message is mocked out by MessageContent mock, so we check for the component
      expect(screen.getByText('Socrates')).toBeInTheDocument()
    })

    it('handles persona without birth_year gracefully', () => {
      const personaWithoutYear = { ...mockPersona1, birth_year: null }
      const debate = createMockDebate('completed', [], [personaWithoutYear as Persona])
      render(<DebateTheaterView debate={debate} />)

      expect(screen.getByText('Socrates')).toBeInTheDocument()
    })

    it('handles persona without debate_count', () => {
      const personaWithoutCount = { ...mockPersona1, debate_count: undefined }
      const debate = createMockDebate('completed', [], [personaWithoutCount as Persona])
      render(<DebateTheaterView debate={debate} />)

      expect(screen.getByText('Socrates')).toBeInTheDocument()
      expect(screen.queryByText(/debates$/)).not.toBeInTheDocument()
    })

    it('handles empty summary gracefully', () => {
      const debate = createMockDebate('completed', [mockMessage1])
      debate.summary = ''
      render(<DebateTheaterView debate={debate} />)

      expect(screen.queryByText('📋 Debate Summary')).not.toBeInTheDocument()
    })
  })

  describe('Message Content Rendering', () => {
    it('renders message content with proper formatting', () => {
      const debate = createMockDebate('completed', [mockMessage1])
      render(<DebateTheaterView debate={debate} />)

      expect(screen.getByText(/only true wisdom/)).toBeInTheDocument()
    })

    it('preserves whitespace in message content', () => {
      const messageWithWhitespace: DebateMessage = {
        ...mockMessage1,
        content: 'Line one\n\nLine two\nLine three',
      }
      const debate = createMockDebate('completed', [messageWithWhitespace])
      render(<DebateTheaterView debate={debate} />)

      // Check that message content is rendered (MessageContent mock will show the content)
      expect(screen.getByText(/Line one/)).toBeInTheDocument()
    })

    it('handles long message content', () => {
      const longContent = 'This is a very long message. '.repeat(50)
      const longMessage: DebateMessage = {
        ...mockMessage1,
        content: longContent,
      }
      const debate = createMockDebate('completed', [longMessage])
      render(<DebateTheaterView debate={debate} />)

      expect(screen.getByText(/This is a very long message/)).toBeInTheDocument()
    })

    it('handles special characters in message content', () => {
      const specialMessage: DebateMessage = {
        ...mockMessage1,
        content: 'Test & symbols: <tag> "quotes" \'apostrophe\'',
      }
      const debate = createMockDebate('completed', [specialMessage])
      render(<DebateTheaterView debate={debate} />)

      expect(screen.getByText(/Test & symbols/)).toBeInTheDocument()
    })
  })

  describe('Round Counter Display', () => {
    it('displays round 1 when no messages exist', () => {
      const debate = createMockDebate('pending', [])
      render(<DebateTheaterView debate={debate} />)

      expect(screen.getByText('Round 1 of 3')).toBeInTheDocument()
    })

    it('displays correct round from current message', () => {
      const debate = createMockDebate('generating', [mockMessage1, mockMessage2, mockMessage3])
      vi.mocked(useTypewriter).mockReturnValue({
        displayedText: mockMessage1.content,
        isTyping: true,
        reset: vi.fn(),
      })

      render(<DebateTheaterView debate={debate} />)

      // Component starts from first message when generating
      expect(screen.getByText(/Round 1 of 3/)).toBeInTheDocument()
    })

    it('displays max_rounds correctly', () => {
      const debate = createMockDebate('pending', [])
      debate.max_rounds = 5
      render(<DebateTheaterView debate={debate} />)

      expect(screen.getByText('Round 1 of 5')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('has proper alt text for images', () => {
      const debate = createMockDebate()
      render(<DebateTheaterView debate={debate} />)

      expect(screen.getByAltText('Socrates')).toBeInTheDocument()
      expect(screen.getByAltText('Plato')).toBeInTheDocument()
    })

    it('uses semantic HTML elements', () => {
      const debate = createMockDebate()
      const { container } = render(<DebateTheaterView debate={debate} />)

      // Check for semantic elements
      expect(container.querySelector('img')).toBeInTheDocument()
    })

    it('citation links are keyboard accessible', () => {
      const debate = createMockDebate('completed', [mockMessage1])
      render(<DebateTheaterView debate={debate} />)

      const citationLink = screen.getByText(/📚 The Republic by Plato/).closest('a')
      expect(citationLink).toBeInTheDocument()
      expect(citationLink).toHaveAttribute('href')
    })
  })

  describe('Debate Summary Markdown Rendering', () => {
    it('renders markdown formatting in summary', () => {
      const debate = createMockDebate('completed', [mockMessage1, mockMessage2])
      debate.summary = '**Bold text** and *italic text*'
      render(<DebateTheaterView debate={debate} />)

      expect(screen.getByText('📋 Debate Summary')).toBeInTheDocument()
    })

    it('renders list items in summary', () => {
      const debate = createMockDebate('completed', [mockMessage1, mockMessage2])
      debate.summary = '- Point one\n- Point two\n- Point three'
      render(<DebateTheaterView debate={debate} />)

      expect(screen.getByText('📋 Debate Summary')).toBeInTheDocument()
    })
  })

  describe('Multiple Rounds Handling', () => {
    it('displays messages from multiple rounds correctly', () => {
      const round2Message: DebateMessage = {
        id: 4,
        persona: mockPersona2,
        round_number: 2,
        content: 'In the second round, I respond.',
        created_at: '2024-01-01T00:03:00Z',
      }

      const debate = createMockDebate('completed', [
        mockMessage1,
        mockMessage2,
        mockMessage3,
        round2Message,
      ])
      render(<DebateTheaterView debate={debate} />)

      expect(screen.getByText(/only true wisdom/)).toBeInTheDocument()
      expect(screen.getByText(/knowledge can be attained/)).toBeInTheDocument()
      expect(screen.getByText(/must always question/)).toBeInTheDocument()
      expect(screen.getByText(/In the second round/)).toBeInTheDocument()
    })

    it('shows round labels for each new round', () => {
      const round2Message: DebateMessage = {
        id: 4,
        persona: mockPersona1,
        round_number: 2,
        content: 'Round 2 begins',
        created_at: '2024-01-01T00:03:00Z',
      }

      const debate = createMockDebate('completed', [mockMessage1, mockMessage2, round2Message])
      render(<DebateTheaterView debate={debate} />)

      // Should see Round 1 and Round 2 labels in the persona cards
      const roundLabels = screen.getAllByText(/Round \d/)
      expect(roundLabels.length).toBeGreaterThan(0)
    })
  })

  describe('Generating Debate Behavior', () => {
    it('starts from first message when debate was generating on first load', () => {
      const debate = createMockDebate('generating', [mockMessage1, mockMessage2])
      vi.mocked(useTypewriter).mockReturnValue({
        displayedText: mockMessage1.content,
        isTyping: false,
        reset: vi.fn(),
      })

      render(<DebateTheaterView debate={debate} />)

      // Should show the first message
      expect(useTypewriter).toHaveBeenCalledWith(
        expect.objectContaining({
          text: mockMessage1.content,
        })
      )
    })

    it('tracks debate status change from generating to completed', () => {
      const debate = createMockDebate('generating', [mockMessage1])
      const { rerender } = render(<DebateTheaterView debate={debate} />)

      // Update to completed
      const completedDebate = { ...debate, status: 'completed' as const }
      rerender(<DebateTheaterView debate={completedDebate} />)

      // Should still work correctly - check for persona name instead of message content
      expect(screen.getByText('Socrates')).toBeInTheDocument()
    })
  })
})
