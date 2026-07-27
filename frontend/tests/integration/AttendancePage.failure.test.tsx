import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import AttendancePage from '../../src/pages/AttendancePage';
import { describe, it, expect } from 'vitest';

const renderWithRouter = (initialState: any = { employeeId: 'emp-failed', employeeName: 'Test Employee' }) => {
  const router = createMemoryRouter([
    {
      path: '/attendance',
      element: <AttendancePage />
    }
  ], { initialEntries: [{ pathname: '/attendance', state: initialState }] });

  render(<RouterProvider router={router} />);
};

describe('AttendancePage Integration - Failure', () => {
  it('shows a wrong-face banner naming the employee on face mismatch', async () => {
    renderWithRouter();

    fireEvent.click(screen.getByRole('button', { name: /départ/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /vérifier maintenant/i })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: /vérifier maintenant/i }));

    await waitFor(() => {
      expect(screen.getByText('Visage non reconnu')).toBeInTheDocument();
      expect(
        screen.getByText("Le visage détecté ne correspond pas à celui de Test Employee. Vérifiez l'identité de la personne et réessayez.")
      ).toBeInTheDocument();
    });

    // Can retry
    fireEvent.click(screen.getByRole('button', { name: /réessayer/i }));

    await waitFor(() => {
      expect(screen.queryByText('Visage non reconnu')).not.toBeInTheDocument();
      expect(screen.getByRole('button', { name: /arrivée/i })).toBeInTheDocument();
    });
  });
});
