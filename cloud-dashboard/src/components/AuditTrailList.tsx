import React from 'react';
import type { Correction } from '../api/corrections';

const ACTION_LABELS: Record<string, string> = {
  add_arrival: 'Arrivée ajoutée',
  add_departure: 'Départ ajouté',
  correct_time: 'Heure corrigée',
  change_type: 'Type modifié',
};

function formatValue(value: unknown): string {
  if (!value || typeof value !== 'object') return '—';
  const entries = Object.entries(value as Record<string, unknown>);
  return entries.map(([key, val]) => `${key}: ${String(val)}`).join(', ');
}

export const AuditTrailList: React.FC<{ corrections: Correction[] }> = ({ corrections }) => {
  if (corrections.length === 0) {
    return (
      <p className="page-subtitle" data-testid="audit-trail-empty">
        Aucune correction pour cet employé.
      </p>
    );
  }

  return (
    <div className="table-wrap">
      <table className="data-table" data-testid="audit-trail-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Action</th>
            <th>Avant</th>
            <th>Après</th>
            <th>Raison</th>
          </tr>
        </thead>
        <tbody>
          {corrections.map((correction) => (
            <tr key={correction.id} data-testid={`correction-row-${correction.id}`}>
              <td>{correction.performed_at ? new Date(correction.performed_at).toLocaleString() : '—'}</td>
              <td>{ACTION_LABELS[correction.action ?? ''] ?? correction.action}</td>
              <td>{formatValue(correction.previous_value)}</td>
              <td>{formatValue(correction.new_value)}</td>
              <td>{correction.reason}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
