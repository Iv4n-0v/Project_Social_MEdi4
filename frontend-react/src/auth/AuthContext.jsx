import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { authApi } from '../api/auth';
import { ApiError } from '../api/errors';
import { refreshSession, setAccessToken, setSessionLostHandler } from '../api/http';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [account, setAccount] = useState(null);
  const [ready, setReady] = useState(false); // ya se intento recuperar la sesion

  const applySession = useCallback((s) => {
    setAccessToken(s.access_token);
    setAccount(s.account);
    return s.account;
  }, []);

  // Al abrir la pagina: si hay cookie de sesion, se recupera sin pedir contraseña
  useEffect(() => {
    let alive = true;
    setSessionLostHandler(() => setAccount(null));
    refreshSession()
      .then((s) => alive && setAccount(s.account))
      .catch((e) => {
        if (!(e instanceof ApiError)) return; // sin red: se queda como visitante anonimo
      })
      .finally(() => alive && setReady(true));
    return () => {
      alive = false;
    };
  }, []);

  const login = useCallback(async (email, password) => applySession(await authApi.login({ email, password })), [applySession]);
  const register = useCallback(
    async (data) => applySession(await authApi.register(data)),
    [applySession]
  );
  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      setAccessToken(null);
      setAccount(null);
    }
  }, []);
  const addRole = useCallback(async (role) => applySession(await authApi.addRole(role)), [applySession]);
  const adopt = useCallback((s) => applySession(s), [applySession]);

  const value = useMemo(
    () => ({
      account,
      ready,
      isLoggedIn: !!account,
      hasRole: (r) => !!account && account.roles.includes(r),
      login,
      register,
      logout,
      addRole,
      adopt,
    }),
    [account, ready, login, register, logout, addRole, adopt]
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth debe usarse dentro de AuthProvider');
  return ctx;
}
