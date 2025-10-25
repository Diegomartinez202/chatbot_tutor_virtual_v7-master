// src/state/tokenProvider.js
/**
 * Permite inyectar una función que devuelva el accessToken
 * desde Redux, Zustand, etc. Si no se define, usamos localStorage.
 */

let tokenGetter = null;

/** Configura el getter del token (se llama en el bootstrap de la app). */
export function setAccessTokenGetter(fn) {
    tokenGetter = typeof fn === "function" ? fn : null;
}

/** Obtiene el token actual desde el getter inyectado o desde localStorage. */
export function getAccessToken() {
    try {
        if (tokenGetter) {
            const t = tokenGetter();
            if (t) return t;
        }
    } catch {
        // ignorar errores del getter
    }
    try {
        return localStorage.getItem("access_token"); // fallback legacy
    } catch {
        return null;
    }
}