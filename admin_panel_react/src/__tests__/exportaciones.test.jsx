import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ExportacionesPage from "@/pages/ExportacionesPage";
import { exportarCSV, fetchHistorialExportaciones } from "@/services/api";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// ✅ Mock de API
jest.mock("@/services/api", () => ({
    exportarCSV: jest.fn(),
    fetchHistorialExportaciones: jest.fn(),
}));

// 🧪 Helper para renderizar con React Query
const renderWithClient = (ui) => {
    const queryClient = new QueryClient();
    return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
};

describe("📤 ExportacionesPage", () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    test("renderiza correctamente la tabla y exporta CSV", async () => {
        // 🟢 Mock del historial
        fetchHistorialExportaciones.mockResolvedValue([
            {
                nombre_archivo: "logs_2025.csv",
                tipo: "conversaciones",
                timestamp: new Date().toISOString(),
                email: "admin@test.com",
                url: "https://example.com/logs_2025.csv",
            },
        ]);

        // 🟢 Mock de exportación
        exportarCSV.mockResolvedValue({ url: "https://example.com/export.csv" });

        renderWithClient(<ExportacionesPage />);

        // Espera a que se muestre el título
        expect(await screen.findByText("Exportaciones realizadas")).toBeInTheDocument();

        // Simula clic en botón Exportar
        const exportBtn = screen.getByText(/Exportar CSV/i);
        fireEvent.click(exportBtn);

        // Verifica que se llamó a exportarCSV
        await waitFor(() => {
            expect(exportarCSV).toHaveBeenCalled();
        });

        // Verifica contenido en la tabla
        expect(await screen.findByText("logs_2025.csv")).toBeInTheDocument();
        expect(screen.getByText("admin@test.com")).toBeInTheDocument();
        expect(screen.getByText("Descargar")).toBeInTheDocument();
    });

    test("muestra mensaje si no hay exportaciones", async () => {
        fetchHistorialExportaciones.mockResolvedValue([]);

        renderWithClient(<ExportacionesPage />);
        expect(await screen.findByText("No se encontraron exportaciones.")).toBeInTheDocument();
    });
});