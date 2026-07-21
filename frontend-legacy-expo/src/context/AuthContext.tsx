import React, { createContext, useCallback, useContext, useMemo, useState } from 'react';
import * as api from '../api/mockApi';
import { Guard } from '../api/types';

interface AuthContextValue {
  guard: Guard | null;
  isLoading: boolean;
  signIn: (username: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [guard, setGuard] = useState<Guard | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const signIn = useCallback(async (username: string, password: string) => {
    setIsLoading(true);
    try {
      const { guard: signedInGuard } = await api.login(username, password);
      setGuard(signedInGuard);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const signOut = useCallback(async () => {
    await api.logout();
    setGuard(null);
  }, []);

  const value = useMemo(() => ({ guard, isLoading, signIn, signOut }), [guard, isLoading, signIn, signOut]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
}
