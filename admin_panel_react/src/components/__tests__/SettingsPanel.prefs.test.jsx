// admin_panel_react/src/components/__tests__/SettingsPanel.prefs.test.jsx
import React from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

// 🔧 Mocks i18n: devuelve el default si se pasa, o la key
vi.mock("react-i18next", async () => {
    const actual = await vi.importActual("react-i18next");
    return {
        ...actual,
        useTranslation: () => ({
            t: (key, def) => def || key,
        }),
    };
});

// 🔧 Mock IconTooltip para simplificar DOM
vi.mock("@/components/ui/IconTooltip", () => ({
    default: ({ children }) => <>{children}</>,
}));

// 🔧 Mock toaster
const toastSuccessMock = vi.fn();
vi.mock("react-hot-toast", () => ({
    toast: {
        success: (...args) => toastSuccessMock(...args),
        error: vi.fn(),
    },
}));

import SettingsPanel from "@/components/SettingsPanel";

// Helper para encadenar mocks de fetch (GET, PUT)
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

describe("SettingsPanel - idioma y alto contraste → PUT OK → toaster", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
        toastSuccessMock.mockClear();
        try {
            localStorage.clear();
        } catch { }
        import.meta.env.VITE_USER_SETTINGS_URL = "/api/me/settings";
    });

    it("cambia idioma a 'en' y muestra toaster tras PUT OK", async () => {
        vi.useFakeTimers();

        // 1) GET inicial
        // 2) PUT con language=en
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
                        language: "en",
                        theme: "light",
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

        // Espera GET
        await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1));

        // El <select> tiene aria-label={tConfig("language")} → mock devuelve "language"
        const languageSelect = await screen.findByRole("combobox", { name: /language/i });
        await userEvent.selectOptions(languageSelect, "en");

        // Debe realizar PUT (segunda llamada)
        await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(2));

        // Avanza el debounce del toaster (450ms en el componente)
        vi.runAllTimers();

        // Verifica toaster
        await waitFor(() => expect(toastSuccessMock).toHaveBeenCalled());
        const [msg] = toastSuccessMock.mock.calls[0];
        expect(msg).toMatch(/Preferencias sincronizadas/i);

        vi.useRealTimers();
    });

    it("activa Alto Contraste y muestra toaster tras PUT OK", async () => {
        vi.useFakeTimers();

        // 1) GET inicial
        // 2) PUT con highContrast=true
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
                        theme: "light",
                        fontScale: 1.0,
                        highContrast: true,
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

        // Espera GET
        await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1));

        // El checkbox tiene aria-label={tConfig("high_contrast", "Alto contraste")}
        const hcCheckbox = await screen.findByRole("checkbox", { name: /alto contraste/i });
        await userEvent.click(hcCheckbox);

        // Debe realizar PUT (segunda llamada)
        await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(2));

        // Avanza el debounce del toaster
        vi.runAllTimers();

        // Verifica toaster
        await waitFor(() => expect(toastSuccessMock).toHaveBeenCalled());
        const [msg] = toastSuccessMock.mock.calls[0];
        expect(msg).toMatch(/Preferencias sincronizadas/i);

        vi.useRealTimers();
    });
});
