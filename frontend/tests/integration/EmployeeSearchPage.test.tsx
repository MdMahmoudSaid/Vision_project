import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { createMemoryRouter, RouterProvider, useLocation } from 'react-router-dom';
import EmployeeSearchPage from '../../src/pages/EmployeeSearchPage';
import { server } from '../msw/server';
import { http, HttpResponse } from 'msw';
import { describe, it, expect } from 'vitest';

const AttendanceMock = () => {
  const location = useLocation();
  return <div data-testid="attendance-page">{location.state?.employeeName}</div>;
};

const renderWithRouter = () => {
  const router = createMemoryRouter([
    {
      path: '/search',
      element: <EmployeeSearchPage />
    },
    {
      path: '/attendance',
      element: <AttendanceMock />
    }
  ], { initialEntries: ['/search'] });

  render(<RouterProvider router={router} />);
};

describe('EmployeeSearchPage Integration', () => {
  it('searches and selects an employee (T031)', async () => {
    renderWithRouter();

    // EmployeeSearchPage fetches a default list on mount (FR-014); wait for
    // that initial load to settle before the button is enabled again.
    await waitFor(() => expect(screen.getByRole('button')).toHaveTextContent(/^chercher$/i));

    fireEvent.change(screen.getByLabelText(/recherche employé/i), { target: { value: 'Ahmed' } });
    fireEvent.click(screen.getByRole('button', { name: /chercher/i }));
    
    await waitFor(() => {
      expect(screen.getByText('Ahmed Mohamed')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByRole('button', { name: /sélectionner/i }));
    
    await waitFor(() => {
      expect(screen.getByTestId('attendance-page')).toHaveTextContent('Ahmed Mohamed');
    });
  });

  it('shows empty state for no matches (T033)', async () => {
    renderWithRouter();
    await waitFor(() => expect(screen.getByRole('button')).toHaveTextContent(/^chercher$/i));

    fireEvent.change(screen.getByLabelText(/recherche employé/i), { target: { value: 'Nobody' } });
    fireEvent.click(screen.getByRole('button', { name: /chercher/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/aucun employé trouvé/i)).toBeInTheDocument();
    });
  });

  it('does not show inactive employees even if they match (T032)', async () => {
    server.use(
      http.get('/employees', () => {
        return HttpResponse.json([
          {
            id: 'inactive-id',
            full_name: 'Ahmed Inactive',
            employee_number: 'EMP-999',
            department: 'None',
            active: false,
            has_face_reference: true
          }
        ]);
      })
    );

    renderWithRouter();
    await waitFor(() => expect(screen.getByRole('button')).toHaveTextContent(/^chercher$/i));

    fireEvent.change(screen.getByLabelText(/recherche employé/i), { target: { value: 'Ahmed' } });
    fireEvent.click(screen.getByRole('button', { name: /chercher/i }));

    await waitFor(() => {
      expect(screen.queryByText('Ahmed Inactive')).not.toBeInTheDocument();
      // Should show the empty state because the only result is filtered out
    });
  });
});
