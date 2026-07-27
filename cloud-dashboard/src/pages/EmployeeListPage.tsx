import React, { useEffect, useState, useCallback } from 'react';
import { getEmployees, type SyncedEmployee, type GetEmployeesParams } from '../api/employees';
import { describeError } from '../api/client';
import { Link } from 'react-router-dom';

export const EmployeeListPage: React.FC = () => {
  const [employees, setEmployees] = useState<SyncedEmployee[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [search, setSearch] = useState('');
  const [department, setDepartment] = useState('');
  const [activeOnly, setActiveOnly] = useState(true);

  const loadEmployees = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: GetEmployeesParams = {};
      if (activeOnly) params.active = true;
      if (search.trim()) params.query = search.trim();
      if (department.trim()) params.department = department.trim();

      const data = await getEmployees(params);
      setEmployees(data);
    } catch (err: any) {
      setError(describeError(err, 'Erreur de chargement').message);
    } finally {
      setLoading(false);
    }
  }, [search, department, activeOnly]);

  useEffect(() => {
    // Simple debounce would be better here, but for now we'll just trigger load when filters change.
    const timer = setTimeout(() => {
      loadEmployees();
    }, 300);
    return () => clearTimeout(timer);
  }, [loadEmployees]);

  return (
    <div>
      <div className="page-eyebrow">Cloud</div>
      <h1 className="page-title">Employés synchronisés</h1>

      <div className="card">
        <div className="filter-row">
          <div className="field">
            <label htmlFor="search">Recherche</label>
            <input
              id="search"
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Nom ou matricule"
              data-testid="search-input"
            />
          </div>
          <div className="field">
            <label htmlFor="department">Département</label>
            <input
              id="department"
              type="text"
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              placeholder="Département"
              data-testid="department-input"
            />
          </div>
          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={activeOnly}
              onChange={(e) => setActiveOnly(e.target.checked)}
              data-testid="active-checkbox"
            />
            Actifs uniquement
          </label>
        </div>
      </div>

      {error && <div className="notice notice--error" data-testid="error-message">{error}</div>}

      {loading ? (
        <p className="page-subtitle" data-testid="loading-indicator">Chargement...</p>
      ) : (
        <div className="table-wrap">
          <table className="data-table" data-testid="employee-table">
            <thead>
              <tr>
                <th>Matricule</th>
                <th>Nom complet</th>
                <th>Département</th>
                <th>Statut</th>
                <th>Visage enrôlé</th>
                <th>Dernière synchro</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {employees.length === 0 ? (
                <tr className="empty-row">
                  <td colSpan={7}>Aucun employé trouvé.</td>
                </tr>
              ) : (
                employees.map(emp => (
                  <tr key={emp.id} data-testid={`employee-row-${emp.id}`}>
                    <td>{emp.employee_number}</td>
                    <td>{emp.full_name}</td>
                    <td>{emp.department || '-'}</td>
                    <td>
                      <span className={`status-tag status-tag--${emp.active ? 'go' : 'neutral'}`}>
                        {emp.active ? 'Actif' : 'Inactif'}
                      </span>
                    </td>
                    <td>{emp.has_face_reference ? 'Oui' : 'Non'}</td>
                    <td>{new Date(emp.synced_at).toLocaleString()}</td>
                    <td>
                      <Link to={`/employees/${emp.id}/history`}>Historique</Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
