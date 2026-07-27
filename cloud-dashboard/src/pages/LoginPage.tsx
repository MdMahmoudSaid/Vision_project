import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../auth/SessionContext';
import { login as loginApi } from '../api/auth';
import { describeError } from '../api/client';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { login } = useSession();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const response = await loginApi({ email, password });
      login(response.access_token, response.user);
      navigate('/', { replace: true });
    } catch (err: any) {
      const display = describeError(err, 'Erreur de connexion');
      setError(display.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-shell">
      <div className="login-card">
        <div className="login-brand">
          <span className="topbar-mark" aria-hidden="true" />
          Pointage Cloud
        </div>
        <div className="login-eyebrow">Tableau de bord</div>

        <form onSubmit={handleSubmit} className="stack">
          <div className="field">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              data-testid="email-input"
            />
          </div>
          <div className="field">
            <label htmlFor="password">Mot de passe</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              data-testid="password-input"
            />
          </div>
          {error && <div className="login-error" data-testid="error-message">{error}</div>}
          <button type="submit" disabled={loading} className="btn btn-primary btn-medium btn-block">
            {loading ? 'Connexion...' : 'Se connecter'}
          </button>
        </form>
      </div>
    </div>
  );
};
