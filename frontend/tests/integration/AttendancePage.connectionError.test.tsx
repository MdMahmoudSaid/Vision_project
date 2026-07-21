import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import AttendancePage from '../../src/pages/AttendancePage';
import { server } from '../msw/server';
import { http } from 'msw';
import { describe, it, expect } from 'vitest';

const renderWithRouter = (initialState: any = { employeeId: 'emp-success', employeeName: 'Test Employee' }) => {
  const router = createMemoryRouter([
    {
      path: '/attendance',
      element: <AttendancePage />
    }
  ], { initialEntries: [{ pathname: '/attendance', state: initialState }] });

  render(<RouterProvider router={router} />);
};

describe('AttendancePage Integration - Connection Error', () => {
  it('shows connection error banner on network failure', async () => {
    server.use(
      http.post('/attendance/verify', () => {
        return Response.error(); // Simulates network error
      })
    );

    renderWithRouter();
    
    fireEvent.click(screen.getByRole('button', { name: /arrivée/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /vérifier maintenant/i })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: /vérifier maintenant/i }));

    await waitFor(() => {
      expect(screen.getByText('Erreur de connexion')).toBeInTheDocument();
      expect(screen.getByText(/Could not connect to the local server/i)).toBeInTheDocument();
    });
  });
});
