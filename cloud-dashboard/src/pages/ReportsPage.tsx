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
    <div style={{ padding: '2rem' }}>
      <h1>Générateur de Rapports de Présence</h1>

      <form onSubmit={handleGenerate} style={{
        background: '#f8f9fa',
        padding: '1.5rem',
        borderRadius: '8px',
        marginBottom: '2rem',
        border: '1px solid #dee2e6'
      }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem' }}>Type de rapport</label>
            <select 
              value={type} 
              onChange={(e) => setType(e.target.value as any)}
              style={{ width: '100%', padding: '0.5rem', borderRadius: '4px' }}
              data-testid="report-type-select"
            >
              <option value="daily">Quotidien</option>
              <option value="weekly">Hebdomadaire</option>
              <option value="monthly">Mensuel</option>
              <option value="custom">Personnalisé</option>
            </select>
          </div>

          {type === 'daily' && (
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem' }}>Date</label>
              <input 
                type="date" 
                value={date} 
                onChange={(e) => setDate(e.target.value)} 
                required 
                style={{ width: '100%', padding: '0.5rem', borderRadius: '4px' }}
                data-testid="date-input"
              />
            </div>
          )}

          {type === 'weekly' && (
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem' }}>Date de début de semaine</label>
              <input 
                type="date" 
                value={weekStart} 
                onChange={(e) => setWeekStart(e.target.value)} 
                required 
                style={{ width: '100%', padding: '0.5rem', borderRadius: '4px' }}
                data-testid="week-start-input"
              />
            </div>
          )}

          {type === 'monthly' && (
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem' }}>Mois (AAAA-MM)</label>
              <input 
                type="month" 
                value={month} 
                onChange={(e) => setMonth(e.target.value)} 
                required 
                style={{ width: '100%', padding: '0.5rem', borderRadius: '4px' }}
                data-testid="month-input"
              />
            </div>
          )}

          {type === 'custom' && (
            <>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem' }}>Du</label>
                <input 
                  type="date" 
                  value={dateFrom} 
                  onChange={(e) => setDateFrom(e.target.value)} 
                  required 
                  style={{ width: '100%', padding: '0.5rem', borderRadius: '4px' }}
                  data-testid="date-from-input"
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem' }}>Au</label>
                <input 
                  type="date" 
                  value={dateTo} 
                  onChange={(e) => setDateTo(e.target.value)} 
                  required 
                  style={{ width: '100%', padding: '0.5rem', borderRadius: '4px' }}
                  data-testid="date-to-input"
                />
              </div>
              <div style={{ gridColumn: 'span 2' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem' }}>ID Employé (optionnel)</label>
                <input 
                  type="text" 
                  value={employeeId} 
                  onChange={(e) => setEmployeeId(e.target.value)} 
                  placeholder="Laisser vide pour toute l'organisation"
                  style={{ width: '100%', padding: '0.5rem', borderRadius: '4px' }}
                  data-testid="employee-id-input"
                />
              </div>
            </>
          )}
        </div>

        <button 
          type="submit" 
          disabled={loading}
          style={{
            padding: '0.5rem 1rem',
            background: '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
          data-testid="generate-btn"
        >
          {loading ? 'Génération...' : 'Afficher le rapport'}
        </button>
      </form>

      {error && <div style={{ color: 'red', marginBottom: '1rem' }} data-testid="error-message">{error}</div>}

      {report && (
        <div>
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
            <button 
              onClick={() => handleExport('pdf')} 
              data-testid="export-pdf-btn"
              style={{ padding: '0.5rem 1rem', background: '#dc3545', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
            >
              Exporter en PDF
            </button>
            <button 
              onClick={() => handleExport('xlsx')} 
              data-testid="export-excel-btn"
              style={{ padding: '0.5rem 1rem', background: '#17a2b8', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
            >
              Exporter en Excel
            </button>
            <button 
              onClick={handlePrint} 
              data-testid="print-btn"
              style={{ padding: '0.5rem 1rem', background: '#6c757d', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
            >
              Imprimer
            </button>
          </div>

          <ReportTable 
            report={report} 
            onCorrect={canCorrect ? handleCorrect : undefined} 
          />
        </div>
      )}
    </div>
  );
};
