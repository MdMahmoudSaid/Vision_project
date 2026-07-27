import React, { useCallback, useEffect, useState } from 'react';
import { getUsers, inviteUser, updateUser, type CloudUser } from '../api/users';
import { describeError } from '../api/client';

type CloudRole = 'owner' | 'admin' | 'viewer';

export const UserManagementPage: React.FC = () => {
  const [users, setUsers] = useState<CloudUser[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<CloudRole>('viewer');
  const [inviting, setInviting] = useState(false);
  const [inviteError, setInviteError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setUsers(await getUsers());
    } catch (err) {
      setError(describeError(err, 'Erreur de chargement').message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    setInviteError(null);
    setInviting(true);
    try {
      await inviteUser({ email, role, password });
      setEmail('');
      setPassword('');
      setRole('viewer');
      await load();
    } catch (err) {
      setInviteError(describeError(err, "Erreur lors de l'invitation").message);
    } finally {
      setInviting(false);
    }
  };

  const handleRoleChange = async (userId: string, newRole: CloudRole) => {
    try {
      await updateUser(userId, { role: newRole });
      await load();
    } catch (err) {
      setError(describeError(err, 'Erreur lors du changement de rôle').message);
    }
  };

  const handleToggleActive = async (userId: string, active: boolean) => {
    try {
      await updateUser(userId, { active: !active });
      await load();
    } catch (err) {
      setError(describeError(err, "Erreur lors de la révocation").message);
    }
  };

  return (
    <div style={{ padding: '2rem' }}>
      <h1>Gestion des utilisateurs</h1>

      <div style={{ background: '#f8f9fa', padding: '1.5rem', borderRadius: '8px', marginBottom: '2rem' }}>
        <h3>Inviter un utilisateur</h3>
        <form onSubmit={handleInvite} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '0.25rem' }}>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              data-testid="invite-email-input"
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '0.25rem' }}>Mot de passe initial</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              data-testid="invite-password-input"
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '0.25rem' }}>Rôle</label>
            <select value={role} onChange={(e) => setRole(e.target.value as CloudRole)} data-testid="invite-role-select">
              <option value="owner">Owner</option>
              <option value="admin">Admin</option>
              <option value="viewer">Viewer</option>
            </select>
          </div>
          <button type="submit" disabled={inviting} data-testid="invite-submit-btn">
            {inviting ? 'Invitation...' : 'Inviter'}
          </button>
        </form>
        {inviteError && <div style={{ color: 'red', marginTop: '0.5rem' }} data-testid="invite-error">{inviteError}</div>}
      </div>

      {loading && <p data-testid="loading-indicator">Chargement...</p>}
      {error && <div style={{ color: 'red' }} data-testid="error-message">{error}</div>}

      <table data-testid="users-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th style={{ textAlign: 'left', padding: '0.5rem' }}>Email</th>
            <th style={{ textAlign: 'left', padding: '0.5rem' }}>Rôle</th>
            <th style={{ textAlign: 'left', padding: '0.5rem' }}>Statut</th>
            <th style={{ textAlign: 'left', padding: '0.5rem' }}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id} data-testid={`user-row-${u.id}`}>
              <td style={{ padding: '0.5rem' }}>{u.email}</td>
              <td style={{ padding: '0.5rem' }}>
                <select
                  value={u.role}
                  onChange={(e) => handleRoleChange(u.id!, e.target.value as CloudRole)}
                  data-testid={`role-select-${u.id}`}
                >
                  <option value="owner">Owner</option>
                  <option value="admin">Admin</option>
                  <option value="viewer">Viewer</option>
                </select>
              </td>
              <td style={{ padding: '0.5rem' }}>{u.active ? 'Actif' : 'Révoqué'}</td>
              <td style={{ padding: '0.5rem' }}>
                <button
                  type="button"
                  onClick={() => handleToggleActive(u.id!, !!u.active)}
                  data-testid={`toggle-active-${u.id}`}
                >
                  {u.active ? 'Révoquer' : 'Réactiver'}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
