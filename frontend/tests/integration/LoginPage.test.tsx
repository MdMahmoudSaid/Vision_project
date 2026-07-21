import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import LoginPage from '../../src/pages/LoginPage';
import { SessionProvider } from '../../src/auth/SessionContext';
import { ThemeProvider } from '../../src/theme/ThemeContext';
import { server } from '../msw/server';
import { http, HttpResponse } from 'msw';
import { describe, it, expect } from 'vitest';

const renderWithRouter = () => {
  const router = createMemoryRouter([
    {
      path: '/login',
      element: <LoginPage />
    },
    {
      path: '/attendance',
      element: <div data-testid="attendance-page">Attendance</div>
    }
  ], { initialEntries: ['/login'] });

  render(
    <ThemeProvider>
      <SessionProvider>
        <RouterProvider router={router} />
      </SessionProvider>
    </ThemeProvider>
  );
};

describe('LoginPage Integration', () => {
  it('redirects to /attendance on successful login', async () => {
    renderWithRouter();
    
    fireEvent.change(screen.getByLabelText(/nom d'utilisateur/i), { target: { value: 'garde1' } });
    fireEvent.change(screen.getByLabelText(/mot de passe/i), { target: { value: 'my_password' } });
    fireEvent.click(screen.getByRole('button', { name: /se connecter/i }));
    
    await waitFor(() => {
      expect(screen.getByTestId('attendance-page')).toBeInTheDocument();
    });
  });

  it('shows error message on failed login', async () => {
    server.use(
      http.post('/auth/login', () => {
        return HttpResponse.json({ detail: 'Incorrect username or password' }, { status: 401 });
      })
    );

    renderWithRouter();
    
    fireEvent.change(screen.getByLabelText(/nom d'utilisateur/i), { target: { value: 'wrong' } });
    fireEvent.change(screen.getByLabelText(/mot de passe/i), { target: { value: 'wrong' } });
    fireEvent.click(screen.getByRole('button', { name: /se connecter/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/identifiants incorrects/i)).toBeInTheDocument();
    });
  });
});
