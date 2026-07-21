import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import AttendancePage from '../../src/pages/AttendancePage';
import { describe, it, expect } from 'vitest';

const renderWithRouter = (initialState: any = { employeeId: 'emp-duplicate', employeeName: 'Test Employee' }) => {
  const router = createMemoryRouter([
    {
      path: '/attendance',
      element: <AttendancePage />
    }
  ], { initialEntries: [{ pathname: '/attendance', state: initialState }] });

  render(<RouterProvider router={router} />);
};

describe('AttendancePage Integration - Duplicate', () => {
  it('shows duplicate blocked banner', async () => {
    renderWithRouter();
    
    fireEvent.click(screen.getByRole('button', { name: /arrivée/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /vérifier maintenant/i })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: /vérifier maintenant/i }));

    await waitFor(() => {
      expect(screen.getByText('Pointage refusé')).toBeInTheDocument();
      expect(screen.getByText('Recent attendance was already recorded for this employee')).toBeInTheDocument();
    });
  });
});
