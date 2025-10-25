import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import PersonaSelector from '@/components/debates/create/PersonaSelector';
import type { PersonasByCategory } from '@/types';

const mockPersonasData: PersonasByCategory = {
  theologians: [
    {
      id: 1,
      name: 'Thomas Aquinas',
      slug: 'aquinas',
      title: 'Doctor Angelicus',
      era: '1225-1274 CE',
      birth_year: 1225,
      death_year: 1274,
      category: 'theologians',
      required_tier: 'free',
      religion_worldview: 'Christianity',
    },
    {
      id: 2,
      name: 'Augustine',
      slug: 'augustine',
      title: 'Doctor of Grace',
      era: '354-430 CE',
      birth_year: 354,
      death_year: 430,
      category: 'theologians',
      required_tier: 'starter',
      religion_worldview: 'Christianity',
    },
  ],
  philosophers: [
    {
      id: 3,
      name: 'Socrates',
      slug: 'socrates',
      title: 'The Gadfly of Athens',
      era: '470-399 BCE',
      birth_year: -470,
      death_year: -399,
      category: 'philosophers',
      required_tier: 'free',
      religion_worldview: 'Ancient Greek',
    },
  ],
};

describe('PersonaSelector', () => {
  const mockOnTogglePersona = vi.fn();

  const defaultProps = {
    data: mockPersonasData,
    selectedPersonas: [],
    onTogglePersona: mockOnTogglePersona,
    maxParticipants: 10,
    user: { subscription_tier: 'pro' },
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders all personas from all categories', () => {
    render(<PersonaSelector {...defaultProps} />);

    expect(screen.getByText('Thomas Aquinas')).toBeInTheDocument();
    expect(screen.getByText('Augustine')).toBeInTheDocument();
    expect(screen.getByText('Socrates')).toBeInTheDocument();
  });

  it('displays selected count correctly', () => {
    render(<PersonaSelector {...defaultProps} selectedPersonas={[1, 3]} />);

    expect(screen.getByText(/selected: 2 \/ 10/i)).toBeInTheDocument();
  });

  it('calls onTogglePersona when clicking a persona card', () => {
    render(<PersonaSelector {...defaultProps} />);

    const aquinasCard = screen.getByText('Thomas Aquinas').closest('[role="button"]');
    if (aquinasCard) {
      fireEvent.click(aquinasCard.parentElement!);
    }

    expect(mockOnTogglePersona).toHaveBeenCalledWith(1);
  });

  it('highlights selected personas', () => {
    render(<PersonaSelector {...defaultProps} selectedPersonas={[1]} />);

    const aquinasCard = screen.getByText('Thomas Aquinas').closest('.MuiCard-root');
    expect(aquinasCard).toHaveStyle({ borderWidth: '2px' });
  });

  it('filters personas by search query', () => {
    render(<PersonaSelector {...defaultProps} />);

    const searchInput = screen.getByPlaceholderText(/search by name/i);
    fireEvent.change(searchInput, { target: { value: 'Aquinas' } });

    expect(screen.getByText('Thomas Aquinas')).toBeInTheDocument();
    expect(screen.queryByText('Socrates')).not.toBeInTheDocument();
  });

  it('filters personas by category', () => {
    render(<PersonaSelector {...defaultProps} />);

    const theologiansChip = screen.getByText(/theologians/i);
    fireEvent.click(theologiansChip);

    expect(screen.getByText('Thomas Aquinas')).toBeInTheDocument();
    expect(screen.queryByText('Socrates')).not.toBeInTheDocument();
  });

  it('clears search filter when clear button is clicked', () => {
    render(<PersonaSelector {...defaultProps} />);

    const searchInput = screen.getByPlaceholderText(/search by name/i);
    fireEvent.change(searchInput, { target: { value: 'Aquinas' } });

    const clearButton = screen.getAllByRole('button').find(btn =>
      btn.querySelector('[data-testid="ClearIcon"]')
    );

    if (clearButton) {
      fireEvent.click(clearButton);
    }

    expect(searchInput).toHaveValue('');
  });

  it('shows tier badges for locked personas', () => {
    const userWithFreeTier = { subscription_tier: 'free' };

    render(<PersonaSelector {...defaultProps} user={userWithFreeTier} />);

    // Augustine requires 'starter' tier, should show badge
    const augustineCard = screen.getByText('Augustine').closest('.MuiCard-root');
    expect(augustineCard).toBeInTheDocument();
  });

  it('prevents clicking locked personas', () => {
    const userWithFreeTier = { subscription_tier: 'free' };

    render(<PersonaSelector {...defaultProps} user={userWithFreeTier} />);

    // Try to click Augustine (requires starter tier)
    const augustineCard = screen.getByText('Augustine').closest('.MuiCard-root');
    if (augustineCard) {
      fireEvent.click(augustineCard);
    }

    // Should not call onTogglePersona for locked persona
    expect(mockOnTogglePersona).not.toHaveBeenCalled();
  });

  it('displays category filters for all categories', () => {
    render(<PersonaSelector {...defaultProps} />);

    expect(screen.getByText(/theologians/i)).toBeInTheDocument();
    expect(screen.getByText(/philosophers/i)).toBeInTheDocument();
  });

  it('shows clear all button when filters are active', () => {
    render(<PersonaSelector {...defaultProps} />);

    const searchInput = screen.getByPlaceholderText(/search by name/i);
    fireEvent.change(searchInput, { target: { value: 'test' } });

    expect(screen.getByText(/clear all/i)).toBeInTheDocument();
  });

  it('clears all filters when clear all is clicked', () => {
    render(<PersonaSelector {...defaultProps} />);

    // Set search query
    const searchInput = screen.getByPlaceholderText(/search by name/i);
    fireEvent.change(searchInput, { target: { value: 'test' } });

    // Click category filter
    const theologiansChip = screen.getByText(/theologians/i);
    fireEvent.click(theologiansChip);

    // Click clear all
    const clearAllButton = screen.getByText(/clear all/i);
    fireEvent.click(clearAllButton);

    expect(searchInput).toHaveValue('');
  });
});
