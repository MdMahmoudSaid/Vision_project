import { useEffect, useState } from 'react';

/** Milliseconds elapsed since `active` last became true; resets to 0 when it
 * becomes false. Used to show progressively more reassuring status text
 * during waits whose real duration can vary (e.g. a face-detection retry
 * loop), so a slow attempt never looks like a frozen, silent UI. */
export function useElapsedWhile(active: boolean, tickMs: number = 500): number {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!active) {
      setElapsed(0);
      return;
    }
    const start = Date.now();
    setElapsed(0);
    const interval = setInterval(() => setElapsed(Date.now() - start), tickMs);
    return () => clearInterval(interval);
  }, [active, tickMs]);

  return elapsed;
}
