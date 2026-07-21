import { useLocation, useNavigate, Navigate } from 'react-router-dom';
import { enrollFace } from '../api/employees';
import { Button } from '../components/Button';
import { ResultBanner } from '../components/ResultBanner';
import { CameraPreview } from '../components/CameraPreview';
import { describeError, type ErrorDisplay } from '../api/client';
import { useSession } from '../auth/SessionContext';
import { usePreviewGate } from '../hooks/usePreviewGate';
import { useState } from 'react';

// Same pacing as the attendance preview (AttendancePage) — enough time to
// notice bad framing before the capture runs automatically.
const PREVIEW_AUTO_ADVANCE_MS = 1800;

const FaceEnrollmentPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useSession();

  const employeeId = location.state?.employeeId;
  const employeeName = location.state?.employeeName;

  const [result, setResult] = useState<
    { type: 'success'; title: string; message: string } | ErrorDisplay | null
  >(null);

  const runEnrollment = async () => {
    setResult(null);
    try {
      // The fixed camera and face detection run entirely on the local PC
      // backend; this UI only triggers the capture and shows the outcome.
      // There is no request field to force a failure — a failed enrollment
      // reflects what the real camera actually captured.
      const response = await enrollFace(employeeId, { sample_count: 3 });
      setResult({
        type: 'success',
        title: 'Enrôlement réussi',
        message: `Visage enregistré (${response.sample_count} échantillons).`
      });
    } catch (err) {
      setResult(describeError(err, 'Capture impossible'));
    }
  };

  const gate = usePreviewGate<void>({
    autoAdvanceMs: PREVIEW_AUTO_ADVANCE_MS,
    onRun: runEnrollment
  });

  if (user?.role !== 'admin') {
    return <div className="forbidden-state" data-testid="forbidden">Accès refusé</div>;
  }

  if (!employeeId) {
    return <Navigate to="/manage" replace />;
  }

  if (result) {
    return (
      <ResultBanner
        type={result.type}
        title={result.title}
        message={result.message}
        onDone={() => navigate('/search')}
        onRetry={
          result.type !== 'success'
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
        <div className="page-eyebrow">Administration</div>
        <h1 className="page-title">Enrôler {employeeName}</h1>

        <CameraPreview active={gate.isPreviewing} />

        <p className="page-subtitle" style={{ marginBottom: 'var(--spacing-lg)' }}>
          {gate.isPreviewing
            ? "Assurez-vous que le visage de l'employé est bien visible."
            : 'Capture en cours...'}
        </p>

        {gate.isPreviewing && (
          <div className="stack" style={{ maxWidth: '320px', margin: '0 auto' }}>
            <Button onClick={gate.confirmNow}>Capturer maintenant</Button>
            <Button variant="secondary" onClick={gate.reset} size="medium">Annuler</Button>
          </div>
        )}
      </div>
    );
  }

  return (
    <div>
      <div className="page-eyebrow">Administration</div>
      <h1 className="page-title">Enrôler {employeeName}</h1>

      <div className="card" style={{ textAlign: 'center' }}>
        <p className="page-subtitle" style={{ marginBottom: 'var(--spacing-lg)' }}>
          Demandez à l'employé de regarder la caméra fixe, puis lancez la capture.
        </p>
        <Button onClick={() => gate.start()}>Lancer l'enrôlement</Button>
      </div>
    </div>
  );
};

export default FaceEnrollmentPage;
