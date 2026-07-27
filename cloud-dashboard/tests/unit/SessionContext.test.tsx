import { render, screen, act } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { SessionProvider, useSession } from '../../src/auth/SessionContext';
import React from 'react';
import * as clientApi from '../../src/api/client';

// Simple component to test context values
const TestComponent = () => {
  const { token, user, login, logout } = useSession();
  
  return (
    <div>
      <div data-testid="token">{token || 'no-token'}</div>
      <div data-testid="user">{user ? user.email : 'no-user'}</div>
      <button 
        onClick={() => login('new-token', { id: 'u1', email: 'test@example.com', role: 'admin' } as any)}
      >
        Do Login
      </button>
      <button onClick={logout}>Do Logout</button>
    </div>
  );
};

describe('SessionContext', () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.clearAllMocks();
  });

  it('provides null token and user initially when session storage is empty', () => {
    render(
      <SessionProvider>
        <TestComponent />
      </SessionProvider>
    );
    
    expect(screen.getByTestId('token').textContent).toBe('no-token');
    expect(screen.getByTestId('user').textContent).toBe('no-user');
  });

  it('loads initial state from session storage', () => {
    sessionStorage.setItem('token', 'stored-token');
    sessionStorage.setItem('user', JSON.stringify({ email: 'stored@example.com' }));
    
    render(
      <SessionProvider>
        <TestComponent />
      </SessionProvider>
    );
    
    expect(screen.getByTestId('token').textContent).toBe('stored-token');
    expect(screen.getByTestId('user').textContent).toBe('stored@example.com');
  });

  it('updates state and session storage on login', () => {
    render(
      <SessionProvider>
        <TestComponent />
      </SessionProvider>
    );
    
    act(() => {
      screen.getByText('Do Login').click();
    });
    
    expect(screen.getByTestId('token').textContent).toBe('new-token');
    expect(screen.getByTestId('user').textContent).toBe('test@example.com');
    expect(sessionStorage.getItem('token')).toBe('new-token');
  });

  it('clears state and session storage on logout', () => {
    sessionStorage.setItem('token', 'stored-token');
    sessionStorage.setItem('user', JSON.stringify({ email: 'stored@example.com' }));
    
    render(
      <SessionProvider>
        <TestComponent />
      </SessionProvider>
    );
    
    act(() => {
      screen.getByText('Do Logout').click();
    });
    
    expect(screen.getByTestId('token').textContent).toBe('no-token');
    expect(screen.getByTestId('user').textContent).toBe('no-user');
    expect(sessionStorage.getItem('token')).toBeNull();
  });

  it('logs out when auth:unauthorized event is fired', () => {
    sessionStorage.setItem('token', 'stored-token');
    sessionStorage.setItem('user', JSON.stringify({ email: 'stored@example.com' }));
    
    render(
      <SessionProvider>
        <TestComponent />
      </SessionProvider>
    );
    
    act(() => {
      window.dispatchEvent(new Event('auth:unauthorized'));
    });
    
    expect(screen.getByTestId('token').textContent).toBe('no-token');
    expect(screen.getByTestId('user').textContent).toBe('no-user');
  });
});
