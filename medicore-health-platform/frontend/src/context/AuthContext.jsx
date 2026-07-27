import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { api, decodeToken, setTokens, clearTokens } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null); // { id, role, email, full_name }
  const [loading, setLoading] = useState(true);

  const hydrate = useCallback(async () => {
    const token = localStorage.getItem("medicore_access_token");
    if (!token) {
      setLoading(false);
      return;
    }
    try {
      const me = await api.get("/auth/me");
      const claims = decodeToken(token);
      setUser({ ...me, role: claims?.role || me.role });
    } catch {
      clearTokens();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  const login = async (email, password, mfa_code) => {
    const tokens = await api.post("/auth/login", { email, password, mfa_code });
    setTokens(tokens);
    const me = await api.get("/auth/me");
    const claims = decodeToken(tokens.access_token);
    setUser({ ...me, role: claims?.role || me.role });
    return me;
  };

  const register = async (payload) => {
    return api.post("/auth/register", payload);
  };

  const logout = async () => {
    const refresh_token = localStorage.getItem("medicore_refresh_token");
    try {
      if (refresh_token) await api.post("/auth/logout", { refresh_token });
    } catch {
      /* best-effort */
    }
    clearTokens();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser: hydrate }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
