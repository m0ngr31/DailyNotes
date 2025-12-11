import eventHub from './eventHub';
import { getToken } from './user';

// Generate a unique session ID for this browser tab
const SESSION_ID = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

export interface SSEEventData {
  note_uuid?: string;
  task_uuid?: string;
  task_name?: string;
  old_task?: string;
  new_task?: string;
  column?: string;
  is_date?: boolean;
  title?: string;
  session_id?: string; // To identify which session originated the event
}

// Export session ID so components can tag their requests
export const getSessionId = () => SESSION_ID;

// Track recently updated notes to avoid duplicate processing
const recentlyUpdatedNotes = new Map<string, number>();
const DEDUP_WINDOW_MS = 2000; // Ignore SSE events for 2 seconds after local update

export const markNoteUpdatedLocally = (noteUuid: string) => {
  recentlyUpdatedNotes.set(noteUuid, Date.now());
  // Clean up old entries
  setTimeout(() => {
    recentlyUpdatedNotes.delete(noteUuid);
  }, DEDUP_WINDOW_MS);
};

export const wasRecentlyUpdatedLocally = (noteUuid: string): boolean => {
  const timestamp = recentlyUpdatedNotes.get(noteUuid);
  if (!timestamp) return false;
  return Date.now() - timestamp < DEDUP_WINDOW_MS;
};

type SSEEventHandler = (data: SSEEventData) => void;

class SSEService {
  private abortController: AbortController | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start with 1 second
  private handlers: Map<string, Set<SSEEventHandler>> = new Map();
  private isConnecting = false;

  /**
   * Connect to the SSE endpoint.
   * Will automatically reconnect on disconnection.
   */
  connect(): void {
    console.log('SSE: connect() called');
    if (this.abortController || this.isConnecting) {
      console.log('SSE: Already connected or connecting, skipping');
      return;
    }

    const token = getToken();
    if (!token) {
      console.warn('SSE: No auth token, skipping connection');
      return;
    }

    console.log('SSE: Initiating connection...');
    this.isConnecting = true;

    // For SSE, we need to bypass the webpack-dev-server proxy which buffers responses.
    // In development, connect directly to Flask on port 5001.
    // In production, use the normal API path.
    let baseUrl: string;
    if (process.env.NODE_ENV === 'development' && window.location.port === '8080') {
      // Development mode with Vue dev server - connect directly to Flask
      baseUrl = 'http://localhost:5001/api';
    } else if (process.env.VUE_APP_BASE_URL) {
      baseUrl = `${process.env.VUE_APP_BASE_URL}/api`;
    } else {
      baseUrl = '/api';
    }

    // We'll use a custom approach since EventSource doesn't support headers
    // Create an EventSource with credentials and intercept with a polyfill-like approach
    // Actually, we'll use fetch with ReadableStream instead for header support
    this.connectWithFetch(baseUrl, token);
  }

  private async connectWithFetch(baseUrl: string, token: string): Promise<void> {
    try {
      // Create abort controller for this connection
      this.abortController = new AbortController();

      console.log(`SSE: Fetching ${baseUrl}/events/stream`);
      const response = await fetch(`${baseUrl}/events/stream`, {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: 'text/event-stream',
        },
        signal: this.abortController.signal,
      });

      console.log(`SSE: Response status ${response.status}`);
      if (!response.ok) {
        throw new Error(`SSE connection failed: ${response.status}`);
      }

      if (!response.body) {
        throw new Error('SSE: No response body');
      }

      this.isConnecting = false;
      this.reconnectAttempts = 0;
      this.reconnectDelay = 1000;

      console.log('SSE: Connected');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      // Process the stream
      const processStream = async (): Promise<void> => {
        try {
          while (true) {
            const { done, value } = await reader.read();

            if (done) {
              console.log('SSE: Stream ended');
              this.handleDisconnect();
              return;
            }

            buffer += decoder.decode(value, { stream: true });

            // Process complete events in the buffer
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // Keep incomplete line in buffer

            let currentEvent = '';
            let currentData = '';

            for (const line of lines) {
              if (line.startsWith('event:')) {
                currentEvent = line.slice(6).trim();
              } else if (line.startsWith('data:')) {
                currentData = line.slice(5).trim();
              } else if (line === '' && currentData) {
                // Empty line means end of event
                this.handleEvent(currentEvent || 'message', currentData);
                currentEvent = '';
                currentData = '';
              } else if (line.startsWith(':')) {
                // Comment/heartbeat, ignore
              }
            }
          }
        } catch (error) {
          console.error('SSE: Stream error', error);
          this.handleDisconnect();
        }
      };

      processStream();
    } catch (error) {
      console.error('SSE: Connection error', error);
      this.isConnecting = false;
      this.handleDisconnect();
    }
  }

  private handleEvent(eventType: string, dataStr: string): void {
    try {
      const data = JSON.parse(dataStr) as SSEEventData;

      // Call registered handlers
      const handlers = this.handlers.get(eventType);
      if (handlers) {
        handlers.forEach((handler) => handler(data));
      }

      // Also emit to the global event hub for components that listen there
      switch (eventType) {
        case 'note_updated':
          eventHub.emit('sseNoteUpdated', data);
          break;
        case 'task_updated':
          eventHub.emit('sseTaskUpdated', data);
          break;
        case 'task_column_updated':
          eventHub.emit('sseTaskColumnUpdated', data);
          break;
        case 'connected':
          console.log('SSE: Server acknowledged connection');
          break;
      }
    } catch (error) {
      console.error('SSE: Failed to parse event data', error, dataStr);
    }
  }

  private handleDisconnect(): void {
    this.abortController = null;
    this.isConnecting = false;

    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * 2 ** (this.reconnectAttempts - 1);
      console.log(`SSE: Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

      setTimeout(() => {
        const token = getToken();
        if (token) {
          this.connect();
        }
      }, delay);
    } else {
      console.warn('SSE: Max reconnect attempts reached');
    }
  }

  /**
   * Disconnect from the SSE endpoint.
   */
  disconnect(): void {
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
    this.reconnectAttempts = this.maxReconnectAttempts; // Prevent auto-reconnect
    console.log('SSE: Disconnected');
  }

  /**
   * Register a handler for a specific event type.
   */
  on(eventType: string, handler: SSEEventHandler): void {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, new Set());
    }
    this.handlers.get(eventType)!.add(handler);
  }

  /**
   * Unregister a handler for a specific event type.
   */
  off(eventType: string, handler: SSEEventHandler): void {
    const handlers = this.handlers.get(eventType);
    if (handlers) {
      handlers.delete(handler);
    }
  }

  /**
   * Reset reconnection counter (call after successful auth).
   */
  resetReconnect(): void {
    this.reconnectAttempts = 0;
    this.reconnectDelay = 1000;
  }
}

// Export singleton instance
export const sseService = new SSEService();
