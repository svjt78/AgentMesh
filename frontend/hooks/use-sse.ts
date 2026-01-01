/**
 * useSSE Hook - Server-Sent Events subscription
 */

import { useEffect, useState, useCallback, useRef } from 'react';

export interface SSEEvent {
  id?: string;
  event?: string;
  data: any;
  timestamp: string;
}

export interface UseSSEOptions {
  onEvent?: (event: SSEEvent) => void;
  onError?: (error: Event) => void;
  onComplete?: () => void;
  reconnect?: boolean;
}

export function useSSE(url: string | null, options: UseSSEOptions = {}) {
  const [events, setEvents] = useState<SSEEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const lastEventIdRef = useRef<string | null>(null);

  // Use ref for options to avoid recreating connect callback
  const optionsRef = useRef(options);
  optionsRef.current = options;

  const connect = useCallback(() => {
    if (!url) return;

    // Build URL with last event ID for reconnection
    let streamUrl = url;
    if (optionsRef.current.reconnect && lastEventIdRef.current) {
      streamUrl += `?last_event_id=${lastEventIdRef.current}`;
    }

    const eventSource = new EventSource(streamUrl);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      console.log('SSE connection opened');
      setIsConnected(true);
      setError(null);
    };

    eventSource.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        const event: SSEEvent = {
          id: e.lastEventId,
          data,
          timestamp: new Date().toISOString(),
        };

        // Store last event ID
        if (e.lastEventId) {
          lastEventIdRef.current = e.lastEventId;
        }

        setEvents((prev) => [...prev, event]);
        optionsRef.current.onEvent?.(event);
      } catch (err) {
        console.error('Failed to parse SSE event:', err);
      }
    };

    // Handle custom event types
    eventSource.addEventListener('workflow_completed', (e: MessageEvent) => {
      console.log('Workflow completed');
      optionsRef.current.onComplete?.();
      eventSource.close();
      setIsConnected(false);
    });

    eventSource.addEventListener('workflow_error', (e: MessageEvent) => {
      console.error('Workflow error:', e.data);
      optionsRef.current.onComplete?.();
      eventSource.close();
      setIsConnected(false);
    });

    eventSource.onerror = (e) => {
      console.error('SSE error:', e);
      setError('Connection error');
      setIsConnected(false);
      optionsRef.current.onError?.(e);

      // Reconnect if enabled
      if (optionsRef.current.reconnect) {
        setTimeout(() => {
          console.log('Reconnecting...');
          connect();
        }, 3000);
      }
    };
  }, [url]); // Only depend on url, not options

  useEffect(() => {
    if (!url) return;

    // Clear events when URL changes (new session)
    setEvents([]);

    // Close existing connection if any
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    connect();

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, [url, connect]); // url and connect (which only changes when url changes)

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setIsConnected(false);
    }
  }, []);

  return {
    events,
    isConnected,
    error,
    disconnect,
  };
}
