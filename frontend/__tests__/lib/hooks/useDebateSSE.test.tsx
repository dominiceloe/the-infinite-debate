import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useDebateSSE } from '@/lib/hooks/useDebateSSE';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import type { Debate, Persona } from '@/types';

// Track EventSource instances for testing
let mockEventSourceInstance: MockEventSource | null = null;

// Mock EventSource
class MockEventSource {
  url: string;
  onopen: (() => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  readyState: number = 0;

  constructor(url: string) {
    this.url = url;
    // eslint-disable-next-line @typescript-eslint/no-this-alias
    mockEventSourceInstance = this; // Track the instance for test assertions
    // Simulate async connection
    setTimeout(() => {
      this.readyState = 1;
      if (this.onopen) {
        this.onopen();
      }
    }, 10);
  }

  close() {
    this.readyState = 2;
  }

  // Helper to simulate incoming messages
  simulateMessage(data: unknown) {
    if (this.onmessage) {
      const event = new MessageEvent('message', {
        data: JSON.stringify(data),
      });
      this.onmessage(event);
    }
  }

  // Helper to simulate errors
  simulateError() {
    if (this.onerror) {
      this.onerror(new Event('error'));
    }
  }
}

// Replace global EventSource with mock
vi.stubGlobal('EventSource', MockEventSource);

describe('useDebateSSE', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
    mockEventSourceInstance = null; // Reset instance tracker
  });

  afterEach(() => {
    queryClient.clear();
    vi.clearAllMocks();
    mockEventSourceInstance = null;
  });

  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it('should connect to SSE endpoint when enabled', async () => {
    const { result } = renderHook(
      () =>
        useDebateSSE({
          slug: 'test-debate',
          enabled: true,
        }),
      { wrapper }
    );

    // Initially not connected
    expect(result.current.isConnected).toBe(false);

    // Wait for connection
    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    expect(mockEventSourceInstance).toBeTruthy();
    expect(mockEventSourceInstance?.url).toContain('/debates/test-debate/stream/');
  });

  it('should not connect when disabled', () => {
    const { result } = renderHook(
      () =>
        useDebateSSE({
          slug: 'test-debate',
          enabled: false,
        }),
      { wrapper }
    );

    expect(result.current.isConnected).toBe(false);
    expect(mockEventSourceInstance).toBeNull();
  });

  it('should handle incoming status messages', async () => {
    const onMessage = vi.fn();

    // Setup initial debate in cache
    const initialDebate: Debate = {
      id: 1,
      title: 'Test Debate',
      topic: 'What is truth?',
      slug: 'test-debate',
      participants: [],
      depth_level: 'intermediate',
      max_rounds: 5,
      transcript: '',
      summary: '',
      status: 'generating',
      rounds_completed: 0,
      error_message: '',
      messages: [],
      created_at: '2025-10-26T10:00:00Z',
      updated_at: '2025-10-26T10:00:00Z',
      completed_at: null,
    };
    queryClient.setQueryData(['debate', 'test-debate'], initialDebate);

    const { result } = renderHook(
      () =>
        useDebateSSE({
          slug: 'test-debate',
          enabled: true,
          onMessage,
        }),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Simulate status message
    mockEventSourceInstance?.simulateMessage({
      type: 'status',
      status: 'generating',
      rounds_completed: 2,
      max_rounds: 5,
    });

    await waitFor(() => {
      expect(onMessage).toHaveBeenCalledWith({
        type: 'status',
        status: 'generating',
        rounds_completed: 2,
        max_rounds: 5,
      });
    });

    // Verify cache was updated
    const updatedDebate = queryClient.getQueryData<Debate>(['debate', 'test-debate']);
    expect(updatedDebate?.status).toBe('generating');
    expect(updatedDebate?.rounds_completed).toBe(2);
  });

  it('should add message to cache directly without refetching', async () => {
    // Setup initial debate in cache with existing messages
    const mockPersona: Persona = {
      id: 1,
      name: 'Socrates',
      slug: 'socrates',
      title: 'The Gadfly of Athens',
      category: 'philosophers',
      era: 'Ancient Greece',
      birth_year: -470,
      death_year: -399,
      religion_worldview: 'Greek Philosophy',
    };

    const initialDebate: Debate = {
      id: 1,
      title: 'Test Debate',
      topic: 'What is knowledge?',
      slug: 'test-debate',
      participants: [mockPersona],
      depth_level: 'intermediate',
      max_rounds: 5,
      transcript: '',
      summary: '',
      status: 'generating',
      rounds_completed: 1,
      error_message: '',
      messages: [
        {
          id: 1,
          persona: mockPersona,
          round_number: 1,
          content: 'First message',
          created_at: '2025-10-26T10:00:00Z',
        },
      ],
      created_at: '2025-10-26T10:00:00Z',
      updated_at: '2025-10-26T10:00:00Z',
      completed_at: null,
    };
    queryClient.setQueryData(['debate', 'test-debate'], initialDebate);

    // Spy on setQueryData to verify it was called
    const setQueryDataSpy = vi.spyOn(queryClient, 'setQueryData');
    // Spy on invalidateQueries to verify it was NOT called for message events
    const invalidateQueriesSpy = vi.spyOn(queryClient, 'invalidateQueries');

    const { result } = renderHook(
      () =>
        useDebateSSE({
          slug: 'test-debate',
          enabled: true,
        }),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Simulate message event
    mockEventSourceInstance?.simulateMessage({
      type: 'message',
      message_id: 2,
      persona_name: 'Plato',
      persona_slug: 'plato',
      round_number: 2,
      content: 'Second message from Plato',
    });

    await waitFor(() => {
      const updatedDebate = queryClient.getQueryData<Debate>(['debate', 'test-debate']);
      expect(updatedDebate?.messages?.length).toBe(2);
    });

    // Verify setQueryData was called for the message
    expect(setQueryDataSpy).toHaveBeenCalledWith(
      ['debate', 'test-debate'],
      expect.any(Function)
    );

    // Verify invalidateQueries was NOT called for message events
    // (it should only be called on completion/failed status)
    expect(invalidateQueriesSpy).not.toHaveBeenCalled();

    // Verify the new message was added correctly
    const updatedDebate = queryClient.getQueryData<Debate>(['debate', 'test-debate']);
    expect(updatedDebate?.messages?.length).toBe(2);

    const newMessage = updatedDebate?.messages?.[1];
    expect(newMessage).toEqual({
      id: 2,
      round_number: 2,
      content: 'Second message from Plato',
      persona: {
        name: 'Plato',
        slug: 'plato',
      },
      created_at: expect.any(String),
    });
  });

  it('should prevent duplicate messages', async () => {
    const mockPersona: Persona = {
      id: 1,
      name: 'Aristotle',
      slug: 'aristotle',
      title: 'The Philosopher',
      category: 'philosophers',
      era: 'Ancient Greece',
      birth_year: -384,
      death_year: -322,
      religion_worldview: 'Greek Philosophy',
    };

    const initialDebate: Debate = {
      id: 1,
      title: 'Test Debate',
      topic: 'What is virtue?',
      slug: 'test-debate',
      participants: [mockPersona],
      depth_level: 'intermediate',
      max_rounds: 5,
      transcript: '',
      summary: '',
      status: 'generating',
      rounds_completed: 1,
      error_message: '',
      messages: [
        {
          id: 42,
          persona: mockPersona,
          round_number: 1,
          content: 'Existing message',
          created_at: '2025-10-26T10:00:00Z',
        },
      ],
      created_at: '2025-10-26T10:00:00Z',
      updated_at: '2025-10-26T10:00:00Z',
      completed_at: null,
    };
    queryClient.setQueryData(['debate', 'test-debate'], initialDebate);

    const { result } = renderHook(
      () =>
        useDebateSSE({
          slug: 'test-debate',
          enabled: true,
        }),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Simulate message event with duplicate message_id
    mockEventSourceInstance?.simulateMessage({
      type: 'message',
      message_id: 42, // Same ID as existing message
      persona_name: 'Aristotle',
      persona_slug: 'aristotle',
      round_number: 1,
      content: 'Duplicate attempt',
    });

    await waitFor(() => {
      // Wait a bit to ensure handler executed
    }, { timeout: 100 });

    // Verify message was NOT added (still only 1 message)
    const updatedDebate = queryClient.getQueryData<Debate>(['debate', 'test-debate']);
    expect(updatedDebate?.messages?.length).toBe(1);
    expect(updatedDebate?.messages?.[0].content).toBe('Existing message');
  });

  it('should handle missing cache gracefully', async () => {
    // No debate in cache initially

    const { result } = renderHook(
      () =>
        useDebateSSE({
          slug: 'test-debate',
          enabled: true,
        }),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Simulate message event when cache is empty
    expect(() => {
      mockEventSourceInstance?.simulateMessage({
        type: 'message',
        message_id: 1,
        persona_name: 'Confucius',
        persona_slug: 'confucius',
        round_number: 1,
        content: 'Message to empty cache',
      });
    }).not.toThrow();

    // Verify cache remains undefined
    const updatedDebate = queryClient.getQueryData<Debate>(['debate', 'test-debate']);
    expect(updatedDebate).toBeUndefined();
  });

  it('should include correct persona data from SSE event', async () => {
    const initialDebate: Debate = {
      id: 1,
      title: 'Test Debate',
      topic: 'What is the good life?',
      slug: 'test-debate',
      participants: [],
      depth_level: 'intermediate',
      max_rounds: 5,
      transcript: '',
      summary: '',
      status: 'generating',
      rounds_completed: 0,
      error_message: '',
      messages: [],
      created_at: '2025-10-26T10:00:00Z',
      updated_at: '2025-10-26T10:00:00Z',
      completed_at: null,
    };
    queryClient.setQueryData(['debate', 'test-debate'], initialDebate);

    const { result } = renderHook(
      () =>
        useDebateSSE({
          slug: 'test-debate',
          enabled: true,
        }),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Simulate message with specific persona data
    mockEventSourceInstance?.simulateMessage({
      type: 'message',
      message_id: 100,
      persona_name: 'Thomas Aquinas',
      persona_slug: 'aquinas',
      round_number: 3,
      content: 'The five ways demonstrate...',
    });

    await waitFor(() => {
      const updatedDebate = queryClient.getQueryData<Debate>(['debate', 'test-debate']);
      expect(updatedDebate?.messages?.length).toBe(1);
    });

    const updatedDebate = queryClient.getQueryData<Debate>(['debate', 'test-debate']);
    const message = updatedDebate?.messages?.[0];

    expect(message?.id).toBe(100);
    expect(message?.round_number).toBe(3);
    expect(message?.content).toBe('The five ways demonstrate...');
    expect(message?.persona).toEqual({
      name: 'Thomas Aquinas',
      slug: 'aquinas',
    });
    expect(message?.created_at).toBeTruthy();
  });

  it('should handle empty old messages array gracefully', async () => {
    // Debate with undefined messages array
    const initialDebate: Debate = {
      id: 1,
      title: 'Test Debate',
      topic: 'What is being?',
      slug: 'test-debate',
      participants: [],
      depth_level: 'intermediate',
      max_rounds: 5,
      transcript: '',
      summary: '',
      status: 'generating',
      rounds_completed: 0,
      error_message: '',
      // messages is undefined (not initialized)
      created_at: '2025-10-26T10:00:00Z',
      updated_at: '2025-10-26T10:00:00Z',
      completed_at: null,
    };
    queryClient.setQueryData(['debate', 'test-debate'], initialDebate);

    const { result } = renderHook(
      () =>
        useDebateSSE({
          slug: 'test-debate',
          enabled: true,
        }),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Simulate message event
    mockEventSourceInstance?.simulateMessage({
      type: 'message',
      message_id: 1,
      persona_name: 'Nagarjuna',
      persona_slug: 'nagarjuna',
      round_number: 1,
      content: 'All phenomena are empty...',
    });

    await waitFor(() => {
      const updatedDebate = queryClient.getQueryData<Debate>(['debate', 'test-debate']);
      expect(updatedDebate?.messages?.length).toBe(1);
    });

    // Verify message was added despite undefined messages array
    const updatedDebate = queryClient.getQueryData<Debate>(['debate', 'test-debate']);
    expect(updatedDebate?.messages?.length).toBe(1);
    expect(updatedDebate?.messages?.[0].content).toBe('All phenomena are empty...');
  });

  it('should call onError callback on connection error', async () => {
    const onError = vi.fn();
    renderHook(
      () =>
        useDebateSSE({
          slug: 'test-debate',
          enabled: true,
          onError,
        }),
      { wrapper }
    );

    await waitFor(() => {
      expect(mockEventSourceInstance).toBeTruthy();
    });

    // Simulate error
    mockEventSourceInstance?.simulateError();

    await waitFor(() => {
      expect(onError).toHaveBeenCalledWith(expect.any(Error));
    });
  });

  it('should close connection on unmount', async () => {
    const { unmount } = renderHook(
      () =>
        useDebateSSE({
          slug: 'test-debate',
          enabled: true,
        }),
      { wrapper }
    );

    await waitFor(() => {
      expect(mockEventSourceInstance).toBeTruthy();
    });

    const closeSpy = vi.spyOn(mockEventSourceInstance!, 'close');

    unmount();

    expect(closeSpy).toHaveBeenCalled();
    expect(mockEventSourceInstance?.readyState).toBe(2); // CLOSED
  });

  it('should close connection and invalidate cache on completion status', async () => {
    const initialDebate: Debate = {
      id: 1,
      title: 'Test Debate',
      topic: 'What is reality?',
      slug: 'test-debate',
      participants: [],
      depth_level: 'intermediate',
      max_rounds: 5,
      transcript: '',
      summary: '',
      status: 'generating',
      rounds_completed: 0,
      error_message: '',
      messages: [],
      created_at: '2025-10-26T10:00:00Z',
      updated_at: '2025-10-26T10:00:00Z',
      completed_at: null,
    };
    queryClient.setQueryData(['debate', 'test-debate'], initialDebate);

    const invalidateQueriesSpy = vi.spyOn(queryClient, 'invalidateQueries');

    const { result } = renderHook(
      () =>
        useDebateSSE({
          slug: 'test-debate',
          enabled: true,
        }),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    const closeSpy = vi.spyOn(mockEventSourceInstance!, 'close');

    // Simulate completion status
    mockEventSourceInstance?.simulateMessage({
      type: 'status',
      status: 'completed',
      rounds_completed: 5,
      max_rounds: 5,
    });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(false);
    });

    // Verify connection was closed
    expect(closeSpy).toHaveBeenCalled();

    // Verify invalidateQueries was called on completion
    expect(invalidateQueriesSpy).toHaveBeenCalledWith({
      queryKey: ['debate', 'test-debate'],
    });
  });
});
