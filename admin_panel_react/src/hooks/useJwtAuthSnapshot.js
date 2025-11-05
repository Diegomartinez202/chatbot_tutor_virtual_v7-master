import { useMemo } from "react";
import { jwtDecode } from "jwt-decode"; // 👈 named import (NO default)

export function useJwtAuthSnapshot() {
    let token = null;
    try {
        token = localStorage.getItem("accessToken") || localStorage.getItem("access_token") || null;
    } catch {
        token = null;
    }

    const auth = useMemo(() => {
        if (!token) return { isAuthenticated: false, user: null, expired: false, token: null };

        try {
            const decoded = jwtDecode(token);
            const now = Math.floor(Date.now() / 1000);

            if (decoded?.exp && decoded.exp < now) {
                return { isAuthenticated: false, user: null, expired: true, token: null };
            }

            const email = decoded?.email || decoded?.sub || null;
            const rol =
                decoded?.rol || decoded?.role || decoded?.roles?.[0] || decoded?.authorities?.[0] || "usuario";

            return {
                isAuthenticated: true,
                user: { email, rol },
                expired: false,
                token,
            };
        } catch {
            return { isAuthenticated: false, user: null, expired: false, token: null };
        }
    }, [token]);

    return auth;
}

export default useJwtAuthSnapshot;
