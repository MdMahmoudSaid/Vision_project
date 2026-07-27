import { useState } from 'react';
import { useLocation, Navigate, useNavigate } from 'react-router-dom';
import { verifyAttendance } from '../api/attendance';
import { Button } from '../components/Button';
import { ResultBanner } from '../components/ResultBanner';
import { CameraPreview } from '../components/CameraPreview';
import { describeError } from '../api/client';
import { usePreviewGate } from '../hooks/usePreviewGate';
import { useElapsedWhile } from '../hooks/useElapsedWhile';

const initials = (name: string) =>
  name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('');

// How long the guard sees the live camera preview before verification
// proceeds automatically — enough to notice bad framing and reposition,
// short enough not to meaningfully affect the overall success budget. A
// guard who is already well positioned can also skip ahead immediately.
const PREVIEW_AUTO_ADVANCE_MS = 1800;

type AttendanceType = 'arrival' | 'departure';

const AttendancePage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [result, setResult] = useState<{ type: any; title: string; message?: string } | null>(null);

  const employeeId = location.state?.employeeId;
  const employeeName = location.state?.employeeName;

  const runVerification = async (type: AttendanceType) => {
    setResult(null);
    try {
      const res = await verifyAttendance({ employee_id: employeeId, type });
      if (res.result === 'success') {
        setResult({ type: 'success', title: 'Pointage réussi', message: res.message });
      } else if (res.result === 'failed') {
        setResult({ type: 'failure', title: 'Échec de la vérification', message: res.message });
      } else if (res.result === 'duplicate_blocked') {
        setResult({ type: 'duplicate-blocked', title: 'Pointage refusé', message: res.message });
      }
    } catch (err) {
      setResult(describeError(err, 'Erreur technique'));
    }
  };

  const gate = usePreviewGate<AttendanceType>({
    autoAdvanceMs: PREVIEW_AUTO_ADVANCE_MS,
    onRun: runVerification
  });
  const runningElapsedMs = useElapsedWhile(gate.isRunning);

  if (!employeeId) {
    return <Navigate to="/search" replace />;
  }

  const reset = () => {
    gate.reset();
    setResult(null);
    navigate('/search');
  };

  if (result) {
    return (
      <ResultBanner
        type={result.type}
        title={result.title}
        message={result.message}
        onDone={reset}
        onRetry={
          result.type === 'connection-error' ||
          result.type === 'failure' ||
          result.type === 'no-face' ||
          result.type === 'spoof'
            ? () => {
                setResult(null);
                gate.reset();
              }
            : undefined
        }
      />
    );
  }

  if (gate.isPreviewing || gate.isRunning) {
    return (
      <div style={{ textAlign: 'center' }}>
        <div className="page-eyebrow">Vérification faciale</div>
        <h1 className="page-title">Regardez la caméra</h1>

        <CameraPreview active={gate.isPreviewing} />

        <p className="page-subtitle" style={{ marginBottom: 'var(--spacing-lg)' }}>
          {gate.isPreviewing
            ? `Assurez-vous que ${employeeName} est bien visible.`
            : runningElapsedMs > 6000
              ? 'Cela prend plus de temps que prévu. Assurez-vous que la personne est bien en face de la caméra, avec un bon éclairage.'
              : runningElapsedMs > 2500
                ? 'Recherche du visage en cours...'
                : 'Vérification en cours...'}
        </p>

        {gate.isPreviewing && (
          <div className="stack" style={{ maxWidth: '320px', margin: '0 auto' }}>
            <Button onClick={gate.confirmNow}>Vérifier maintenant</Button>
            <Button variant="secondary" onClick={reset} size="medium">Annuler</Button>
          </div>
        )}
      </div>
    );
  }

  return (
    <div>
      <div className="page-eyebrow">Vérification faciale</div>
      <h1 className="page-title">Pointage pour {employeeName}</h1>

      <div className="attendance-subject">
        <div className="attendance-subject-mark" aria-hidden="true">{initials(employeeName || '?')}</div>
        <div>
          <div className="badge-chip-name">{employeeName}</div>
          <div className="badge-chip-meta">Prêt pour vérification</div>
        </div>
      </div>

      <div className="stack">
        <Button
          className="attendance-action"
          onClick={() => gate.start('arrival')}
        >
          <span className="action-icon" aria-hidden="true">↘</span>
          Arrivée
        </Button>
        <Button
          variant="secondary"
          className="attendance-action btn-outline-accent"
          onClick={() => gate.start('departure')}
        >
          <span className="action-icon" aria-hidden="true">↗</span>
          Départ
        </Button>
        <div style={{ marginTop: 'var(--spacing-lg)', textAlign: 'center' }}>
          <Button variant="secondary" onClick={reset} size="medium">Annuler</Button>
        </div>
      </div>
    </div>
  );
};

export default AttendancePage;
