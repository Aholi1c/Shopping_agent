// SSE streaming helper for chat responses
// Uses fetch + ReadableStream to POST a ChatRequest and parse text/event-stream

export interface StreamChatRequest {
  message: string;
  conversation_id?: number;
  message_type?: 'text' | 'image' | 'audio' | 'video';
  media_url?: string | null;
  model?: string;
  max_tokens?: number;
  temperature?: number;
  use_memory?: boolean;
  use_rag?: boolean;
}

export interface StreamOptions {
  baseUrl?: string; // defaults to process.env.REACT_APP_API_URL || http://localhost:8000
  signal?: AbortSignal;
  onDelta: (delta: string) => void;
  onDone?: (payload?: any) => void; // receives JSON from event: done
  onError?: (err: any) => void;
  onMeta?: (meta: any) => void; // receives JSON from event: meta
}

export function createAbortController() {
  return new AbortController();
}

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export async function streamChat(
  req: StreamChatRequest,
  opts: StreamOptions
): Promise<void> {
  const base = opts.baseUrl || API_BASE_URL;
  const url = `${base}/api/chat/chat/stream`;

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: req.message,
        conversation_id: req.conversation_id,
        message_type: req.message_type || 'text',
        media_url: req.media_url ?? null,
        model: req.model || 'glm-4-0520',
        max_tokens: req.max_tokens ?? 2048,
        temperature: req.temperature ?? 0.7,
        use_memory: req.use_memory ?? true,
        use_rag: req.use_rag ?? false,
      }),
      signal: opts.signal,
    });

    if (!res.ok || !res.body) {
      const text = await res.text().catch(() => '');
      throw new Error(`SSE request failed: ${res.status} ${res.statusText} ${text}`);
    }

    // Read as SSE: data: <chunk>\n\n  and optional event: meta/error/done
    const reader = res.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      // Split into SSE events by double newline
      const parts = buffer.split(/\n\n/);
      // Keep last partial chunk in buffer
      buffer = parts.pop() || '';

      for (const part of parts) {
        // Each part may have multiple lines; look for event and data lines
        const lines = part.split(/\n/);
        let event: string | null = null;
        let data = '';
        for (const line of lines) {
          if (line.startsWith('event:')) {
            event = line.slice(6).trim();
          } else if (line.startsWith('data:')) {
            const d = line.slice(5);
            data += d.startsWith(' ') ? d.slice(1) : d; // trim one leading space if present
          }
        }

        if (event === 'error') {
          opts.onError?.(new Error(data || 'SSE stream error'));
          continue;
        }
        if (event === 'meta') {
          try {
            const meta = JSON.parse(data);
            opts.onMeta?.(meta);
          } catch {
            // ignore malformed meta
          }
          continue;
        }
        if (event === 'done' || data === '[DONE]') {
          if (event === 'done') {
            try {
              const payload = JSON.parse(data);
              opts.onDone?.(payload);
            } catch {
              opts.onDone?.();
            }
          } else {
            opts.onDone?.();
          }
          continue;
        }
        if (!event && data) {
          // default message event (delta chunk)
          opts.onDelta(data);
        }
      }
    }

    // Flush remaining buffer if contains last event
    if (buffer.trim()) {
      const lines = buffer.split(/\n/);
      let event: string | null = null;
      let data = '';
      for (const line of lines) {
        if (line.startsWith('event:')) event = line.slice(6).trim();
        if (line.startsWith('data:')) {
          const d = line.slice(5);
          data += d.startsWith(' ') ? d.slice(1) : d;
        }
      }
      if (event === 'done' || data === '[DONE]') {
        if (event === 'done') {
          try {
            const payload = JSON.parse(data);
            opts.onDone?.(payload);
          } catch {
            opts.onDone?.();
          }
        } else {
          opts.onDone?.();
        }
      } else if (event === 'meta') {
        try {
          const meta = JSON.parse(data);
          opts.onMeta?.(meta);
        } catch {}
      } else if (data) {
        opts.onDelta(data);
      }
    }

    // Ensure done callback (no payload)
    opts.onDone?.();
  } catch (err) {
    if ((err as any)?.name === 'AbortError') {
      // treat as graceful cancel
      opts.onError?.(new Error('Stream aborted'));
      return;
    }
    opts.onError?.(err);
    throw err;
  }
}
