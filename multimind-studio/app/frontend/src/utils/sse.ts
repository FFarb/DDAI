export async function streamSSE(
  url: string,
  options: RequestInit,
  onMessage: (data: string) => void,
  onDone?: () => void,
  onError?: (error: unknown) => void
): Promise<void> {
  try {
    const response = await fetch(url, options);
    if (!response.ok || !response.body) {
      throw new Error(`SSE request failed with status ${response.status}`);
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split('\n\n');
      buffer = parts.pop() || '';
      for (const part of parts) {
        if (!part.trim()) continue;
        const line = part.trim();
        if (!line.startsWith('data:')) continue;
        const data = line.replace(/^data:/, '').trim();
        if (data === '[DONE]') {
          onDone?.();
          return;
        }
        onMessage(data);
      }
    }
    if (buffer.trim()) {
      const line = buffer.trim();
      if (line.startsWith('data:')) {
        const data = line.replace(/^data:/, '').trim();
        if (data !== '[DONE]') {
          onMessage(data);
        }
      }
    }
    onDone?.();
  } catch (error) {
    onError?.(error);
    onDone?.();
  }
}
