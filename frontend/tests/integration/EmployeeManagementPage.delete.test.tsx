import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import EmployeeManagementPage from '../../src/pages/EmployeeManagementPage';
import { SessionProvider } from '../../src/auth/SessionContext';
import { server } from '../msw/server';
import { describe, it, expect, vi, beforeEach } from 'vitest';

const employeeListFixture = [
  {
    id: 'no-history-id',
    full_name: 'No History Employee',
    employee_number: 'EMP-NOHIST',
    department: 'Security',
    active: true,
    has_face_reference: false
  },
  {
    id: 'has-history-id',
    full_name: 'Has History Employee',
    employee_number: 'EMP-HIST',
    department: 'Security',
    active: true,
    has_face_reference: true
  }
];

beforeEach(() => {
  server.use(
    http.get('/employees', () => HttpResponse.json(employeeListFixture))
  );
});

vi.mock('../../src/auth/SessionContext', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual as any,
    useSession: () => ({
      user: { id: 'admin1', username: 'admin', role: 'admin' },
      token: 'admin-token',
      login: vi.fn(),
      logout: vi.fn()
    })
  };
});

const renderWithRouter = () => {
  const router = createMemoryRouter(
    [
      { path: '/manage', element: <EmployeeManagementPage /> }
    ],
    { initialEntries: ['/manage'] }
  );

  render(
    <SessionProvider>
      <RouterProvider router={router} />
    </SessionProvider>
  );
};

describe('EmployeeManagementPage delete flow', () => {
  it('lists employees and deletes one with no history after confirmation', async () => {
    renderWithRouter();

    await waitFor(() => {
      expect(screen.getByText('No History Employee')).toBeInTheDocument();
    });

    const row = screen.getByText('No History Employee').closest('.admin-row') as HTMLElement;
    fireEvent.click(within(row).getByRole('button', { name: /supprimer/i }));
    fireEvent.click(within(row).getByRole('button', { name: /confirmer/i }));

    await waitFor(() => {
      expect(screen.queryByText('No History Employee')).not.toBeInTheDocument();
    });
  });

  it('offers deactivation fallback when delete is blocked by history (409)', async () => {
    renderWithRouter();

    await waitFor(() => {
      expect(screen.getByText('Has History Employee')).toBeInTheDocument();
    });

    const row = screen.getByText('Has History Employee').closest('.admin-row') as HTMLElement;
    fireEvent.click(within(row).getByRole('button', { name: /supprimer/i }));
    fireEvent.click(within(row).getByRole('button', { name: /confirmer/i }));

    await waitFor(() => {
      expect(screen.getByText(/cannot be deleted/i)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /désactiver à la place/i }));

    await waitFor(() => {
      expect(screen.queryByText('Has History Employee')).not.toBeInTheDocument();
    });
  });
});
