import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, afterEach, vi } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { SessionProvider } from '../../src/auth/SessionContext';
import { UserManagementPage } from '../../src/pages/UserManagementPage';
import * as clientModule from '../../src/api/client';
import React from 'react';

describe('UserManagementPage Integration', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    sessionStorage.clear();
  });

  const renderApp = () => {
    vi.spyOn(clientModule, 'getSessionUser').mockReturnValue({
      id: 'owner-1',
      email: 'owner@example.com',
      role: 'owner',
      active: true,
    });
    vi.spyOn(clientModule, 'getSessionToken').mockReturnValue('fake-token');

    render(
      <SessionProvider>
        <BrowserRouter>
          <UserManagementPage />
        </BrowserRouter>
      </SessionProvider>
    );
  };

  it('lists existing users', async () => {
    renderApp();
    await waitFor(() => {
      expect(screen.getByText('owner@example.com')).toBeInTheDocument();
      expect(screen.getByText('admin@example.com')).toBeInTheDocument();
    });
  });

  it('invites a new user with a chosen role', async () => {
    renderApp();
    await waitFor(() => {
      expect(screen.getByTestId('users-table')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByTestId('invite-email-input'), { target: { value: 'new-viewer@example.com' } });
    fireEvent.change(screen.getByTestId('invite-password-input'), { target: { value: 'supersecret1' } });
    fireEvent.change(screen.getByTestId('invite-role-select'), { target: { value: 'viewer' } });
    fireEvent.click(screen.getByTestId('invite-submit-btn'));

    await waitFor(() => {
      expect(screen.getByText('new-viewer@example.com')).toBeInTheDocument();
    });
  });

  it('changes an existing user role', async () => {
    renderApp();
    await waitFor(() => {
      expect(screen.getByTestId('role-select-admin-1')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByTestId('role-select-admin-1'), { target: { value: 'viewer' } });

    await waitFor(() => {
      expect((screen.getByTestId('role-select-admin-1') as HTMLSelectElement).value).toBe('viewer');
    });
  });

  it('revokes a user and reflects the revoked status', async () => {
    renderApp();
    await waitFor(() => {
      expect(screen.getByTestId('toggle-active-admin-1')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('toggle-active-admin-1'));

    await waitFor(() => {
      expect(screen.getByTestId('user-row-admin-1')).toHaveTextContent('Révoqué');
    });
  });

  it('deletes a user after confirming', async () => {
    renderApp();
    await waitFor(() => {
      expect(screen.getByTestId('delete-btn-admin-1')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('delete-btn-admin-1'));
    await waitFor(() => {
      expect(screen.getByTestId('confirm-delete-admin-1')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId('confirm-delete-admin-1'));

    await waitFor(() => {
      expect(screen.queryByTestId('user-row-admin-1')).not.toBeInTheDocument();
    });
  });

  it('cannot delete its own account', async () => {
    renderApp();
    await waitFor(() => {
      expect(screen.getByTestId('delete-btn-owner-1')).toBeDisabled();
    });
  });
});
