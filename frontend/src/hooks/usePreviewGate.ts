import { useEffect, useRef, useState } from 'react';

export type PreviewGatePhase = 'idle' | 'preview' | 'running';

interface UsePreviewGateOptions<T> {
  /** How long the live camera preview shows before the action runs
   * automatically. A guard who is already well positioned can also confirm
   * immediately instead of waiting. */
  autoAdvanceMs: number;
  onRun: (payload: T) => void | Promise<void>;
}

/** Shared state machine behind every "show the camera circle, then act"
 * flow (attendance verification, face enrollment): idle -> preview (camera
 * visible, auto-advance timer running) -> running (real capture in
 * progress). The camera can only be held open by one caller at a time, so
 * the preview must always stop before the real action starts — this hook
 * is the single place that enforces that ordering. */
export function usePreviewGate<T = void>({ autoAdvanceMs, onRun }: UsePreviewGateOptions<T>) {
  const [phase, setPhase] = useState<PreviewGatePhase>('idle');
  const [pending, setPending] = useState<T | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearTimer = () => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  };

  useEffect(() => clearTimer, []);

  const run = (payload: T) => {
    clearTimer();
    setPhase('running');
    onRun(payload);
  };

  const start = (payload: T) => {
    setPending(payload);
    setPhase('preview');
    clearTimer();
    timerRef.current = setTimeout(() => run(payload), autoAdvanceMs);
  };

  const confirmNow = () => {
    if (pending === null) return;
    run(pending);
  };

  const reset = () => {
    clearTimer();
    setPhase('idle');
    setPending(null);
  };

  return {
    phase,
    pending,
    start,
    confirmNow,
    reset,
    isIdle: phase === 'idle',
    isPreviewing: phase === 'preview',
    isRunning: phase === 'running'
  };
}
