// src/services/tokenStorage.js
// Almacén robusto para tokens en memoria + localStorage (varios nombres por compatibilidad)

const KEYS = [
    "auth_token",
    "access_token",
    "token",
    "jwt",
];

let memoryToken = null;

export function getToken() {
    if (memoryToken) return memoryToken;

    for (const k of KEYS) {
        const v = localStorage.getItem(k);
        if (v) {
            memoryToken = v;
            return v;
        }
    }
    return null;
}

export function setToken(token) {
    memoryToken = token || null;
    if (!token) {
        clearToken();
        return;
    }
    // Clave “oficial”
    localStorage.setItem("auth_token", token);
    // Espejos por compatibilidad
    localStorage.setItem("access_token", token);
}

export function clearToken() {
    memoryToken = null;
    for (const k of KEYS) {
        try { localStorage.removeItem(k); } catch { }
    }
}

export function getRefreshToken() {
    // Si manejas refresh_token, guárdalo aquí:
    //  - localStorage.setItem("refresh_token", x)
    try {
        return localStorage.getItem("refresh_token");
    } catch {
        return null;
    }
}

export function setRefreshToken(refreshToken) {
    if (!refreshToken) {
        try { localStorage.removeItem("refresh_token"); } catch { }
        return;
    }
    localStorage.setItem("refresh_token", refreshToken);
}
