// admin_panel_react/src/hooks/__tests__/useUserSettings.test.jsx
import { describe, it, expect, beforeEach, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useUserSettings } from "../useUserSettings";

// Util: mock sencillo de fetch por escenario
function mockFetchOnce(responseData, { status = 200, ok = true } = {}) {
    global.fetch = vi.fn().mockResolvedValueOnce({
        ok,
        status,
        json: vi.fn().mockResolvedValue(responseData),
    });
}

// Limpieza antes de cada test
beforeEach(() => {
    vi.restoreAllMocks();
    // Evita que un token real interfiera con Authorization
    try {
        localStorage.clear();
    } catch { }
    // Default URL para el hook
    import.meta.env.VITE_USER_SETTINGS_URL = "/api/me/settings";
});

describe("useUserSettings hook", () => {
    it("autoLoad=true → hace GET y setea prefs desde el backend", async () => {
        // Respuesta GET del backend (defaults)
        mockFetchOnce({
            language: "es",
            theme: "light",
            fontScale: 1.0,
            highContrast: false,
        });

        const { result, rerender } = renderHook(() => useUserSettings({ autoLoad: true }));

        // loading true al inicio
        expect(result.current.loading).toBe(true);

        // Espera microtask queue del fetch mock
        await vi.dynamicImportSettled?.() // para happy-dom; si no existe, ignorar
        await new Promise(r => setTimeout(r, 0));

        // Re-render y asserts
        rerender();

        expect(result.current.loading).toBe(false);
        expect(result.current.error).toBe(null);
        expect(result.current.prefs).toEqual({
            language: "es",
            theme: "light",
            fontScale: 1.0,
            highContrast: false,
        });
    });

    it("save(nextPrefs) → hace PUT, normaliza prefs y las deja en state", async () => {
        // 1) GET inicial
        mockFetchOnce({
            language: "es",
            theme: "light",
            fontScale: 1.0,
            highContrast: false,
        });

        const { result } = renderHook(() => useUserSettings({ autoLoad: true }));
        await new Promise(r => setTimeout(r, 0));

        // 2) PUT de guardado
        const next = {
            language: "en",
            darkMode: true,      // se transforma en theme: "dark"
            fontScale: 1.2,
            highContrast: true,
        };

        // Respuesta PUT del backend
        global.fetch = vi.fn().mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: vi.fn().mockResolvedValue({
                ok: true,
                prefs: {
                    language: "en",
                    theme: "dark",
                    fontScale: 1.2,
                    highContrast: true,
                },
            }),
        });

        let resp;
        await act(async () => {
            resp = await result.current.save(next);
        });

        expect(resp.ok).toBe(true);
        expect(result.current.prefs).toEqual({
            language: "en",
            theme: "dark",
            fontScale: 1.2,
            highContrast: true,
        });

        // Verifica que el fetch PUT recibió Authorization si había token
        // (no hay token aquí por defecto; si quieres probarlo: setea localStorage)
        const lastCall = global.fetch.mock.calls[0];
        expect(lastCall[0]).toBe("/api/me/settings");
        expect(lastCall[1].method).toBe("PUT");
        expect(lastCall[1].headers["Content-Type"]).toBe("application/json");
    });

    it("maneja error en GET (res.ok=false)", async () => {
        global.fetch = vi.fn().mockResolvedValueOnce({
            ok: false,
            status: 500,
            json: vi.fn().mockResolvedValue({ detail: "Server error" }),
        });

        const { result } = renderHook(() => useUserSettings({ autoLoad: true }));
        await new Promise(r => setTimeout(r, 0));

        expect(result.current.loading).toBe(false);
        expect(result.current.error).toBeInstanceOf(Error);
        // Debe mantener defaults si falla el GET
        expect(result.current.prefs.language).toBe("es");
    });
});
