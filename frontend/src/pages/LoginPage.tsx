import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login } from '../api/auth';
import { useSession } from '../auth/SessionContext';
import { useTheme } from '../theme/ThemeContext';
import { Button } from '../components/Button';
import { ApiError } from '../api/client';

const LoginPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login: setSession } = useSession();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await login({ username, password });
      setSession(res.access_token, res.user);
      navigate('/attendance');
    } catch (err: any) {
      if (err instanceof ApiError && err.status === 0) {
        setError('Connexion au système local impossible. Vérifiez le Wi-Fi.');
      } else {
        setError('Identifiants incorrects');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-shell">
      <div className="login-card">
        <button
          onClick={toggleTheme}
          className="theme-toggle"
          style={{ float: 'right' }}
          aria-label={theme === 'dark' ? 'Passer en mode clair' : 'Passer en mode sombre'}
          title={theme === 'dark' ? 'Mode clair' : 'Mode sombre'}
        >
          {theme === 'dark' ? '☀' : '☾'}
        </button>
        <div className="login-brand">
          <span className="topbar-mark" aria-hidden="true" />
          Pointage
        </div>
        <div className="login-eyebrow">Poste local · Accès sécurisé</div>

        <form onSubmit={handleSubmit} className="stack">
          <div className="field">
            <label htmlFor="username">Nom d'utilisateur</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
            />
          </div>
          <div className="field">
            <label htmlFor="password">Mot de passe</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>
          {error && <div className="login-error">{error}</div>}
          <Button type="submit" disabled={loading}>{loading ? 'Connexion...' : 'Se connecter'}</Button>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
