import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import AttendancePage from '../../src/pages/AttendancePage';
import { describe, it, expect } from 'vitest';

const renderWithRouter = (initialState: any = { employeeId: 'emp-success', employeeName: 'Test Employee' }) => {
  const router = createMemoryRouter([
    {
      path: '/attendance',
      element: <AttendancePage />
    },
    {
      path: '/search',
      element: <div data-testid="search-page">Search Page</div>
    }
  ], { initialEntries: [{ pathname: '/attendance', state: initialState }] });

  render(<RouterProvider router={router} />);
};

describe('AttendancePage Integration - Success', () => {
  it('shows success banner on successful arrival', async () => {
    renderWithRouter();
    
    expect(screen.getByText(/pointage pour/i)).toBeInTheDocument();
    
    fireEvent.click(screen.getByRole('button', { name: /arrivée/i }));

    // The camera preview step appears first; confirm immediately rather
    // than waiting for the auto-advance timer.
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /vérifier maintenant/i })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: /vérifier maintenant/i }));

    await waitFor(() => {
      expect(screen.getByText('Pointage réussi')).toBeInTheDocument();
    });
    
    // Clicking done should navigate to search
    fireEvent.click(screen.getByRole('button', { name: /terminé/i }));
    
    await waitFor(() => {
      expect(screen.getByTestId('search-page')).toBeInTheDocument();
    });
  });
});
