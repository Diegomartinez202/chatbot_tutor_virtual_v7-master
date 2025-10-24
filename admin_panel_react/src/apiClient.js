// admin_panel_react/src/apiClient.js
import { API_BASE } from './envConfig';

export async function apiFetch(path, init) {
    const url = `${API_BASE}${path.startsWith('/') ? '' : '/'}${path}`;
    const res = await fetch(url, {
        credentials: 'include', // si usas cookie httpOnly de refresh
        ...init,
        headers: {
            'Content-Type': 'application/json',
            ...(init && init.headers ? init.headers : {}),
        },
    });
    if (!res.ok) {
        const text = await res.text().catch(() => '');
        throw new Error(`HTTP ${res.status}: ${text || res.statusText}`);
    }
    // si el endpoint no devuelve JSON, ajusta esto:
    try { return await res.json(); } catch { return null; }
}