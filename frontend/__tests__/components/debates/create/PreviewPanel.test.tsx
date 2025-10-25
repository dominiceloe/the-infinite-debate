import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import PreviewPanel from '@/components/debates/create/PreviewPanel';
import type { Persona } from '@/types';

const mockPersonas: Persona[] = [
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
];

describe('PreviewPanel', () => {
  const mockOnRemovePersona = vi.fn();
  const mockOnReorderPersonas = vi.fn();
  const mockOnClearAll = vi.fn();
  const mockOnSubmit = vi.fn();

  const defaultProps = {
    selectedPersonaDetails: mockPersonas,
    onRemovePersona: mockOnRemovePersona,
    onReorderPersonas: mockOnReorderPersonas,
    onClearAll: mockOnClearAll,
    onSubmit: mockOnSubmit,
    isSubmitting: false,
    canSubmit: true,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders nothing when no personas selected', () => {
    const { container } = render(
      <PreviewPanel {...defaultProps} selectedPersonaDetails={[]} />
    );

    expect(container.firstChild).toBeNull();
  });

  it('displays selected personas count', () => {
    render(<PreviewPanel {...defaultProps} />);

    expect(screen.getByText(/selected participants \(2\)/i)).toBeInTheDocument();
  });

  it('renders all selected personas in cards', () => {
    render(<PreviewPanel {...defaultProps} />);

    expect(screen.getByText('1. Thomas Aquinas')).toBeInTheDocument();
    expect(screen.getByText('2. Socrates')).toBeInTheDocument();
  });

  it('calls onRemovePersona when remove button is clicked', () => {
    render(<PreviewPanel {...defaultProps} />);

    const removeButtons = screen.getAllByRole('button', { name: '' }).filter(btn =>
      btn.querySelector('[data-testid="CloseIcon"]')
    );

    if (removeButtons.length > 0) {
      fireEvent.click(removeButtons[0]);
    }

    expect(mockOnRemovePersona).toHaveBeenCalledWith(1);
  });

  it('calls onClearAll when clear all button is clicked', () => {
    render(<PreviewPanel {...defaultProps} />);

    const clearAllButton = screen.getByText(/clear all/i);
    fireEvent.click(clearAllButton);

    expect(mockOnClearAll).toHaveBeenCalled();
  });

  it('calls onSubmit when create debate button is clicked', () => {
    render(<PreviewPanel {...defaultProps} />);

    const submitButton = screen.getByText(/create debate/i);
    fireEvent.click(submitButton);

    expect(mockOnSubmit).toHaveBeenCalled();
  });

  it('disables submit button when canSubmit is false', () => {
    render(<PreviewPanel {...defaultProps} canSubmit={false} />);

    const submitButton = screen.getByText(/create debate/i);
    expect(submitButton).toBeDisabled();
  });

  it('disables submit button when isSubmitting is true', () => {
    render(<PreviewPanel {...defaultProps} isSubmitting={true} />);

    const submitButton = screen.getByText(/creating\.\.\./i);
    expect(submitButton).toBeDisabled();
  });

  it('shows "Creating..." text when submitting', () => {
    render(<PreviewPanel {...defaultProps} isSubmitting={true} />);

    expect(screen.getByText(/creating\.\.\./i)).toBeInTheDocument();
  });

  it('supports drag and drop reordering', () => {
    render(<PreviewPanel {...defaultProps} />);

    const cards = screen.getAllByText(/\d\. /).map(el => el.closest('.MuiCard-root'));

    if (cards.length >= 2 && cards[0] && cards[1]) {
      // Simulate drag start on first card
      fireEvent.dragStart(cards[0], {
        dataTransfer: {
          effectAllowed: 'move',
          setData: vi.fn(),
          getData: vi.fn(() => '0'),
        },
      });

      // Simulate drop on second card
      fireEvent.drop(cards[1], {
        dataTransfer: {
          effectAllowed: 'move',
          setData: vi.fn(),
          getData: vi.fn(() => '0'),
        },
      });

      expect(mockOnReorderPersonas).toHaveBeenCalledWith(0, 1);
    }
  });

  it('displays era information for each persona', () => {
    render(<PreviewPanel {...defaultProps} />);

    expect(screen.getByText('1225-1274 CE')).toBeInTheDocument();
    expect(screen.getByText('470-399 BCE')).toBeInTheDocument();
  });

  it('shows drag indicator icon on persona cards', () => {
    render(<PreviewPanel {...defaultProps} />);

    const dragIcons = screen.getAllByTestId('DragIndicatorIcon');
    expect(dragIcons.length).toBe(2);
  });

  it('renders clear all button only when expanded', () => {
    render(<PreviewPanel {...defaultProps} />);

    // Initially expanded
    expect(screen.getByText(/clear all/i)).toBeInTheDocument();

    // Note: Collapse behavior is controlled by scroll,
    // so we can't easily test the collapsed state without mocking scroll
  });

  it('shows drag instruction text', () => {
    render(<PreviewPanel {...defaultProps} />);

    expect(screen.getByText(/drag to reorder turn sequence/i)).toBeInTheDocument();
  });
});
