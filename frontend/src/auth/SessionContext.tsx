import React, { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { getSessionToken, getSessionUser, setSessionToken, setSessionUser, clearSessionToken, clearSessionUser } from '../api/client';
import type { components } from '../api/types';

type LocalUser = components['schemas']['LocalUser'];

interface SessionContextType {
  token: string | null;
  user: LocalUser | null;
  login: (token: string, user: LocalUser) => void;
  logout: () => void;
}

const SessionContext = createContext<SessionContextType | undefined>(undefined);

export const SessionProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [token, setTokenState] = useState<string | null>(getSessionToken());
  const [user, setUserState] = useState<LocalUser | null>(getSessionUser());

  useEffect(() => {
    const handleUnauthorized = () => {
      logout();
    };
    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => {
      window.removeEventListener('auth:unauthorized', handleUnauthorized);
    };
  }, []);

  const login = (newToken: string, newUser: LocalUser) => {
    setSessionToken(newToken);
    setSessionUser(newUser);
    setTokenState(newToken);
    setUserState(newUser);
  };

  const logout = () => {
    clearSessionToken();
    clearSessionUser();
    setTokenState(null);
    setUserState(null);
  };

  return (
    <SessionContext.Provider value={{ token, user, login, logout }}>
      {children}
    </SessionContext.Provider>
  );
};

export const useSession = () => {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  return context;
};
