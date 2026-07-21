import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  createEmployee,
  deactivateEmployee,
  deleteEmployee,
  searchEmployees,
  type EmployeeSummary
} from '../api/employees';
import { Button } from '../components/Button';
import { ApiError, describeError } from '../api/client';
import { useSession } from '../auth/SessionContext';

const EmployeeManagementPage = () => {
  const navigate = useNavigate();
  const { user } = useSession();

  const [fullName, setFullName] = useState('');
  const [employeeNumber, setEmployeeNumber] = useState('');
  const [department, setDepartment] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [employees, setEmployees] = useState<EmployeeSummary[]>([]);
  const [showInactive, setShowInactive] = useState(false);
  const [listLoading, setListLoading] = useState(false);
  const [confirmingId, setConfirmingId] = useState<string | null>(null);
  const [rowBusyId, setRowBusyId] = useState<string | null>(null);
  const [rowError, setRowError] = useState<{ id: string; message: string; hasHistory: boolean } | null>(null);

  const loadEmployees = async () => {
    setListLoading(true);
    try {
      const results = await searchEmployees('', !showInactive);
      setEmployees(results);
    } catch {
      setEmployees([]);
    } finally {
      setListLoading(false);
    }
  };

  useEffect(() => {
    loadEmployees();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showInactive]);

  if (user?.role !== 'admin') {
    return <div className="forbidden-state" data-testid="forbidden">Accès refusé</div>;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await createEmployee({
        full_name: fullName,
        employee_number: employeeNumber,
        department: department || undefined
      });
      navigate('/enroll', { state: { employeeId: res.id, employeeName: res.full_name } });
    } catch (err: any) {
      setError(describeError(err, 'Une erreur est survenue.').message);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    setRowBusyId(id);
    setRowError(null);
    try {
      await deleteEmployee(id);
      setConfirmingId(null);
      setEmployees(prev => prev.filter(emp => emp.id !== id));
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setRowError({ id, message: err.message, hasHistory: true });
      } else {
        setRowError({ id, message: describeError(err, 'Suppression impossible').message, hasHistory: false });
      }
    } finally {
      setRowBusyId(null);
    }
  };

  const handleDeactivate = async (id: string) => {
    setRowBusyId(id);
    try {
      const updated = await deactivateEmployee(id);
      setConfirmingId(null);
      setRowError(null);
      setEmployees(prev =>
        showInactive
          ? prev.map(emp => (emp.id === id ? { ...emp, ...updated } : emp))
          : prev.filter(emp => emp.id !== id)
      );
    } catch (err) {
      setRowError({ id, message: describeError(err, 'Échec de la désactivation').message, hasHistory: false });
    } finally {
      setRowBusyId(null);
    }
  };

  return (
    <div>
      <div className="page-eyebrow">Administration</div>
      <h1 className="page-title">Créer un employé</h1>

      <div className="card">
        {error && <div className="login-error" style={{ marginBottom: 'var(--spacing-md)' }}>{error}</div>}
        <form onSubmit={handleSubmit} className="stack">
          <div className="field">
            <label htmlFor="fullName">Nom complet</label>
            <input
              id="fullName"
              required
              type="text"
              value={fullName}
              onChange={e => setFullName(e.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="employeeNumber">Matricule</label>
            <input
              id="employeeNumber"
              required
              type="text"
              value={employeeNumber}
              onChange={e => setEmployeeNumber(e.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="department">Département (optionnel)</label>
            <input
              id="department"
              type="text"
              value={department}
              onChange={e => setDepartment(e.target.value)}
            />
          </div>
          <Button type="submit" disabled={loading}>
            {loading ? 'Création...' : 'Créer et passer à l\'enrôlement'}
          </Button>
        </form>
      </div>

      <h2 className="page-title" style={{ fontSize: 'var(--text-lg)', marginTop: 'var(--spacing-xl)' }}>
        Employés
      </h2>

      <label className="toggle-row">
        <input
          type="checkbox"
          checked={showInactive}
          onChange={e => setShowInactive(e.target.checked)}
        />
        Afficher les employés inactifs
      </label>

      {listLoading && <p className="page-subtitle">Chargement...</p>}

      {!listLoading && employees.length === 0 && (
        <p className="page-subtitle">Aucun employé à afficher.</p>
      )}

      {employees.map(emp => (
        <div key={emp.id} className={`admin-row ${emp.active === false ? 'is-inactive' : ''}`}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="badge-chip-name">{emp.full_name}</div>
            <div className="badge-chip-meta">
              {emp.employee_number}
              {emp.department ? ` · ${emp.department}` : ''}
              {emp.active === false ? ' · Inactif' : ''}
            </div>
          </div>

          <div className="admin-row-actions">
            {confirmingId === emp.id ? (
              <>
                <button
                  type="button"
                  className="row-btn row-btn-danger"
                  onClick={() => handleDelete(emp.id)}
                  disabled={rowBusyId === emp.id}
                >
                  {rowBusyId === emp.id ? 'Suppression...' : 'Confirmer'}
                </button>
                <button
                  type="button"
                  className="row-btn"
                  onClick={() => setConfirmingId(null)}
                  disabled={rowBusyId === emp.id}
                >
                  Annuler
                </button>
              </>
            ) : (
              <button
                type="button"
                className="row-btn row-btn-danger"
                onClick={() => {
                  setConfirmingId(emp.id);
                  setRowError(null);
                }}
              >
                Supprimer
              </button>
            )}
          </div>

          {rowError?.id === emp.id && (
            <div className="login-error admin-row-error">
              {rowError.message}
              {rowError.hasHistory && (
                <>
                  {' '}
                  <button
                    type="button"
                    className="row-btn"
                    style={{ marginLeft: 'var(--spacing-sm)' }}
                    onClick={() => handleDeactivate(emp.id)}
                    disabled={rowBusyId === emp.id}
                  >
                    Désactiver à la place
                  </button>
                </>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default EmployeeManagementPage;
