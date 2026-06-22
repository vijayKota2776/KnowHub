import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('kh_token'));
  const [loading, setLoading] = useState(true);

  // Fetch user profile on mount if token exists
  useEffect(() => {
    if (token) {
      api.users.me()
        .then(setUser)
        .catch(() => {
          // Token invalid — clear it
          localStorage.removeItem('kh_token');
          localStorage.removeItem('kh_user_id');
          setToken(null);
          setUser(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [token]);

  const login = useCallback(async (email, password) => {
    const data = await api.auth.login({ email, password });
    const t = data.token.access_token;
    localStorage.setItem('kh_token', t);
    localStorage.setItem('kh_user_id', data.user_id);
    setToken(t);
    // Fetch full profile
    const profile = await api.users.me();
    setUser(profile);
    return profile;
  }, []);

  const register = useCallback(async (username, email, password) => {
    const data = await api.auth.register({ username, email, password });
    const t = data.token.access_token;
    localStorage.setItem('kh_token', t);
    localStorage.setItem('kh_user_id', data.user.user_id);
    setToken(t);
    const profile = await api.users.me();
    setUser(profile);
    return profile;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('kh_token');
    localStorage.removeItem('kh_user_id');
    setToken(null);
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    if (!token) return;
    const profile = await api.users.me();
    setUser(profile);
    return profile;
  }, [token]);

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout, refreshUser, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
