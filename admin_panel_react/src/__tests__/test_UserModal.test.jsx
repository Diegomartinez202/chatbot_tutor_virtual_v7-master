// admin-panel-react/src/__tests__/test_UserModal.test.jsx
import { render, screen, fireEvent } from "@testing-library/react";
import UserModal from "../components/UserModal";

describe("🧪 UserModal", () => {
    it("abre y muestra el modal correctamente", () => {
        render(<UserModal onSubmit={() => { }} />);

        expect(screen.getByText("➕ Crear Usuario")).toBeInTheDocument();
        expect(screen.getByPlaceholderText("Nombre")).toBeInTheDocument();
        expect(screen.getByPlaceholderText("Email")).toBeInTheDocument();
        expect(screen.getByPlaceholderText("Contraseña")).toBeInTheDocument();
    });

    it("llama onSubmit con los datos del formulario", () => {
        const mockSubmit = jest.fn();
        render(<UserModal onSubmit={mockSubmit} />);

        fireEvent.change(screen.getByPlaceholderText("Nombre"), {
            target: { value: "Juan" },
        });
        fireEvent.change(screen.getByPlaceholderText("Email"), {
            target: { value: "juan@test.com" },
        });
        fireEvent.change(screen.getByPlaceholderText("Contraseña"), {
            target: { value: "123456" },
        });
        fireEvent.change(screen.getByRole("combobox"), {
            target: { value: "soporte" },
        });

        fireEvent.click(screen.getByText("Crear"));

        expect(mockSubmit).toHaveBeenCalledWith({
            nombre: "Juan",
            email: "juan@test.com",
            password: "123456",
            rol: "soporte",
        });
    });
});
