/**
 * Render free-tier keepalive — pings the backend health endpoint every
 * 14 minutes to prevent the service from spinning down due to inactivity.
 *
 * Usage: call startKeepalive() in App.tsx useEffect and call the returned
 * cleanup function on unmount.
 */
const PING_INTERVAL_MS = 14 * 60 * 1000;

/**
 * Start the keepalive ping interval.
 *
 * Sends an immediate ping on call, then repeats every 14 minutes.
 * @returns Cleanup function that clears the interval (for useEffect return)
 */
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
