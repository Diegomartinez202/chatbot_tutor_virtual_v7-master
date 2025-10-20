// src/services/authHelper.js

/**
 * Registro global opcional de una función de logout.
 * Úsalo desde tu AuthContext: registerLogout(logout)
 */

let _logout = null;

/**
 * Registra la función de logout global (por ejemplo, desde AuthContext).
 * Si pasas algo no-función, limpia el registro.
 */
export function registerLogout(fn) {
    _logout = typeof fn === "function" ? fn : null;
}

/** Devuelve la función de logout registrada (o null si no hay). */
export function getLogout() {
    return _logout;
}

/**
 * Dispara el logout registrado (si existe). Ignora errores para no romper UI.
 * Puedes pasar argumentos si tu logout los acepta.
 */
export async function triggerLogout(...args) {
    if (typeof _logout === "function") {
        try {
            return await _logout(...args);
        } catch {
            // Silenciar errores de logout para evitar loops/ruidos en UI
        }
    }
    return undefined;
}

/** Limpia el logout registrado. */
export function clearLogout() {
    _logout = null;
}

/**
 * Compatibilidad hacia atrás con implementaciones antiguas.
 * Ejemplo: const { logout } = getAuthHelper(); logout?.();
 */
export function getAuthHelper() {
    return { logout: _logout };
}