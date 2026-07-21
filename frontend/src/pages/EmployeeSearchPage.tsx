import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { searchEmployees, type EmployeeSummary } from '../api/employees';
import { EmployeeListItem } from '../components/EmployeeListItem';
import { Button } from '../components/Button';

const EmployeeSearchPage = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<EmployeeSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const navigate = useNavigate();

  const runSearch = async (q: string) => {
    setLoading(true);
    setHasSearched(true);
    try {
      const res = await searchEmployees(q);
      setResults(res);
    } catch (err) {
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  // Show a default list of active employees on load so a short roster is
  // browsable without requiring the guard to type a query first (FR-014).
  useEffect(() => {
    runSearch('');
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    runSearch(query);
  };

  const handleSelect = (id: string, name: string) => {
    navigate('/attendance', { state: { employeeId: id, employeeName: name } });
  };

  // The server is asked to filter by active=true (avoids fetching data we'd
  // discard for a large roster); this defensive filter keeps FR-004 true
  // even if a response ever includes an inactive employee anyway.
  const visibleResults = results.filter(emp => emp.active !== false);

  return (
    <div>
      <div className="page-eyebrow">Sélection</div>
      <h1 className="page-title">Chercher un employé</h1>

      <form onSubmit={handleSearch} className="search-bar">
        <input
          aria-label="Recherche employé"
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Nom ou matricule..."
        />
        <Button type="submit" disabled={loading} style={{ width: 'auto' }}>
          {loading ? 'Recherche...' : 'Chercher'}
        </Button>
      </form>

      <div>
        {visibleResults.map(emp => (
          <EmployeeListItem
            key={emp.id}
            id={emp.id}
            fullName={emp.full_name}
            employeeNumber={emp.employee_number}
            department={emp.department}
            onSelect={handleSelect}
          />
        ))}
        {hasSearched && !loading && visibleResults.length === 0 && (
          <div className="empty-state">Aucun employé trouvé.</div>
        )}
      </div>
    </div>
  );
};

export default EmployeeSearchPage;
