import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
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
  const router = createMemoryRouter(
    [
      {
        path: '/enroll',
        element: <FaceEnrollmentPage />
      },
      {
        path: '/search',
        element: <div data-testid="search-page">Search Page</div>
      }
    ],
    { initialEntries: [{ pathname: '/enroll', state: { employeeId: 'no-face-emp-id', employeeName: 'No Face Employee' } }] }
  );

  render(
    <SessionProvider>
      <RouterProvider router={router} />
    </SessionProvider>
  );
};

describe('FaceEnrollmentPage - No Face Detected', () => {
  it('shows an actionable alert instead of a false success when no clear face was captured', async () => {
    renderWithRouter();

    fireEvent.click(screen.getByRole('button', { name: /lancer l'enrôlement/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /capturer maintenant/i })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: /capturer maintenant/i }));

    await waitFor(() => {
      expect(screen.getByText('Aucun visage détecté')).toBeInTheDocument();
      expect(screen.queryByText(/enrôlement réussi/i)).not.toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /réessayer/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /lancer l'enrôlement/i })).toBeInTheDocument();
    });
  });
});
