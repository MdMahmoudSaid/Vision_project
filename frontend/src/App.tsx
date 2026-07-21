import { Outlet, Navigate, useLocation, NavLink } from 'react-router-dom';
import { useSession, SessionProvider } from './auth/SessionContext';
import { useTheme } from './theme/ThemeContext';

export const ProtectedLayout = () => {
  const { token, user, logout } = useSession();
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();

  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  const navLinkClass = ({ isActive }: { isActive: boolean }) => (isActive ? 'is-active' : '');

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-row">
          <div className="topbar-brand">
            <span className="topbar-mark" aria-hidden="true" />
            Pointage
          </div>

          <div className="user-chip">
            <span className="user-chip-id">
              <span className="role">{user?.role}</span> · {user?.username}
            </span>
            <button
              onClick={toggleTheme}
              className="theme-toggle"
              aria-label={theme === 'dark' ? 'Passer en mode clair' : 'Passer en mode sombre'}
              title={theme === 'dark' ? 'Mode clair' : 'Mode sombre'}
            >
              {theme === 'dark' ? '☀' : '☾'}
            </button>
            <button onClick={logout} className="logout-btn">Déconnexion</button>
          </div>
        </div>

        <nav className="topbar-nav">
          <NavLink to="/attendance" className={navLinkClass}>Pointage</NavLink>
          <NavLink to="/search" className={navLinkClass}>Recherche</NavLink>
          <NavLink to="/shift-activity" className={navLinkClass}>Activité</NavLink>
          {user?.role === 'admin' && (
            <NavLink to="/manage" className={navLinkClass}>Employés</NavLink>
          )}
        </nav>
      </header>
      <main className="page">
        <Outlet />
      </main>
    </div>
  );
};

export default function App() {
  return (
    <SessionProvider>
      <Outlet />
    </SessionProvider>
  );
}
