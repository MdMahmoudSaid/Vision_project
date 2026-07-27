import React from 'react';
import type { Report } from '../api/reports';
import { CompletenessBadge } from './CompletenessBadge';

interface ReportTableProps {
  report: Report;
  onCorrect?: (row: any) => void;
}

export const ReportTable: React.FC<ReportTableProps> = ({ report, onCorrect }) => {
  return (
    <div>
      {report.may_be_incomplete && (
        <div className="notice notice--caution" data-testid="incomplete-warning">
          <strong>Attention :</strong> la période sélectionnée contient des dates postérieures à la dernière
          synchronisation connue. Certaines données de présence peuvent être manquantes.
        </div>
      )}

      <div className="table-wrap">
        <table className="data-table" data-testid="report-table">
          <thead>
            <tr>
              <th>Employé</th>
              <th>Date</th>
              <th>Arrivée</th>
              <th>Départ</th>
              <th>Durée de travail</th>
              <th>Statut</th>
              {onCorrect && <th>Actions</th>}
            </tr>
          </thead>
          <tbody>
            {report.rows.length === 0 ? (
              <tr className="empty-row">
                <td colSpan={onCorrect ? 7 : 6}>Aucune donnée à afficher.</td>
              </tr>
            ) : (
              report.rows.map((row, idx) => (
                <tr key={`${row.employee_id}-${row.date}-${idx}`} data-testid="report-row">
                  <td>{row.employee_name}</td>
                  <td>{row.date}</td>
                  <td>{row.arrival_time ? new Date(row.arrival_time).toLocaleTimeString() : '-'}</td>
                  <td>{row.departure_time ? new Date(row.departure_time).toLocaleTimeString() : '-'}</td>
                  <td>{row.worked_duration_minutes !== null ? `${row.worked_duration_minutes} min` : '-'}</td>
                  <td>
                    <CompletenessBadge status={row.completeness} />
                    {row.corrected && (
                      <span style={{ marginLeft: '0.5rem', fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
                        (Corrigé)
                      </span>
                    )}
                  </td>
                  {onCorrect && (
                    <td>
                      <button
                        onClick={() => onCorrect(row)}
                        data-testid={`correct-btn-${row.employee_id}`}
                        className="btn btn-secondary btn-small"
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
    </div>
  );
};
