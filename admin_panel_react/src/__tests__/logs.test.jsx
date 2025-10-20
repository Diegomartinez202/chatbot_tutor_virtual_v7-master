import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import LogsPage from "@/pages/LogsPage";
import { getLogsList } from "@/services/api";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

jest.mock("@/services/api", () => ({
    getLogsList: jest.fn(),
}));

const renderWithClient = (ui) => {
    const queryClient = new QueryClient();
    return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
};

describe("📄 LogsPage", () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    test("renderiza tabla de logs", async () => {
        getLogsList.mockResolvedValue([
            { user_id: "anonimo", message: "Hola", sender: "user", timestamp: new Date().toISOString(), intent: "saludo" },
        ]);

        renderWithClient(<LogsPage />);

        expect(await screen.findByText("Tabla de logs")).toBeInTheDocument();
        expect(await screen.findByText("Hola")).toBeInTheDocument();
        expect(screen.getByText("anonimo")).toBeInTheDocument();
        expect(screen.getByText("saludo")).toBeInTheDocument();
    });

    test("muestra mensaje si no hay logs", async () => {
        getLogsList.mockResolvedValue([]);

        renderWithClient(<LogsPage />);
        expect(await screen.findByText("No se encontraron logs.")).toBeInTheDocument();
    });
});