import React from 'react';
import { render, screen, act } from '@testing-library/react';
import { SessionProvider, useSession } from '../../src/auth/SessionContext';
import { clearSessionToken, clearSessionUser } from '../../src/api/client';
import { describe, it, expect, beforeEach } from 'vitest';

const TestComponent = () => {
  const { token, user, login, logout } = useSession();
  
  return (
    <div>
      <div data-testid="token">{token || 'no-token'}</div>
      <div data-testid="user">{user ? user.username : 'no-user'}</div>
      <button 
        data-testid="login-btn" 
        onClick={() => login('test-token', { id: '1', username: 'testuser', full_name: 'Test', role: 'guard' } as any)}
      >
        Login
      </button>
      <button data-testid="logout-btn" onClick={logout}>Logout</button>
    </div>
  );
};

describe('SessionContext', () => {
  beforeEach(() => {
    clearSessionToken();
    clearSessionUser();
  });

  it('provides default null state', () => {
    render(<SessionProvider><TestComponent /></SessionProvider>);
    expect(screen.getByTestId('token').textContent).toBe('no-token');
  });

  it('updates state on login and logout', () => {
    render(<SessionProvider><TestComponent /></SessionProvider>);
    
    act(() => {
      screen.getByTestId('login-btn').click();
    });
    
    expect(screen.getByTestId('token').textContent).toBe('test-token');
    expect(screen.getByTestId('user').textContent).toBe('testuser');
    
    act(() => {
      screen.getByTestId('logout-btn').click();
    });
    
    expect(screen.getByTestId('token').textContent).toBe('no-token');
  });

  it('logs out on auth:unauthorized event', () => {
    render(<SessionProvider><TestComponent /></SessionProvider>);
    
    act(() => {
      screen.getByTestId('login-btn').click();
    });
    expect(screen.getByTestId('token').textContent).toBe('test-token');

    act(() => {
      window.dispatchEvent(new Event('auth:unauthorized'));
    });
    
    expect(screen.getByTestId('token').textContent).toBe('no-token');
  });
});
