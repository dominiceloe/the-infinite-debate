import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import TopicSelector from '@/components/debates/create/TopicSelector';

describe('TopicSelector', () => {
  const mockOnTitleChange = vi.fn();
  const mockOnTopicChange = vi.fn();

  const defaultProps = {
    title: '',
    topic: '',
    onTitleChange: mockOnTitleChange,
    onTopicChange: mockOnTopicChange,
  };

  it('renders title and topic inputs', () => {
    render(<TopicSelector {...defaultProps} />);

    expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/topic \/ question/i)).toBeInTheDocument();
  });

  it('displays current title and topic values', () => {
    render(
      <TopicSelector
        {...defaultProps}
        title="Test Debate"
        topic="Test Question?"
      />
    );

    expect(screen.getByDisplayValue('Test Debate')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Test Question?')).toBeInTheDocument();
  });

  it('calls onTitleChange when title input changes', () => {
    render(<TopicSelector {...defaultProps} />);

    const titleInput = screen.getByLabelText(/title/i);
    fireEvent.change(titleInput, { target: { value: 'New Title' } });

    expect(mockOnTitleChange).toHaveBeenCalledWith('New Title');
  });

  it('calls onTopicChange when topic input changes', () => {
    render(<TopicSelector {...defaultProps} />);

    const topicInput = screen.getByLabelText(/topic \/ question/i);
    fireEvent.change(topicInput, { target: { value: 'New Topic' } });

    expect(mockOnTopicChange).toHaveBeenCalledWith('New Topic');
  });

  it('has required attribute on inputs', () => {
    render(<TopicSelector {...defaultProps} />);

    expect(screen.getByLabelText(/title/i)).toBeRequired();
    expect(screen.getByLabelText(/topic \/ question/i)).toBeRequired();
  });

  it('renders with correct placeholder text', () => {
    render(<TopicSelector {...defaultProps} />);

    expect(screen.getByPlaceholderText(/e\.g\., The Nature of Reality/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/What is the nature of reality/i)).toBeInTheDocument();
  });
});
