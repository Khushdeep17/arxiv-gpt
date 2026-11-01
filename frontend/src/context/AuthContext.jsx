import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";
import {
  tokenStorage,
  loginUser,
  registerUser,
  fetchCurrentUser,
} from "../services/api";

// ----------------------------------------------------------------
// AuthContext — single source of truth for authentication state.
// ----------------------------------------------------------------
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  // null = not yet determined; {} = guest; { id, email, ... } = authenticated
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  // loading=true while we validate an existing stored token on mount
  const [loading, setLoading] = useState(true);

  // ---------------------------------------------------------------
  // On mount: if a stored token exists, validate it via GET /auth/me.
  // On failure (expired / invalid), clear credentials silently.
  // ---------------------------------------------------------------
  useEffect(() => {
    const stored = tokenStorage.get();
    if (!stored) {
      setLoading(false);
      return;
    }

    setToken(stored);

    fetchCurrentUser()
      .then((res) => {
        setUser(res.data);
      })
      .catch(() => {
        // Token invalid or expired — clear everything
        tokenStorage.clear();
        setToken(null);
        setUser(null);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  // ---------------------------------------------------------------
  // login — calls POST /auth/login, persists token, hydrates user.
  // Returns { user } on success.
  // Throws the original Axios error so callers can extract detail.
  // ---------------------------------------------------------------
  const login = useCallback(async (email, password) => {
    const res = await loginUser(email, password);
    const { access_token, user: userData } = res.data;
    tokenStorage.set(access_token);
    setToken(access_token);
    setUser(userData);
    return { user: userData };
  }, []);

  // ---------------------------------------------------------------
  // register — calls POST /auth/register, persists token, hydrates user.
  // Returns { user } on success.
  // ---------------------------------------------------------------
  const register = useCallback(async (email, password, fullName) => {
    const res = await registerUser(email, password, fullName);
    const { access_token, user: userData } = res.data;
    tokenStorage.set(access_token);
    setToken(access_token);
    setUser(userData);
    return { user: userData };
  }, []);

  // ---------------------------------------------------------------
  // logout — clears token, user, and resets auth state.
  // Callers are responsible for clearing any private UI data
  // (e.g. history) after calling this.
  // ---------------------------------------------------------------
  const logout = useCallback(() => {
    tokenStorage.clear();
    setToken(null);
    setUser(null);
  }, []);

  const isAuthenticated = Boolean(user && token);

  const value = {
    user,
    token,
    isAuthenticated,
    loading,
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// ---------------------------------------------------------------
// Convenience hook — throws if used outside AuthProvider.
// ---------------------------------------------------------------
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}

