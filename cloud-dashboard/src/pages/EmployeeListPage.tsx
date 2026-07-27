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
    <div style={{ padding: '2rem' }}>
      <h1>Liste des Employés Synchronisés</h1>
      
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem', padding: '1rem', background: '#f5f5f5', borderRadius: '4px' }}>
        <div>
          <label style={{ display: 'block' }}>Recherche</label>
          <input 
            type="text" 
            value={search} 
            onChange={(e) => setSearch(e.target.value)} 
            placeholder="Nom ou matricule"
            data-testid="search-input"
          />
        </div>
        <div>
          <label style={{ display: 'block' }}>Département</label>
          <input 
            type="text" 
            value={department} 
            onChange={(e) => setDepartment(e.target.value)} 
            placeholder="Département"
            data-testid="department-input"
          />
        </div>
        <div>
          <label style={{ display: 'flex', alignItems: 'center', height: '100%', marginTop: '1rem', gap: '0.5rem' }}>
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

      {error && <div style={{ color: 'red', marginBottom: '1rem' }} data-testid="error-message">{error}</div>}

      {loading ? (
        <div data-testid="loading-indicator">Chargement...</div>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse' }} data-testid="employee-table">
          <thead>
            <tr>
              <th style={{ textAlign: 'left', padding: '0.5rem', borderBottom: '2px solid #ccc' }}>Matricule</th>
              <th style={{ textAlign: 'left', padding: '0.5rem', borderBottom: '2px solid #ccc' }}>Nom complet</th>
              <th style={{ textAlign: 'left', padding: '0.5rem', borderBottom: '2px solid #ccc' }}>Département</th>
              <th style={{ textAlign: 'left', padding: '0.5rem', borderBottom: '2px solid #ccc' }}>Statut</th>
              <th style={{ textAlign: 'left', padding: '0.5rem', borderBottom: '2px solid #ccc' }}>Visage Enrollé</th>
              <th style={{ textAlign: 'left', padding: '0.5rem', borderBottom: '2px solid #ccc' }}>Dernière Synchro</th>
              <th style={{ textAlign: 'left', padding: '0.5rem', borderBottom: '2px solid #ccc' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {employees.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: '1rem' }}>Aucun employé trouvé.</td>
              </tr>
            ) : (
              employees.map(emp => (
                <tr key={emp.id} data-testid={`employee-row-${emp.id}`}>
                  <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>{emp.employee_number}</td>
                  <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>{emp.full_name}</td>
                  <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>{emp.department || '-'}</td>
                  <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>{emp.active ? 'Actif' : 'Inactif'}</td>
                  <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>{emp.has_face_reference ? 'Oui' : 'Non'}</td>
                  <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>{new Date(emp.synced_at).toLocaleString()}</td>
                  <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>
                    <Link to={`/employees/${emp.id}/history`}>Historique</Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      )}
    </div>
  );
};
