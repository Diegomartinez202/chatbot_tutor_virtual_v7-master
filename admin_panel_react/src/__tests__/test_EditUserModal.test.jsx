// admin-panel-react/src/__tests__/test_EditUserModal.test.jsx
import { render, screen, fireEvent } from "@testing-library/react";
import EditUserModal from "../components/EditUserModal";

const user = {
    _id: "123",
    nombre: "Laura",
    email: "laura@test.com",
    rol: "usuario",
};

describe("🧪 EditUserModal", () => {
    it("muestra los datos del usuario", () => {
        render(<EditUserModal user={user} onUpdate={() => { }} onClose={() => { }} />);
        expect(screen.getByDisplayValue("Laura")).toBeInTheDocument();
        expect(screen.getByDisplayValue("laura@test.com")).toBeInTheDocument();
        expect(screen.getByDisplayValue("usuario")).toBeInTheDocument();
    });

    it("llama onUpdate con datos modificados", () => {
        const mockUpdate = jest.fn();
        render(<EditUserModal user={user} onUpdate={mockUpdate} onClose={() => { }} />);

        fireEvent.change(screen.getByDisplayValue("Laura"), {
            target: { value: "Laura Editada" },
        });
        fireEvent.click(screen.getByText("Guardar"));

        expect(mockUpdate).toHaveBeenCalledWith("123", {
            nombre: "Laura Editada",
            email: "laura@test.com",
            rol: "usuario",
        });
    });

    it("llama onClose correctamente", () => {
        const mockClose = jest.fn();
        render(<EditUserModal user={user} onUpdate={() => { }} onClose={mockClose} />);
        fireEvent.click(screen.getByText("Cancelar"));
        expect(mockClose).toHaveBeenCalled();
    });
});