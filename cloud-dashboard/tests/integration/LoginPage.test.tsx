import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, beforeAll, afterAll, afterEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { SessionProvider } from '../../src/auth/SessionContext';
import { AppRoutes } from '../../src/routes';
import { server } from '../msw/server';

describe('LoginPage Integration', () => {
  afterEach(() => {
    sessionStorage.clear();
  });

  const renderApp = () => {
    // Start at login page
    window.history.pushState({}, 'Login', '/login');
    render(
      <SessionProvider>
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </SessionProvider>
    );
  };

  it('renders login form', () => {
    renderApp();
    expect(screen.getByTestId('email-input')).toBeInTheDocument();
    expect(screen.getByTestId('password-input')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /se connecter/i })).toBeInTheDocument();
  });

  it('navigates to overview on successful owner login', async () => {
    renderApp();
    
    fireEvent.change(screen.getByTestId('email-input'), { target: { value: 'owner@example.com' } });
    fireEvent.change(screen.getByTestId('password-input'), { target: { value: 'ownerpass' } });
    fireEvent.click(screen.getByRole('button', { name: /se connecter/i }));
    
    await waitFor(() => {
      expect(screen.getByText('Overview')).toBeInTheDocument();
    });
    
    expect(sessionStorage.getItem('token')).toBe('fake-jwt-token-owner');
  });

  it('navigates to overview on successful admin login', async () => {
    renderApp();
    
    fireEvent.change(screen.getByTestId('email-input'), { target: { value: 'admin@example.com' } });
    fireEvent.change(screen.getByTestId('password-input'), { target: { value: 'adminpass' } });
    fireEvent.click(screen.getByRole('button', { name: /se connecter/i }));
    
    await waitFor(() => {
      expect(screen.getByText('Overview')).toBeInTheDocument();
    });
    
    expect(sessionStorage.getItem('token')).toBe('fake-jwt-token-admin');
  });

  it('displays error on failed login', async () => {
    renderApp();
    
    fireEvent.change(screen.getByTestId('email-input'), { target: { value: 'owner@example.com' } });
    fireEvent.change(screen.getByTestId('password-input'), { target: { value: 'wrong' } });
    fireEvent.click(screen.getByRole('button', { name: /se connecter/i }));
    
    await waitFor(() => {
      expect(screen.getByTestId('error-message')).toHaveTextContent('Invalid credentials or inactive account');
    });
    
    expect(sessionStorage.getItem('token')).toBeNull();
  });
});
