import type { FC } from 'react';

type ResultType = 'success' | 'failure' | 'duplicate-blocked' | 'connection-error' | 'loading';

interface ResultBannerProps {
  type: ResultType;
  title: string;
  message?: string;
  onRetry?: () => void;
  onDone?: () => void;
}

const ICONS: Record<ResultType, string> = {
  success: '✓',
  failure: '✕',
  'duplicate-blocked': '⚠',
  'connection-error': '⌁',
  loading: '…'
};

export const ResultBanner: FC<ResultBannerProps> = ({ type, title, message, onRetry, onDone }) => {
  return (
    <div className={`gate-result gate-result--${type}`} role="status">
      <div className="gate-result-icon" aria-hidden="true">{ICONS[type]}</div>
      <h2 className="gate-result-title">{title}</h2>
      {message && <p className="gate-result-message">{message}</p>}
      <div className="gate-result-actions">
        {onRetry && (
          <button onClick={onRetry} className="btn btn-secondary btn-medium">
            Réessayer
          </button>
        )}
        {onDone && (
          <button onClick={onDone} className="btn btn-primary btn-medium">
            Terminé
          </button>
        )}
      </div>
    </div>
  );
};
