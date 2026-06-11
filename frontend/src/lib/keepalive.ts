const PING_INTERVAL_MS = 14 * 60 * 1000;

export const startKeepalive = (): (() => void) => {
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const ping = async () => {
    try {
      await fetch(`${apiUrl}/api/v1/health`);
    } catch (err) {
      console.warn("Keepalive ping failed:", err);
    }
  };

  ping();
  const intervalId = setInterval(ping, PING_INTERVAL_MS);
  
  return () => {
    clearInterval(intervalId);
  };
};
