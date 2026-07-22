import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import AttendancePage from '../../src/pages/AttendancePage';
import { describe, it, expect } from 'vitest';

const renderWithRouter = (initialState: any = { employeeId: 'emp-no-face', employeeName: 'Test Employee' }) => {
  const router = createMemoryRouter([
    {
      path: '/attendance',
      element: <AttendancePage />
    }
  ], { initialEntries: [{ pathname: '/attendance', state: initialState }] });

  render(<RouterProvider router={router} />);
};

describe('AttendancePage Integration - No Face Detected', () => {
  it('shows an actionable alert (not a generic failure) when no face was detected, and allows retry', async () => {
    renderWithRouter();

    fireEvent.click(screen.getByRole('button', { name: /arrivée/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /vérifier maintenant/i })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: /vérifier maintenant/i }));

    await waitFor(() => {
      expect(screen.getByText('Aucun visage détecté')).toBeInTheDocument();
      expect(screen.getByText(/ajustez la posture|bien visible, centré/i)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /réessayer/i }));

    await waitFor(() => {
      expect(screen.queryByText('Aucun visage détecté')).not.toBeInTheDocument();
      expect(screen.getByRole('button', { name: /arrivée/i })).toBeInTheDocument();
    });
  });
});
