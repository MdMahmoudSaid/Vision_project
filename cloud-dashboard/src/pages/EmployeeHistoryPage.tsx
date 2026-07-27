import React, { useCallback, useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  createCorrection,
  getCorrectionsForEmployee,
  getEmployeeAttendanceHistory,
  type Correction,
  type EmployeeAttendanceHistory,
} from '../api/corrections';
import { describeError } from '../api/client';
import { AuditTrailList } from '../components/AuditTrailList';
import { useSession } from '../auth/SessionContext';

type CorrectionAction = 'add_arrival' | 'add_departure' | 'correct_time' | 'change_type';

export const EmployeeHistoryPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { user } = useSession();
  const canCorrect = user?.role === 'owner' || user?.role === 'admin';

  const [history, setHistory] = useState<EmployeeAttendanceHistory | null>(null);
  const [corrections, setCorrections] = useState<Correction[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [action, setAction] = useState<CorrectionAction>('add_arrival');
  const [attendanceEventId, setAttendanceEventId] = useState('');
  const [timestamp, setTimestamp] = useState('');
  const [newType, setNewType] = useState<'arrival' | 'departure'>('arrival');
  const [reason, setReason] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const [historyData, correctionsData] = await Promise.all([
        getEmployeeAttendanceHistory(id),
        getCorrectionsForEmployee(id),
      ]);
      setHistory(historyData);
      setCorrections(correctionsData);
    } catch (err) {
      setError(describeError(err, 'Erreur de chargement').message);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  const handleSubmitCorrection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    setFormError(null);
    setSubmitting(true);
    try {
      const needsEventId = action === 'correct_time' || action === 'change_type';
      const newValue = action === 'change_type' ? { type: newType } : { timestamp };

      await createCorrection({
        employee_id: id,
        attendance_event_id: needsEventId ? attendanceEventId : null,
        action,
        // The generated CorrectionCreate type widens new_value to
        // Record<string, never> because the OpenAPI schema declares it as a
        // bare `object` (deliberately: the shape depends on `action`). The
        // real backend accepts { timestamp } or { type } — cast via
        // `unknown` since neither literal type structurally overlaps with
        // the generated placeholder type.
        new_value: newValue as unknown as Record<string, never>,
        reason,
      });

      setAttendanceEventId('');
      setTimestamp('');
      setReason('');
      await load();
    } catch (err) {
      setFormError(describeError(err, 'Erreur lors de la correction').message);
    } finally {
      setSubmitting(false);
    }
  };

  if (!id) {
    return <div className="empty-state">Employé introuvable.</div>;
  }

  return (
    <div>
      <div className="page-eyebrow">Cloud</div>
      <h1 className="page-title">Historique de l'employé</h1>

      {loading && <p className="page-subtitle" data-testid="loading-indicator">Chargement...</p>}
      {error && <div className="notice notice--error" data-testid="error-message">{error}</div>}

      {history && (
        <>
          <h2 className="page-subtitle" style={{ fontSize: 'var(--text-lg)', color: 'var(--text)', marginBottom: 'var(--spacing-md)' }}>
            {history.employee_name}
          </h2>
          {history.may_be_incomplete && (
            <p className="notice notice--caution" data-testid="incomplete-warning">
              Ces données peuvent être incomplètes (synchronisation en attente).
            </p>
          )}
          <div className="table-wrap" style={{ marginBottom: 'var(--spacing-xl)' }}>
            <table className="data-table" data-testid="history-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Arrivée</th>
                  <th>Départ</th>
                  <th>Statut</th>
                  <th>Corrigé</th>
                </tr>
              </thead>
              <tbody>
                {(history.days ?? []).map((day) => (
                  <tr key={day.date} data-testid={`history-row-${day.date}`}>
                    <td>{day.date}</td>
                    <td>{day.arrival_time ? new Date(day.arrival_time).toLocaleTimeString() : '—'}</td>
                    <td>{day.departure_time ? new Date(day.departure_time).toLocaleTimeString() : '—'}</td>
                    <td>{day.completeness}</td>
                    <td>{day.corrected ? 'Oui' : 'Non'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {canCorrect && (
        <div className="card">
          <h3 style={{ marginBottom: 'var(--spacing-md)' }}>Ajouter une correction</h3>
          <form onSubmit={handleSubmitCorrection} className="stack" style={{ maxWidth: '420px' }}>
            <div className="field">
              <label htmlFor="correction-action">Action</label>
              <select
                id="correction-action"
                value={action}
                onChange={(e) => setAction(e.target.value as CorrectionAction)}
                data-testid="correction-action-select"
              >
                <option value="add_arrival">Ajouter une arrivée manquante</option>
                <option value="add_departure">Ajouter un départ manquant</option>
                <option value="correct_time">Corriger une heure</option>
                <option value="change_type">Changer le type</option>
              </select>
            </div>

            {(action === 'correct_time' || action === 'change_type') && (
              <div className="field">
                <label htmlFor="correction-event-id">ID de l'événement</label>
                <input
                  id="correction-event-id"
                  type="text"
                  value={attendanceEventId}
                  onChange={(e) => setAttendanceEventId(e.target.value)}
                  required
                  data-testid="correction-event-id-input"
                />
              </div>
            )}

            {action !== 'change_type' && (
              <div className="field">
                <label htmlFor="correction-timestamp">Horodatage</label>
                <input
                  id="correction-timestamp"
                  type="datetime-local"
                  value={timestamp}
                  onChange={(e) => setTimestamp(e.target.value)}
                  required
                  data-testid="correction-timestamp-input"
                />
              </div>
            )}

            {action === 'change_type' && (
              <div className="field">
                <label htmlFor="correction-type">Nouveau type</label>
                <select
                  id="correction-type"
                  value={newType}
                  onChange={(e) => setNewType(e.target.value as 'arrival' | 'departure')}
                  data-testid="correction-type-select"
                >
                  <option value="arrival">Arrivée</option>
                  <option value="departure">Départ</option>
                </select>
              </div>
            )}

            <div className="field">
              <label htmlFor="correction-reason">Raison (obligatoire)</label>
              <input
                id="correction-reason"
                type="text"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                required
                data-testid="correction-reason-input"
              />
            </div>

            {formError && <div className="notice notice--error" data-testid="correction-error">{formError}</div>}

            <div>
              <button type="submit" disabled={submitting} className="btn btn-primary btn-medium" data-testid="correction-submit-btn">
                {submitting ? 'Enregistrement...' : 'Enregistrer la correction'}
              </button>
            </div>
          </form>
        </div>
      )}

      <h3 style={{ marginBottom: 'var(--spacing-md)' }}>Historique des corrections</h3>
      <AuditTrailList corrections={corrections} />
    </div>
  );
};
