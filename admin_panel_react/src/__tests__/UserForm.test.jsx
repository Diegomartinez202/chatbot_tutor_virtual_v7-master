// ✅ Test: Componente UserForm
// 🧪 Verifica que los inputs funcionen y se pueda enviar el formulario

import { render, screen, fireEvent } from "@testing-library/react";
import UserForm from "../components/UserForm";

test("🧾 Renderiza inputs y permite envío de datos correctamente", () => {
    const mockSubmit = jest.fn();

    // 🧱 Render del componente con la función simulada
    render(<UserForm onSubmit={mockSubmit} />);

    // ✍️ Simula escritura en los campos
    fireEvent.change(screen.getByPlaceholderText("Nombre"), {
        target: { value: "Daniel" },
    });

    fireEvent.change(screen.getByPlaceholderText("Email"), {
        target: { value: "daniel@test.com" },
    });

    fireEvent.change(screen.getByPlaceholderText("Contraseña"), {
        target: { value: "12345678" },
    });

    fireEvent.change(screen.getByDisplayValue("usuario"), {
        target: { value: "admin" },
    });

    // ✅ Simula clic en "Crear"
    fireEvent.click(screen.getByText("Crear"));

    // 🧾 Asegura que los datos hayan sido enviados correctamente
    expect(mockSubmit).toHaveBeenCalledWith({
        nombre: "Daniel",
        email: "daniel@test.com",
        password: "12345678",
        rol: "admin",
    });
});
test("⚠️ Muestra alerta si falta email o contraseña y no envía datos", () => {
    const mockSubmit = jest.fn();
    window.alert = jest.fn(); // Mock del alert

    render(<UserForm onSubmit={mockSubmit} />);

    // ❌ No llenamos email ni password
    fireEvent.change(screen.getByPlaceholderText("Nombre"), {
        target: { value: "Daniel" },
    });

    fireEvent.click(screen.getByText("Crear"));

    // ❌ No debe enviar datos
    expect(mockSubmit).not.toHaveBeenCalled();

    // ✅ Debe mostrar alerta
    expect(window.alert).toHaveBeenCalledWith("Email y contraseña son obligatorios");
});
test("🧼 Limpia campos luego de enviar formulario correctamente", () => {
    const mockSubmit = jest.fn();

    render(<UserForm onSubmit={mockSubmit} />);

    fireEvent.change(screen.getByPlaceholderText("Nombre"), {
        target: { value: "Daniel" },
    });
    fireEvent.change(screen.getByPlaceholderText("Email"), {
        target: { value: "daniel@test.com" },
    });
    fireEvent.change(screen.getByPlaceholderText("Contraseña"), {
        target: { value: "12345678" },
    });

    fireEvent.click(screen.getByText("Crear"));

    expect(screen.getByPlaceholderText("Nombre").value).toBe("");
    expect(screen.getByPlaceholderText("Email").value).toBe("");
    expect(screen.getByPlaceholderText("Contraseña").value).toBe("");
});