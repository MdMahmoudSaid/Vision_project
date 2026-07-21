import { useEffect, useRef, useState } from 'react';
import { getCameraPreview } from '../api/attendance';

const POLL_INTERVAL_MS = 800;

interface CameraPreviewProps {
  /** Polling stops when false. Set this to false right before triggering the
   * real verification call — the camera can only be held open by one caller
   * at a time, so the preview and the actual capture must never overlap. */
  active: boolean;
}

export const CameraPreview = ({ active }: CameraPreviewProps) => {
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [unavailable, setUnavailable] = useState(false);
  const currentUrlRef = useRef<string | null>(null);

  useEffect(() => {
    if (!active) {
      return;
    }

    let cancelled = false;

    const poll = async () => {
      try {
        const blob = await getCameraPreview();
        if (cancelled) return;
        const nextUrl = URL.createObjectURL(blob);
        if (currentUrlRef.current) {
          URL.revokeObjectURL(currentUrlRef.current);
        }
        currentUrlRef.current = nextUrl;
        setImageUrl(nextUrl);
        setUnavailable(false);
      } catch {
        // The preview is a UX nicety, not a hard requirement — if the camera
        // is briefly unavailable, show a neutral placeholder and keep
        // trying, rather than blocking the guard from verifying.
        if (!cancelled) setUnavailable(true);
      }
    };

    poll();
    const interval = setInterval(poll, POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [active]);

  useEffect(() => {
    return () => {
      if (currentUrlRef.current) {
        URL.revokeObjectURL(currentUrlRef.current);
      }
    };
  }, []);

  return (
    <div className="camera-preview" role="img" aria-label="Aperçu de la caméra">
      <div className="camera-preview-ring" aria-hidden="true" />
      {active && <div className="camera-preview-scanner" aria-hidden="true" />}
      {imageUrl ? (
        <img src={imageUrl} alt="" className="camera-preview-image" />
      ) : (
        <div className="camera-preview-placeholder" aria-hidden="true">
          {unavailable ? '⌁' : '◎'}
        </div>
      )}
    </div>
  );
};
