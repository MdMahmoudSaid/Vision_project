import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { AppRoutes } from './routes';
import { useSession } from './auth/SessionContext';

const NavShell: React.FC = () => {
  const { user, logout } = useSession();
  const navigate = useNavigate();

  if (!user) {
    return null;
  }

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  return (
    <nav className="app-nav">
      <Link to="/" className="app-nav-brand">Pointage Cloud</Link>
      <div className="app-nav-links">
        <Link to="/employees">Employés</Link>
        <Link to="/reports">Rapports</Link>
        {user.role === 'owner' && <Link to="/users">Utilisateurs</Link>}
      </div>
      <div className="app-nav-user">
        <span>{user.email} ({user.role})</span>
        <button type="button" onClick={handleLogout}>Déconnexion</button>
      </div>
    </nav>
  );
};

export const App: React.FC = () => {
  const location = useLocation();
  const isLoginPage = location.pathname === '/login';

  return (
    <div className="app-shell">
      {!isLoginPage && <NavShell />}
      <main className="app-main">
        <AppRoutes />
      </main>
    </div>
  );
};
