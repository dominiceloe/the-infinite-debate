import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import SettingsForm from '@/components/debates/create/SettingsForm';

describe('SettingsForm', () => {
  const mockOnDepthLevelChange = vi.fn();
  const mockOnMaxRoundsChange = vi.fn();

  const defaultProps = {
    depthLevel: 'introductory' as const,
    maxRounds: 3,
    onDepthLevelChange: mockOnDepthLevelChange,
    onMaxRoundsChange: mockOnMaxRoundsChange,
    allowedDepths: ['introductory', 'intermediate', 'advanced'],
    maxRoundsLimit: 10,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders depth level and max rounds inputs', () => {
    render(<SettingsForm {...defaultProps} />);

    expect(screen.getByLabelText(/depth level/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/max rounds/i)).toBeInTheDocument();
  });

  it('displays current depth level value', () => {
    render(<SettingsForm {...defaultProps} depthLevel="intermediate" />);

    const select = screen.getByLabelText(/depth level/i);
    expect(select).toHaveValue('intermediate');
  });

  it('displays current max rounds value', () => {
    render(<SettingsForm {...defaultProps} maxRounds={5} />);

    expect(screen.getByLabelText(/max rounds/i)).toHaveValue(5);
  });

  it('calls onDepthLevelChange when depth level changes', () => {
    render(<SettingsForm {...defaultProps} />);

    const select = screen.getByLabelText(/depth level/i);
    fireEvent.change(select, { target: { value: 'advanced' } });

    expect(mockOnDepthLevelChange).toHaveBeenCalledWith('advanced');
  });

  it('calls onMaxRoundsChange when max rounds changes', () => {
    render(<SettingsForm {...defaultProps} />);

    const input = screen.getByLabelText(/max rounds/i);
    fireEvent.change(input, { target: { value: '7' } });

    expect(mockOnMaxRoundsChange).toHaveBeenCalledWith(7);
  });

  it('disables depth levels not in allowedDepths', () => {
    render(
      <SettingsForm
        {...defaultProps}
        allowedDepths={['introductory']}
      />
    );

    // Open the select menu
    const select = screen.getByLabelText(/depth level/i);
    fireEvent.mouseDown(select);

    // Check that intermediate and advanced are disabled
    const intermediateOption = screen.getByRole('option', { name: /intermediate/i });
    const advancedOption = screen.getByRole('option', { name: /advanced/i });

    expect(intermediateOption).toHaveAttribute('aria-disabled', 'true');
    expect(advancedOption).toHaveAttribute('aria-disabled', 'true');
  });

  it('clamps max rounds to 1 when empty string is entered', () => {
    render(<SettingsForm {...defaultProps} />);

    const input = screen.getByLabelText(/max rounds/i);
    fireEvent.change(input, { target: { value: '' } });

    expect(mockOnMaxRoundsChange).toHaveBeenCalledWith(1);
  });

  it('clamps max rounds to maxRoundsLimit', () => {
    render(<SettingsForm {...defaultProps} maxRoundsLimit={5} />);

    const input = screen.getByLabelText(/max rounds/i);
    fireEvent.change(input, { target: { value: '10' } });

    expect(mockOnMaxRoundsChange).toHaveBeenCalledWith(5);
  });

  it('clamps max rounds to minimum of 1', () => {
    render(<SettingsForm {...defaultProps} />);

    const input = screen.getByLabelText(/max rounds/i);
    fireEvent.change(input, { target: { value: '-5' } });

    expect(mockOnMaxRoundsChange).toHaveBeenCalledWith(1);
  });

  it('shows tier requirements for locked depth levels', () => {
    render(
      <SettingsForm
        {...defaultProps}
        allowedDepths={['introductory']}
      />
    );

    // Open the select menu
    const select = screen.getByLabelText(/depth level/i);
    fireEvent.mouseDown(select);

    expect(screen.getByText(/intermediate \(starter\+\)/i)).toBeInTheDocument();
    expect(screen.getByText(/advanced \(pro\+\)/i)).toBeInTheDocument();
  });
});
