// src/state/tokenProvider.js
/**
 * Permite inyectar una función que devuelva el accessToken
 * desde Redux, Zustand, etc. Si no se define, usamos localStorage.
 */

import { STORAGE_KEYS } from "@/lib/constants";

let tokenGetter = null;

/** Configura el getter del token (se llama en el bootstrap de la app). */
export function setAccessTokenGetter(fn) {
    tokenGetter = typeof fn === "function" ? fn : null;
}

/** Obtiene el token actual desde el getter inyectado o desde localStorage. */
export function getAccessToken() {
    // 1) Preferimos el getter (Zustand/Redux)
    try {
        if (tokenGetter) {
            const t = tokenGetter();
            if (t) return t;
        }
    } catch {
        // ignorar errores del getter
    }

    // 2) localStorage con tu clave oficial
    try {
        const t = localStorage.getItem(STORAGE_KEYS.accessToken);
        if (t) return t;
    } catch {
        // no-op
    }

    // 3) Fallback legacy (compat)
    try {
        return localStorage.getItem("access_token");
    } catch {
        return null;
    }
}
