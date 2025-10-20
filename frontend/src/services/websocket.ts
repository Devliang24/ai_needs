export function createSessionSocket(sessionId: string): WebSocket {
  const base = import.meta.env.VITE_API_URL ?? window.location.origin;
  const url = new URL(`/ws/${sessionId}`, base);
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
  return new WebSocket(url.toString());
}
