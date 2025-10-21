import { useMemo } from "react";
import jwt_decode from "jwt-decode";

export function useAuth() {
    const token = localStorage.getItem("access_token");

    const auth = useMemo(() => {
        if (!token) return { isAuthenticated: false };

        try {
            const decoded = jwt_decode(token);
            const currentTime = Date.now() / 1000;

            if (decoded.exp && decoded.exp < currentTime) {
                // Token expirado
                return { isAuthenticated: false, expired: true };
            }

            return {
                isAuthenticated: true,
                user: {
                    email: decoded.sub,
                    rol: decoded.rol,
                },
                expired: false,
                token,
            };
        } catch (error) {
            return { isAuthenticated: false };
        }
    }, [token]);

    /**
     * 🔐 Redirección al sistema SSO de Zajuna
     * Usa la URL configurada en tu .env (VITE_ZAJUNA_SSO_URL)
     */
    const redirectToZajunaSSO = () => {
        const ssoUrl = import.meta.env.VITE_ZAJUNA_SSO_URL;
        if (!ssoUrl) {
            console.error("⚠️ No se ha definido VITE_ZAJUNA_SSO_URL en el archivo .env");
            return;
        }
        window.location.href = `${ssoUrl}?redirect=${encodeURIComponent(window.location.origin)}`;
    };

    return { ...auth, redirectToZajunaSSO };
}