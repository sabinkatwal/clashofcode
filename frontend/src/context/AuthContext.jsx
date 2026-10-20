/* eslint-disable react-refresh/only-export-components */
import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { setAuthToken } from "../api/axios";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem("clashofcode_user");
    return stored && stored !== "undefined" ? JSON.parse(stored) : null;
  });
  const [token, setToken] = useState(() => {
    const stored = localStorage.getItem("clashofcode_token");
    return stored && stored !== "undefined" ? stored : "";
  });
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const legacyDeveloperToken = token.startsWith("developer-token-") ? token : "";
    if (!legacyDeveloperToken || !user?.username) {
      return;
    }

    let cancelled = false;
    api.post("/auth/developer-login", { username: user.username })
      .then((response) => {
        if (!cancelled) {
          setAuthState(response.data);
        }
      })
      .catch(() => {
        if (!cancelled) {
          localStorage.removeItem("clashofcode_token");
          setToken("");
        }
      });

    return () => {
      cancelled = true;
    };
  }, [token, user?.username]);

  useEffect(() => {
    setAuthToken(token || null);
  }, [token]);

  // Clean up corrupted localStorage
  useEffect(() => {
    const userStored = localStorage.getItem("clashofcode_user");
    const tokenStored = localStorage.getItem("clashofcode_token");
    if (userStored === "undefined") {
      localStorage.removeItem("clashofcode_user");
    }
    if (tokenStored === "undefined") {
      localStorage.removeItem("clashofcode_token");
    }
  }, []);

  const setAuthState = useCallback((authData) => {
    const { user: authUser, access_token } = authData;
    localStorage.setItem("clashofcode_token", access_token);
    localStorage.setItem("clashofcode_user", JSON.stringify(authUser));
    setToken(access_token);
    setUser(authUser);
  }, []);

  const login = async (credentials) => {
    setLoading(true);
    try {
      const response = await api.post("/auth/login", credentials);
      setAuthState(response.data);
      navigate("/dashboard", { replace: true });
    } finally {
      setLoading(false);
    }
  };

  const developerLogin = async (username) => {
    setLoading(true);
    try {
      const response = await api.post("/auth/developer-login", { username });
      setAuthState(response.data);
      navigate("/dashboard", { replace: true });
    } finally {
      setLoading(false);
    }
  };

  const register = async (values) => {
    setLoading(true);
    try {
      const response = await api.post("/auth/register", values);
      setAuthState(response.data);
      navigate("/dashboard", { replace: true });
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem("clashofcode_token");
    localStorage.removeItem("clashofcode_user");
    setToken("");
    setUser(null);
    navigate("/login", { replace: true });
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, developerLogin, register, logout, completeLogin: setAuthState }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
