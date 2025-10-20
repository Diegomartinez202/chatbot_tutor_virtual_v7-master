// src/context/AuthContext.jsx
import React, {
    createContext,
    useContext,
    useEffect,
    useMemo,
    useState,
} from "react";
import axiosClient from "@/services/axiosClient";
import { STORAGE_KEYS } from "@/lib/constants";
import { registerLogout } from "@/services/authHelper"; // stub más abajo

const AuthContext = createContext({
    token: null,
    user: null,
    role: "usuario",
    loading: true,
    isAuthenticated: false,
    login: async (_t) => { },
    logout: async () => { },
});

function setAxiosAuthHeader(token) {
    try {
        if (token) {
            axiosClient.defaults.headers.common.Authorization = `Bearer ${token}`;
        } else {
            delete axiosClient.defaults.headers.common.Authorization;
        }
    } catch { }
}

export const AuthProvider = ({ children }) => {
    const [token, setToken] = useState(() => {
        try {
            return localStorage.getItem(STORAGE_KEYS.accessToken) || null;
        } catch {
            return null;
        }
    });
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    const role = user?.rol || user?.role || "usuario";
    const isAuthenticated = Boolean(token && user);

    useEffect(() => {
        setAxiosAuthHeader(token);
    }, [token]);

    useEffect(() => {
        const onStorage = (e) => {
            if (e.key === STORAGE_KEYS.accessToken) {
                setToken(e.newValue || null);
            }
        };
        window.addEventListener("storage", onStorage);
        return () => window.removeEventListener("storage", onStorage);
    }, []);

    const logout = useMemo(
        () =>
            async () => {
                try {
                    await axiosClient.post("/auth/logout").catch(() => { });
                } finally {
                    try {
                        localStorage.removeItem(STORAGE_KEYS.accessToken);
                    } catch { }
                    setUser(null);
                    setToken(null);
                    setAxiosAuthHeader(null);
                }
            },
        []
    );

    useEffect(() => {
        try {
            registerLogout?.(logout);
        } catch { }
    }, [logout]);

    useEffect(() => {
        let alive = true;
        (async () => {
            if (!token) {
                setLoading(false);
                return;
            }
            setLoading(true);
            try {
                const res = await axiosClient.get("/auth/me");
                if (!alive) return;
                setUser(res.data);
            } catch (err) {
                console.error("Token inválido o error en /auth/me:", err);
                if (!alive) return;
                await logout();
            } finally {
                if (alive) setLoading(false);
            }
        })();
        return () => {
            alive = false;
        };
    }, [token, logout]);

    const login = useMemo(
        () =>
            async (newToken) => {
                try {
                    localStorage.setItem(STORAGE_KEYS.accessToken, newToken);
                } catch { }
                setToken(newToken);
                try {
                    const res = await axiosClient.get("/auth/me");
                    setUser(res.data);
                } catch (err) {
                    console.error("Error al obtener perfil tras login:", err);
                }
            },
        []
    );

    const value = useMemo(
        () => ({
            token,
            user,
            role,
            loading,
            isAuthenticated,
            login,
            logout,
        }),
        [token, user, role, loading, isAuthenticated, login, logout]
    );

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => useContext(AuthContext);
export default AuthContext;