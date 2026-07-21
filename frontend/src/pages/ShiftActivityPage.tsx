import { useEffect, useState } from 'react';
import { getShiftActivity, type ShiftActivityItem } from '../api/attendance';

const OUTCOME_LABELS: Record<string, string> = {
  success: 'Succès',
  failed: 'Échec',
  duplicate_blocked: 'Doublon'
};

const ShiftActivityPage = () => {
  const [activities, setActivities] = useState<ShiftActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchActivities = async () => {
      try {
        const data = await getShiftActivity();
        setActivities(data);
      } catch (err: any) {
        setError('Impossible de charger l\'activité.');
      } finally {
        setLoading(false);
      }
    };
    fetchActivities();
  }, []);

  const formatTime = (isoString: string) => {
    const d = new Date(isoString);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div>
      <div className="page-eyebrow">Journal</div>
      <h1 className="page-title">Activité récente</h1>

      {loading ? (
        <p className="badge-chip-meta">Chargement...</p>
      ) : error ? (
        <div className="login-error">{error}</div>
      ) : activities.length === 0 ? (
        <div className="empty-state">Aucune activité récente.</div>
      ) : (
        <div>
          {activities.map((act, i) => {
            const typeLabel = act.type === 'arrival' ? 'Arrivée' : act.type === 'departure' ? 'Départ' : '—';
            return (
              <div key={`${act.employee_id}-${act.timestamp}-${i}`} data-testid={`activity-${i}`} className="log-row">
                <span className="log-row-time">{formatTime(act.timestamp)}</span>
                <div className="log-row-body">
                  <div className="log-row-name">{act.employee_name}</div>
                  <div className="log-row-meta">
                    {typeLabel} · Garde : {act.guard_username}
                  </div>
                </div>
                <span className={`status-tag status-tag--${act.outcome}`}>
                  {OUTCOME_LABELS[act.outcome] ?? act.outcome}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default ShiftActivityPage;
