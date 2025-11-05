// src/context/AuthContext.jsx
import React, {
    createContext,
    useContext,
    useEffect,
    useMemo,
    useState,
} from "react";
import axiosClient, { setAuthToken } from "@/services/axiosClient"; // 👈 usa el helper central
import { STORAGE_KEYS } from "@/lib/constants";
import { registerLogout } from "@/services/authHelper";

const AuthContext = createContext({
    token: null,
    user: null,
    role: "usuario",
    loading: true,
    isAuthenticated: false,
    login: async (_t) => { },
    logout: async () => { },
    redirectToZajunaSSO: () => { },
});

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

    // 👉 un solo punto de verdad para Authorization
    useEffect(() => {
        setAuthToken(token || null);
    }, [token]);

    // 🔄 Sincroniza token entre pestañas
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
        () => async () => {
            try {
                await axiosClient.post("/auth/logout").catch(() => { });
            } finally {
                try {
                    localStorage.removeItem(STORAGE_KEYS.accessToken);
                } catch { }
                setUser(null);
                setToken(null);
                setAuthToken(null); // limpia Authorization global
            }
        },
        []
    );

    useEffect(() => {
        try {
            registerLogout?.(logout);
        } catch { }
    }, [logout]);

    // 🔍 Validar token actual
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

    // ✅ Login manual (guarda token, fija header, trae perfil, avisa al iframe)
    const login = useMemo(
        () => async (newToken) => {
            try {
                localStorage.setItem(STORAGE_KEYS.accessToken, newToken);
            } catch { }
            setToken(newToken);
            setAuthToken(newToken);

            try {
                const res = await axiosClient.get("/auth/me");
                setUser(res.data);
            } catch (err) {
                console.error("Error al obtener perfil tras login:", err);
            }

            // 🚀 Enviar token al chat embebido si está montado
            try {
                window.__zjBubble?.sendAuthToken?.(newToken);
            } catch { }
        },
        []
    );

    // ⚙️ Redirigir al SSO Zajuna
    const redirectToZajunaSSO = () => {
        const ssoUrl = import.meta.env.VITE_ZAJUNA_SSO_URL;
        if (ssoUrl) {
            const redirectUri = `${window.location.origin}/auth/callback`;
            window.location.href = `${ssoUrl}?redirect_uri=${encodeURIComponent(
                redirectUri
            )}`;
        } else {
            console.warn("⚠️ No se configuró VITE_ZAJUNA_SSO_URL");
        }
    };

    // 🔁 Token → iframe embebido
    useEffect(() => {
        if (!token) return;
        try {
            window.__zjBubble?.sendAuthToken?.(token);
        } catch { }
    }, [token]);

    const value = useMemo(
        () => ({
            token,
            user,
            role,
            loading,
            isAuthenticated,
            login,
            logout,
            redirectToZajunaSSO,
        }),
        [token, user, role, loading, isAuthenticated, login, logout]
    );

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => useContext(AuthContext);
export default AuthContext;
