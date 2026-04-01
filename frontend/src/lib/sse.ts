export interface SSEEvent {
  event: string;
  data: string;
}

/**
 * Parse an SSE text buffer into discrete events.
 * Returns parsed events and the remaining (incomplete) buffer.
 */
export function parseSSEBuffer(buffer: string): {
  events: SSEEvent[];
  remaining: string;
} {
  const events: SSEEvent[] = [];

  // SSE events are separated by double newlines
  const parts = buffer.split("\n\n");
  // Last part may be incomplete — keep as remaining
  const remaining = parts.pop() ?? "";

  for (const part of parts) {
    const trimmed = part.trim();
    if (!trimmed) continue;

    let event = "message";
    const dataLines: string[] = [];

    for (const line of trimmed.split("\n")) {
      if (line.startsWith("event:")) {
        event = line.slice(6).trim();
      } else if (line.startsWith("data:")) {
        dataLines.push(line.slice(5).trimStart());
      } else if (line.startsWith(":")) {
        // comment — ignore
      }
    }

    if (dataLines.length > 0) {
      events.push({ event, data: dataLines.join("\n") });
    }
  }

  return { events, remaining };
}
