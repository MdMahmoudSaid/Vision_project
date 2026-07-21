import React from 'react';
import { render, screen } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import EmployeeManagementPage from '../../src/pages/EmployeeManagementPage';
import { SessionProvider } from '../../src/auth/SessionContext';
import { describe, it, expect, vi } from 'vitest';

vi.mock('../../src/auth/SessionContext', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual as any,
    useSession: () => ({
      user: { id: 'guard1', username: 'guard', role: 'guard' },
      token: 'guard-token',
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
    }
  ], { initialEntries: ['/manage'] });

  render(
    <SessionProvider>
      <RouterProvider router={router} />
    </SessionProvider>
  );
};

describe('EmployeeManagementPage Guard Integration', () => {
  it('guard cannot see management page', async () => {
    renderWithRouter();
    
    expect(screen.getByTestId('forbidden')).toHaveTextContent('Accès refusé');
  });
});
