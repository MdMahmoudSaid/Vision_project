import React, { useCallback, useEffect, useState } from 'react';
import { getUsers, inviteUser, updateUser, deleteUser, type CloudUser } from '../api/users';
import { ApiError, describeError } from '../api/client';
import { useSession } from '../auth/SessionContext';

type CloudRole = 'owner' | 'admin' | 'viewer';

export const UserManagementPage: React.FC = () => {
  const { user: currentUser } = useSession();
  const [users, setUsers] = useState<CloudUser[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<CloudRole>('viewer');
  const [inviting, setInviting] = useState(false);
  const [inviteError, setInviteError] = useState<string | null>(null);

  const [confirmingId, setConfirmingId] = useState<string | null>(null);
  const [rowBusyId, setRowBusyId] = useState<string | null>(null);
  const [rowError, setRowError] = useState<{ id: string; message: string; hasCorrections: boolean } | null>(null);

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

  const handleDelete = async (userId: string) => {
    setRowBusyId(userId);
    setRowError(null);
    try {
      await deleteUser(userId);
      setConfirmingId(null);
      setUsers((prev) => prev.filter((u) => u.id !== userId));
    } catch (err) {
      if (err instanceof ApiError && err.status === 409 && err.code === 'user_has_corrections') {
        setRowError({
          id: userId,
          message:
            'Cet utilisateur a effectué des corrections qui doivent rester dans le journal d\'audit ; '
            + 'il ne peut pas être supprimé. Vous pouvez le révoquer à la place.',
          hasCorrections: true,
        });
      } else {
        setRowError({ id: userId, message: describeError(err, 'Suppression impossible').message, hasCorrections: false });
      }
    } finally {
      setRowBusyId(null);
    }
  };

  return (
    <div>
      <div className="page-eyebrow">Cloud · Owner</div>
      <h1 className="page-title">Gestion des utilisateurs</h1>

      <div className="card">
        <h3 style={{ marginBottom: 'var(--spacing-md)' }}>Inviter un utilisateur</h3>
        <form onSubmit={handleInvite} className="filter-row">
          <div className="field">
            <label htmlFor="invite-email">Email</label>
            <input
              id="invite-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              data-testid="invite-email-input"
            />
          </div>
          <div className="field">
            <label htmlFor="invite-password">Mot de passe initial</label>
            <input
              id="invite-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              data-testid="invite-password-input"
            />
          </div>
          <div className="field">
            <label htmlFor="invite-role">Rôle</label>
            <select
              id="invite-role"
              value={role}
              onChange={(e) => setRole(e.target.value as CloudRole)}
              data-testid="invite-role-select"
            >
              <option value="owner">Owner</option>
              <option value="admin">Admin</option>
              <option value="viewer">Viewer</option>
            </select>
          </div>
          <button type="submit" disabled={inviting} className="btn btn-primary btn-medium" data-testid="invite-submit-btn">
            {inviting ? 'Invitation...' : 'Inviter'}
          </button>
        </form>
        {inviteError && <div className="notice notice--error" style={{ marginTop: 'var(--spacing-md)' }} data-testid="invite-error">{inviteError}</div>}
      </div>

      {loading && <p className="page-subtitle" data-testid="loading-indicator">Chargement...</p>}
      {error && <div className="notice notice--error" data-testid="error-message">{error}</div>}

      <div className="table-wrap">
        <table className="data-table" data-testid="users-table">
          <thead>
            <tr>
              <th>Email</th>
              <th>Rôle</th>
              <th>Statut</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => {
              const isSelf = u.id === currentUser?.id;
              return (
                <tr key={u.id} data-testid={`user-row-${u.id}`}>
                  <td>{u.email}</td>
                  <td>
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
                  <td>
                    <span className={`status-tag status-tag--${u.active ? 'go' : 'neutral'}`}>
                      {u.active ? 'Actif' : 'Révoqué'}
                    </span>
                  </td>
                  <td>
                    <div className="data-table-actions">
                      <button
                        type="button"
                        className="btn btn-secondary btn-small"
                        onClick={() => handleToggleActive(u.id!, !!u.active)}
                        data-testid={`toggle-active-${u.id}`}
                      >
                        {u.active ? 'Révoquer' : 'Réactiver'}
                      </button>

                      {confirmingId === u.id ? (
                        <>
                          <button
                            type="button"
                            className="btn btn-danger btn-small"
                            onClick={() => handleDelete(u.id!)}
                            disabled={rowBusyId === u.id}
                            data-testid={`confirm-delete-${u.id}`}
                          >
                            {rowBusyId === u.id ? 'Suppression...' : 'Confirmer'}
                          </button>
                          <button
                            type="button"
                            className="btn btn-secondary btn-small"
                            onClick={() => setConfirmingId(null)}
                            disabled={rowBusyId === u.id}
                          >
                            Annuler
                          </button>
                        </>
                      ) : (
                        <button
                          type="button"
                          className="btn btn-outline-danger btn-small"
                          onClick={() => {
                            setConfirmingId(u.id!);
                            setRowError(null);
                          }}
                          disabled={isSelf}
                          title={isSelf ? 'Vous ne pouvez pas supprimer votre propre compte' : undefined}
                          data-testid={`delete-btn-${u.id}`}
                        >
                          Supprimer
                        </button>
                      )}
                    </div>

                    {rowError?.id === u.id && (
                      <div className="notice notice--error" style={{ marginTop: 'var(--spacing-sm)' }} data-testid={`row-error-${u.id}`}>
                        {rowError.message}
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
