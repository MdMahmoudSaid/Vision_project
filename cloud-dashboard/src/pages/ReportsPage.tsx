import React, { useState } from 'react';
import { fetchReport, downloadReport, type Report, type ReportParams } from '../api/reports';
import { ReportTable } from '../components/ReportTable';
import { useSession } from '../auth/SessionContext';
import { describeError } from '../api/client';

export const ReportsPage: React.FC = () => {
  const { user } = useSession();

  const [type, setType] = useState<'daily' | 'weekly' | 'monthly' | 'custom'>('daily');
  const [date, setDate] = useState('');
  const [weekStart, setWeekStart] = useState('');
  const [month, setMonth] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [employeeId, setEmployeeId] = useState('');

  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getParams = (): ReportParams => {
    const params: ReportParams = { type };
    if (type === 'daily') params.date = date;
    if (type === 'weekly') params.week_start = weekStart;
    if (type === 'monthly') params.month = month;
    if (type === 'custom') {
      params.date_from = dateFrom;
      params.date_to = dateTo;
      if (employeeId.trim()) params.employee_id = employeeId.trim();
    }
    return params;
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setReport(null);
    try {
      const data = await fetchReport(getParams());
      setReport(data);
    } catch (err: any) {
      setError(describeError(err, 'Erreur de génération du rapport').message);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format: 'pdf' | 'xlsx') => {
    try {
      const blob = await downloadReport({ ...getParams(), format });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `report_${type}.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(describeError(err, `Erreur d'exportation ${format.toUpperCase()}`).message);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const canCorrect = user?.role === 'owner' || user?.role === 'admin';
  const handleCorrect = (row: any) => {
    // US3 will trigger the correction flow modal.
    console.log('Correction requested for row:', row);
  };

  return (
    <div>
      <div className="page-eyebrow">Cloud</div>
      <h1 className="page-title">Générateur de rapports de présence</h1>

      <form onSubmit={handleGenerate} className="card stack">
        <div className="filter-row">
          <div className="field">
            <label htmlFor="report-type">Type de rapport</label>
            <select
              id="report-type"
              value={type}
              onChange={(e) => setType(e.target.value as any)}
              data-testid="report-type-select"
            >
              <option value="daily">Quotidien</option>
              <option value="weekly">Hebdomadaire</option>
              <option value="monthly">Mensuel</option>
              <option value="custom">Personnalisé</option>
            </select>
          </div>

          {type === 'daily' && (
            <div className="field">
              <label htmlFor="date">Date</label>
              <input
                id="date"
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                required
                data-testid="date-input"
              />
            </div>
          )}

          {type === 'weekly' && (
            <div className="field">
              <label htmlFor="week-start">Date de début de semaine</label>
              <input
                id="week-start"
                type="date"
                value={weekStart}
                onChange={(e) => setWeekStart(e.target.value)}
                required
                data-testid="week-start-input"
              />
            </div>
          )}

          {type === 'monthly' && (
            <div className="field">
              <label htmlFor="month">Mois (AAAA-MM)</label>
              <input
                id="month"
                type="month"
                value={month}
                onChange={(e) => setMonth(e.target.value)}
                required
                data-testid="month-input"
              />
            </div>
          )}

          {type === 'custom' && (
            <>
              <div className="field">
                <label htmlFor="date-from">Du</label>
                <input
                  id="date-from"
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                  required
                  data-testid="date-from-input"
                />
              </div>
              <div className="field">
                <label htmlFor="date-to">Au</label>
                <input
                  id="date-to"
                  type="date"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                  required
                  data-testid="date-to-input"
                />
              </div>
              <div className="field">
                <label htmlFor="employee-id">ID employé (optionnel)</label>
                <input
                  id="employee-id"
                  type="text"
                  value={employeeId}
                  onChange={(e) => setEmployeeId(e.target.value)}
                  placeholder="Laisser vide pour toute l'organisation"
                  data-testid="employee-id-input"
                />
              </div>
            </>
          )}
        </div>

        <div>
          <button type="submit" disabled={loading} className="btn btn-primary btn-medium" data-testid="generate-btn">
            {loading ? 'Génération...' : 'Afficher le rapport'}
          </button>
        </div>
      </form>

      {error && <div className="notice notice--error" data-testid="error-message">{error}</div>}

      {report && (
        <div>
          <div className="data-table-actions" style={{ marginBottom: 'var(--spacing-lg)' }}>
            <button onClick={() => handleExport('pdf')} data-testid="export-pdf-btn" className="btn btn-secondary btn-medium">
              Exporter en PDF
            </button>
            <button onClick={() => handleExport('xlsx')} data-testid="export-excel-btn" className="btn btn-secondary btn-medium">
              Exporter en Excel
            </button>
            <button onClick={handlePrint} data-testid="print-btn" className="btn btn-secondary btn-medium">
              Imprimer
            </button>
          </div>

          <ReportTable report={report} onCorrect={canCorrect ? handleCorrect : undefined} />
        </div>
      )}
    </div>
  );
};
