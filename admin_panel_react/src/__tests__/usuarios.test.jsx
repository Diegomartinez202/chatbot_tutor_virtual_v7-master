import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import UserManagement from "@/pages/UserManagement";
import { fetchUsers } from "@/services/api";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

jest.mock("@/services/api", () => ({
    fetchUsers: jest.fn(),
}));

const renderWithClient = (ui) => {
    const queryClient = new QueryClient();
    return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
};

describe("👥 UserManagement", () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    test("renderiza tabla de usuarios", async () => {
        fetchUsers.mockResolvedValue([
            { _id: "1", nombre: "Daniel", email: "daniel@test.com", rol: "admin" },
        ]);

        renderWithClient(<UserManagement />);

        expect(await screen.findByText("Gestión de Usuarios")).toBeInTheDocument();
        expect(await screen.findByText("Daniel")).toBeInTheDocument();
        expect(screen.getByText("daniel@test.com")).toBeInTheDocument();
        expect(screen.getByText("admin")).toBeInTheDocument();
    });

    test("muestra mensaje si no hay usuarios", async () => {
        fetchUsers.mockResolvedValue([]);

        renderWithClient(<UserManagement />);
        expect(await screen.findByText("No se encontraron usuarios.")).toBeInTheDocument();
    });
});
