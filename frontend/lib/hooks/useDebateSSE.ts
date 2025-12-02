import { useEffect, useRef, useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import type { Debate } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api';

interface SSEMessage {
  type: 'status' | 'message' | 'error';
  status?: 'generating' | 'completed' | 'failed';
  rounds_completed?: number;
  max_rounds?: number;
  error_message?: string;
  message_id?: number;
  persona_id?: number;
  persona_name?: string;
  persona_slug?: string;
  round_number?: number;
  content?: string;
}

interface UseDebateSSEOptions {
  slug: string;
  enabled?: boolean;
  onMessage?: (message: SSEMessage) => void;
  onError?: (error: Error) => void;
}

interface UseDebateSSEResult {
  isConnected: boolean;
  lastMessage: SSEMessage | null;
  error: Error | null;
  reconnect: () => void;
}

export function useDebateSSE({
  slug,
  enabled = true,
  onMessage,
  onError,
}: UseDebateSSEOptions): UseDebateSSEResult {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<SSEMessage | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const queryClient = useQueryClient();

  const connect = useCallback(() => {
    if (!enabled || eventSourceRef.current) {
      return;
    }

    try {
      const url = `${API_URL}/debates/${slug}/stream/`;
      const eventSource = new EventSource(url, { withCredentials: true });

      eventSource.onopen = () => {
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;
      };

      eventSource.onmessage = (event) => {
        try {
          const message: SSEMessage = JSON.parse(event.data);
          setLastMessage(message);

          // Call optional message handler
          if (onMessage) {
            onMessage(message);
          }

          // Update React Query cache based on message type
          if (message.type === 'status') {
            queryClient.setQueryData(['debate', slug], (old: Debate | undefined) => {
              if (!old) return old;
              return {
                ...old,
                status: message.status || old.status,
                rounds_completed: message.rounds_completed ?? old.rounds_completed,
                error_message: message.error_message || old.error_message,
              };
            });

            // Close connection if debate is completed or failed
            if (message.status === 'completed' || message.status === 'failed') {
              eventSource.close();
              setIsConnected(false);
              // Trigger a full refetch to get complete data
              queryClient.invalidateQueries({ queryKey: ['debate', slug] });
            }
          } else if (message.type === 'message') {
            // Optimistically add message to cache for real-time display
            queryClient.setQueryData(['debate', slug], (old: Debate | undefined) => {
              if (!old) return old;

              // Check if message already exists (avoid duplicates)
              const messageExists = old.messages?.some(m => m.id === message.message_id);
              if (messageExists) return old;

              // Create new message object from SSE event data
              const newMessage = {
                id: message.message_id!,
                round_number: message.round_number!,
                content: message.content!,
                persona: {
                  id: message.persona_id!,
                  name: message.persona_name!,
                  slug: message.persona_slug!,
                },
                created_at: new Date().toISOString(),
              };

              // Return updated debate with new message appended
              return {
                ...old,
                messages: [...(old.messages || []), newMessage],
              };
            });
          }
        } catch (err) {
          console.error('Failed to parse SSE message:', err);
        }
      };

      eventSource.onerror = (err) => {
        console.error('SSE error:', err);
        eventSource.close();
        setIsConnected(false);

        const errorObj = new Error('SSE connection error');
        setError(errorObj);

        if (onError) {
          onError(errorObj);
        }

        // Implement exponential backoff for reconnection
        const maxAttempts = 5;
        const baseDelay = 1000; // 1 second
        const maxDelay = 30000; // 30 seconds

        if (reconnectAttemptsRef.current < maxAttempts) {
          const delay = Math.min(
            baseDelay * Math.pow(2, reconnectAttemptsRef.current),
            maxDelay
          );

          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current += 1;
            eventSourceRef.current = null;
            connect();
          }, delay);
        }
      };

      eventSourceRef.current = eventSource;
    } catch (err) {
      console.error('Failed to create EventSource:', err);
      const errorObj = err instanceof Error ? err : new Error('Failed to create EventSource');
      setError(errorObj);
      if (onError) {
        onError(errorObj);
      }
    }
  }, [slug, enabled, onMessage, onError, queryClient]);

  const reconnect = useCallback(() => {
    // Close existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    // Clear reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Reset reconnect attempts
    reconnectAttemptsRef.current = 0;

    // Reconnect
    connect();
  }, [connect]);

  useEffect(() => {
    connect();

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };
  }, [connect]);

  return {
    isConnected,
    lastMessage,
    error,
    reconnect,
  };
}
