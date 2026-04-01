"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { parseSSEBuffer } from "@/lib/sse";

interface UseSSEOptions<TEvent = unknown> {
  url: string;
  method?: "POST" | "GET";
  body?: string;
  onEvent: (event: string, data: TEvent) => void;
  onError?: (error: Error) => void;
  onDone?: () => void;
}

interface UseSSEReturn {
  start: () => void;
  abort: () => void;
  isStreaming: boolean;
}

export function useSSE<TEvent = unknown>(
  options: UseSSEOptions<TEvent>,
): UseSSEReturn {
  const [isStreaming, setIsStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const optionsRef = useRef(options);
  optionsRef.current = options;

  const abort = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setIsStreaming(false);
  }, []);

  const start = useCallback(async () => {
    // Abort any existing stream
    abortRef.current?.abort();

    const controller = new AbortController();
    abortRef.current = controller;
    setIsStreaming(true);

    const { url, method = "POST", body, onEvent, onError, onDone } =
      optionsRef.current;

    try {
      const res = await fetch(url, {
        method,
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
        body,
        signal: controller.signal,
      });

      if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(text || `HTTP ${res.status}`);
      }

      const reader = res.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const { events, remaining } = parseSSEBuffer(buffer);
        buffer = remaining;

        for (const evt of events) {
          try {
            const parsed = JSON.parse(evt.data) as TEvent;
            onEvent(evt.event, parsed);
          } catch {
            // If data isn't JSON, pass raw string
            onEvent(evt.event, evt.data as TEvent);
          }
        }
      }

      onDone?.();
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        // User aborted — not an error
      } else {
        onError?.(err instanceof Error ? err : new Error(String(err)));
      }
    } finally {
      if (abortRef.current === controller) {
        abortRef.current = null;
      }
      setIsStreaming(false);
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  return { start, abort, isStreaming };
}
