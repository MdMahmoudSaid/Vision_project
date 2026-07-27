import React from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { AppRoutes } from './routes';
import { useSession } from './auth/SessionContext';
import { useTheme } from './theme/ThemeContext';

const navLinkClass = ({ isActive }: { isActive: boolean }) => (isActive ? 'is-active' : '');

const NavShell: React.FC = () => {
  const { user, logout } = useSession();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();

  if (!user) {
    return null;
  }

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  return (
    <header className="topbar">
      <div className="topbar-row">
        <NavLink to="/" className="topbar-brand">
          <span className="topbar-mark" aria-hidden="true" />
          Pointage Cloud
        </NavLink>

        <div className="user-chip">
          <span className="user-chip-id">
            <span className="role">{user.role}</span> · {user.email}
          </span>
          <button
            onClick={toggleTheme}
            className="theme-toggle"
            aria-label={theme === 'dark' ? 'Passer en mode clair' : 'Passer en mode sombre'}
            title={theme === 'dark' ? 'Mode clair' : 'Mode sombre'}
          >
            {theme === 'dark' ? '☀' : '☾'}
          </button>
          <button onClick={handleLogout} className="logout-btn">Déconnexion</button>
        </div>
      </div>

      <nav className="topbar-nav">
        <NavLink to="/employees" className={navLinkClass}>Employés</NavLink>
        <NavLink to="/reports" className={navLinkClass}>Rapports</NavLink>
        {user.role === 'owner' && <NavLink to="/users" className={navLinkClass}>Utilisateurs</NavLink>}
      </nav>
    </header>
  );
};

export const App: React.FC = () => {
  const location = useLocation();
  const isLoginPage = location.pathname === '/login';

  return (
    <div className="app-shell">
      {!isLoginPage && <NavShell />}
      <main className="page">
        <AppRoutes />
      </main>
    </div>
  );
};
