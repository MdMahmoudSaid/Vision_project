import React from 'react';
import type { Report } from '../api/reports';
import { CompletenessBadge } from './CompletenessBadge';

interface ReportTableProps {
  report: Report;
  onCorrect?: (row: any) => void;
}

export const ReportTable: React.FC<ReportTableProps> = ({ report, onCorrect }) => {
  return (
    <div style={{ marginTop: '1.5rem' }}>
      {report.may_be_incomplete && (
        <div style={{
          padding: '1rem',
          backgroundColor: '#fff3cd',
          color: '#856404',
          border: '1px solid #ffeeba',
          borderRadius: '4px',
          marginBottom: '1rem'
        }} data-testid="incomplete-warning">
          <strong>Attention :</strong> La période sélectionnée contient des dates postérieures à la dernière synchronisation connue. Certaines données de présence peuvent être manquantes.
        </div>
      )}

      <table style={{ width: '100%', borderCollapse: 'collapse' }} data-testid="report-table">
        <thead>
          <tr style={{ background: '#f5f5f5' }}>
            <th style={{ padding: '0.5rem', borderBottom: '2px solid #ccc', textAlign: 'left' }}>Employé</th>
            <th style={{ padding: '0.5rem', borderBottom: '2px solid #ccc', textAlign: 'left' }}>Date</th>
            <th style={{ padding: '0.5rem', borderBottom: '2px solid #ccc', textAlign: 'left' }}>Arrivée</th>
            <th style={{ padding: '0.5rem', borderBottom: '2px solid #ccc', textAlign: 'left' }}>Départ</th>
            <th style={{ padding: '0.5rem', borderBottom: '2px solid #ccc', textAlign: 'left' }}>Durée de travail</th>
            <th style={{ padding: '0.5rem', borderBottom: '2px solid #ccc', textAlign: 'left' }}>Statut</th>
            {onCorrect && <th style={{ padding: '0.5rem', borderBottom: '2px solid #ccc', textAlign: 'left' }}>Actions</th>}
          </tr>
        </thead>
        <tbody>
          {report.rows.length === 0 ? (
            <tr>
              <td colSpan={onCorrect ? 7 : 6} style={{ textAlign: 'center', padding: '1rem' }}>
                Aucune donnée à afficher.
              </td>
            </tr>
          ) : (
            report.rows.map((row, idx) => (
              <tr key={`${row.employee_id}-${row.date}-${idx}`} data-testid="report-row">
                <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>{row.employee_name}</td>
                <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>{row.date}</td>
                <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>
                  {row.arrival_time ? new Date(row.arrival_time).toLocaleTimeString() : '-'}
                </td>
                <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>
                  {row.departure_time ? new Date(row.departure_time).toLocaleTimeString() : '-'}
                </td>
                <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>
                  {row.worked_duration_minutes !== null ? `${row.worked_duration_minutes} min` : '-'}
                </td>
                <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>
                  <CompletenessBadge status={row.completeness} />
                  {row.corrected && <span style={{ marginLeft: '0.5rem', fontSize: '0.8rem', color: '#666' }}>(Corrigé)</span>}
                </td>
                {onCorrect && (
                  <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>
                    <button 
                      onClick={() => onCorrect(row)} 
                      data-testid={`correct-btn-${row.employee_id}`}
                      style={{
                        padding: '0.2rem 0.5rem',
                        background: '#007bff',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer'
                      }}
                    >
                      Corriger
                    </button>
                  </td>
                )}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};
