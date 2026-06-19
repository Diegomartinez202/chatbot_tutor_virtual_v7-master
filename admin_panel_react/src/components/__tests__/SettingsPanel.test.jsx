// admin_panel_react/src/components/__tests__/SettingsPanel.test.jsx
import React from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

// 🔧 Mocks
vi.mock("react-i18next", async () => {
    const actual = await vi.importActual("react-i18next");
    return {
        ...actual,
        useTranslation: () => ({
            t: (key, def) => def || key, // devuelve el default si lo hay
        }),
    };
});

const toastSuccessMock = vi.fn();
vi.mock("react-hot-toast", () => ({
    toast: {
        success: (...args) => toastSuccessMock(...args),
        error: vi.fn(),
    },
}));

// Si IconTooltip o i18n importan algo pesado, puedes stubearlos:
vi.mock("@/components/ui/IconTooltip", () => ({
    default: ({ children }) => <>{children}</>,
}));

// Componente bajo prueba
import SettingsPanel from "@/components/SettingsPanel";

// Helpers
const mockFetchSequence = (responses) => {
    global.fetch = vi.fn();
    responses.forEach(({ ok = true, status = 200, json }) => {
        global.fetch.mockResolvedValueOnce({
            ok,
            status,
            json: async () => (typeof json === "function" ? json() : json),
        });
    });
};

describe("SettingsPanel - toaster de 'Preferencias sincronizadas'", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
        toastSuccessMock.mockClear();
        try {
            localStorage.clear();
        } catch { }
        // URL que usa el hook/efecto
        import.meta.env.VITE_USER_SETTINGS_URL = "/api/me/settings";
    });

    it("muestra toaster tras un PUT OK al alternar el tema", async () => {
        // 1) GET inicial de /api/me/settings
        // 2) PUT con respuesta ok y prefs normalizadas (theme: dark)
        mockFetchSequence([
            {
                json: {
                    language: "es",
                    theme: "light",
                    fontScale: 1.0,
                    highContrast: false,
                },
            },
            {
                json: {
                    ok: true,
                    prefs: {
                        language: "es",
                        theme: "dark",
                        fontScale: 1.0,
                        highContrast: false,
                    },
                },
            },
        ]);

        render(
            <SettingsPanel
                open={true}
                onClose={() => { }}
                isAuthenticated={true}
                onLogout={() => { }}
                onCloseChat={() => { }}
                onLanguageChange={() => { }}
            />
        );

        // Espera a que termine el GET inicial
        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledTimes(1);
        });

        // Busca el botón de cambio de tema (el label inicial será "dark")
        const toggleBtn = await screen.findByRole("button", { name: /dark/i });
        await userEvent.click(toggleBtn);

        // Debe hacer el PUT → total 2 llamadas a fetch
        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledTimes(2);
        });

        // Verifica que se disparó el toaster
        await waitFor(() => {
            expect(toastSuccessMock).toHaveBeenCalled();
        });

        // Mensaje exacto (usa default fallback del tConfig en tu componente)
        const [toastMsg] = toastSuccessMock.mock.calls[0];
        expect(toastMsg).toMatch(/Preferencias sincronizadas/i);
    });
});
