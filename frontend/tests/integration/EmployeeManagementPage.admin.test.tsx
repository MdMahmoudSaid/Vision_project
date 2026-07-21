import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import EmployeeManagementPage from '../../src/pages/EmployeeManagementPage';
import FaceEnrollmentPage from '../../src/pages/FaceEnrollmentPage';
import { SessionProvider } from '../../src/auth/SessionContext';
import { describe, it, expect, vi } from 'vitest';

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
  const router = createMemoryRouter([
    {
      path: '/manage',
      element: <EmployeeManagementPage />
    },
    {
      path: '/enroll',
      element: <FaceEnrollmentPage />
    },
    {
      path: '/search',
      element: <div data-testid="search-page">Search Page</div>
    }
  ], { initialEntries: ['/manage'] });

  render(
    <SessionProvider>
      <RouterProvider router={router} />
    </SessionProvider>
  );
};

describe('EmployeeManagementPage Admin Integration', () => {
  it('admin can create employee and enroll face', async () => {
    renderWithRouter();
    
    fireEvent.change(screen.getByLabelText(/nom complet/i), { target: { value: 'New Test Employee' } });
    fireEvent.change(screen.getByLabelText(/matricule/i), { target: { value: 'EMP-999' } });
    
    fireEvent.click(screen.getByRole('button', { name: /créer et passer à l'enrôlement/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/enrôler new test employee/i)).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByRole('button', { name: /lancer l'enrôlement/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /capturer maintenant/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /capturer maintenant/i }));

    await waitFor(() => {
      expect(screen.getByText(/enrôlement réussi/i)).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByRole('button', { name: /terminé/i }));
    
    await waitFor(() => {
      expect(screen.getByTestId('search-page')).toBeInTheDocument();
    });
  });
});
