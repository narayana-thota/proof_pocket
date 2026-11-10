
import {
  createContext,
  useContext,
  useEffect,
  useState,
} from "react";

import api from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const saveTokens = (accessToken, refreshToken) => {
    localStorage.setItem("access_token", accessToken);

    if (refreshToken) {
      localStorage.setItem("refresh_token", refreshToken);
    }
  };

  const clearSession = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUser(null);
  };

  const fetchCurrentUser = async () => {
    const response = await api.get("/api/auth/me");
    setUser(response.data.user);
    return response.data.user;
  };

  const refreshAccessToken = async () => {
    const refreshToken = localStorage.getItem("refresh_token");

    if (!refreshToken) {
      throw new Error("No refresh token available.");
    }

    const response = await api.post("/api/auth/refresh", {
      refresh_token: refreshToken,
    });

    localStorage.setItem(
      "access_token",
      response.data.access_token
    );

    return response.data.access_token;
  };

  const login = async (email, password) => {
    const response = await api.post("/api/auth/login", {
      email,
      password,
    });

    saveTokens(
      response.data.access_token,
      response.data.refresh_token
    );

    setUser(response.data.user);

    return response.data.user;
  };

  const register = async (fullName, email, password) => {
    const response = await api.post("/api/auth/register", {
      full_name: fullName,
      email,
      password,
    });

    return response.data;
  };

  const logout = async () => {
    const refreshToken = localStorage.getItem("refresh_token");

    try {
      if (refreshToken) {
        await api.post("/api/auth/logout", {
          refresh_token: refreshToken,
        });
      }
    } finally {
      clearSession();
    }
  };

  useEffect(() => {
    const initializeAuth = async () => {
      const accessToken = localStorage.getItem("access_token");
      const refreshToken = localStorage.getItem("refresh_token");

      if (!accessToken && !refreshToken) {
        setLoading(false);
        return;
      }

      try {
        if (accessToken) {
          await fetchCurrentUser();
        } else {
          await refreshAccessToken();
          await fetchCurrentUser();
        }
      } catch {
        try {
          if (!refreshToken) {
            throw new Error("No refresh token.");
          }

          await refreshAccessToken();
          await fetchCurrentUser();
        } catch {
          clearSession();
        }
      } finally {
        setLoading(false);
      }
    };

    initializeAuth();
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider.");
  }

  return context;
}
