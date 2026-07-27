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
    return <div>Employé introuvable.</div>;
  }

  return (
    <div style={{ padding: '2rem' }}>
      <h1>Historique de l'employé</h1>

      {loading && <p data-testid="loading-indicator">Chargement...</p>}
      {error && <div style={{ color: 'red' }} data-testid="error-message">{error}</div>}

      {history && (
        <>
          <h2>{history.employee_name}</h2>
          {history.may_be_incomplete && (
            <p data-testid="incomplete-warning" style={{ color: '#b45309' }}>
              Ces données peuvent être incomplètes (synchronisation en attente).
            </p>
          )}
          <table data-testid="history-table" style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '2rem' }}>
            <thead>
              <tr>
                <th style={{ textAlign: 'left', padding: '0.5rem' }}>Date</th>
                <th style={{ textAlign: 'left', padding: '0.5rem' }}>Arrivée</th>
                <th style={{ textAlign: 'left', padding: '0.5rem' }}>Départ</th>
                <th style={{ textAlign: 'left', padding: '0.5rem' }}>Statut</th>
                <th style={{ textAlign: 'left', padding: '0.5rem' }}>Corrigé</th>
              </tr>
            </thead>
            <tbody>
              {(history.days ?? []).map((day) => (
                <tr key={day.date} data-testid={`history-row-${day.date}`}>
                  <td style={{ padding: '0.5rem' }}>{day.date}</td>
                  <td style={{ padding: '0.5rem' }}>
                    {day.arrival_time ? new Date(day.arrival_time).toLocaleTimeString() : '—'}
                  </td>
                  <td style={{ padding: '0.5rem' }}>
                    {day.departure_time ? new Date(day.departure_time).toLocaleTimeString() : '—'}
                  </td>
                  <td style={{ padding: '0.5rem' }}>{day.completeness}</td>
                  <td style={{ padding: '0.5rem' }}>{day.corrected ? 'Oui' : 'Non'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {canCorrect && (
        <div style={{ background: '#f8f9fa', padding: '1.5rem', borderRadius: '8px', marginBottom: '2rem' }}>
          <h3>Ajouter une correction</h3>
          <form onSubmit={handleSubmitCorrection} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxWidth: '400px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '0.25rem' }}>Action</label>
              <select
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
              <div>
                <label style={{ display: 'block', marginBottom: '0.25rem' }}>ID de l'événement</label>
                <input
                  type="text"
                  value={attendanceEventId}
                  onChange={(e) => setAttendanceEventId(e.target.value)}
                  required
                  data-testid="correction-event-id-input"
                />
              </div>
            )}

            {action !== 'change_type' && (
              <div>
                <label style={{ display: 'block', marginBottom: '0.25rem' }}>Horodatage</label>
                <input
                  type="datetime-local"
                  value={timestamp}
                  onChange={(e) => setTimestamp(e.target.value)}
                  required
                  data-testid="correction-timestamp-input"
                />
              </div>
            )}

            {action === 'change_type' && (
              <div>
                <label style={{ display: 'block', marginBottom: '0.25rem' }}>Nouveau type</label>
                <select
                  value={newType}
                  onChange={(e) => setNewType(e.target.value as 'arrival' | 'departure')}
                  data-testid="correction-type-select"
                >
                  <option value="arrival">Arrivée</option>
                  <option value="departure">Départ</option>
                </select>
              </div>
            )}

            <div>
              <label style={{ display: 'block', marginBottom: '0.25rem' }}>Raison (obligatoire)</label>
              <input
                type="text"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                required
                data-testid="correction-reason-input"
              />
            </div>

            {formError && <div style={{ color: 'red' }} data-testid="correction-error">{formError}</div>}

            <button type="submit" disabled={submitting} data-testid="correction-submit-btn">
              {submitting ? 'Enregistrement...' : 'Enregistrer la correction'}
            </button>
          </form>
        </div>
      )}

      <h3>Historique des corrections</h3>
      <AuditTrailList corrections={corrections} />
    </div>
  );
};
