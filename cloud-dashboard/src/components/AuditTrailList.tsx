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
    return <p data-testid="audit-trail-empty">Aucune correction pour cet employé.</p>;
  }

  return (
    <table data-testid="audit-trail-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
      <thead>
        <tr>
          <th style={{ textAlign: 'left', padding: '0.5rem' }}>Date</th>
          <th style={{ textAlign: 'left', padding: '0.5rem' }}>Action</th>
          <th style={{ textAlign: 'left', padding: '0.5rem' }}>Avant</th>
          <th style={{ textAlign: 'left', padding: '0.5rem' }}>Après</th>
          <th style={{ textAlign: 'left', padding: '0.5rem' }}>Raison</th>
        </tr>
      </thead>
      <tbody>
        {corrections.map((correction) => (
          <tr key={correction.id} data-testid={`correction-row-${correction.id}`}>
            <td style={{ padding: '0.5rem' }}>
              {correction.performed_at ? new Date(correction.performed_at).toLocaleString() : '—'}
            </td>
            <td style={{ padding: '0.5rem' }}>{ACTION_LABELS[correction.action ?? ''] ?? correction.action}</td>
            <td style={{ padding: '0.5rem' }}>{formatValue(correction.previous_value)}</td>
            <td style={{ padding: '0.5rem' }}>{formatValue(correction.new_value)}</td>
            <td style={{ padding: '0.5rem' }}>{correction.reason}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};
