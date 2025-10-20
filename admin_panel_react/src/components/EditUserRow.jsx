// src/components/EditUserRow.jsx
import { useState, useEffect } from "react";
import { Check, X } from "lucide-react";
import IconTooltip from "@/components/ui/IconTooltip";

export default function EditUserRow({
    formData,
    setFormData,
    onSave,
    onCancel,
}) {
    const [errors, setErrors] = useState({});

    useEffect(() => {
        // Asegura valores por defecto al entrar en modo edición
        setFormData((prev) => ({
            nombre: prev?.nombre ?? "",
            email: prev?.email ?? "",
            rol: prev?.rol ?? "usuario",
        }));
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const validate = () => {
        const e = {};
        if (!formData?.nombre?.trim()) e.nombre = "El nombre es obligatorio";
        if (!formData?.email?.trim()) e.email = "El email es obligatorio";
        else if (!/\S+@\S+\.\S+/.test(formData.email)) e.email = "Email no válido";
        if (!formData?.rol) e.rol = "Selecciona un rol";
        setErrors(e);
        return Object.keys(e).length === 0;
    };

    const handleSave = () => {
        if (!validate()) return;
        onSave?.();
    };

    const handleKeyDown = (e) => {
        if (e.key === "Enter") handleSave();
        if (e.key === "Escape") onCancel?.();
    };

    return (
        <tr className="bg-white" onKeyDown={handleKeyDown}>
            <td className="p-2 border align-top">
                <label className="sr-only" htmlFor="edit-nombre">Nombre</label>
                <div className="space-y-1">
                    <input
                        id="edit-nombre"
                        type="text"
                        className="w-full border rounded px-2 py-1"
                        placeholder="Nombre"
                        value={formData?.nombre ?? ""}
                        onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
                        aria-invalid={!!errors.nombre}
                    />
                    {errors.nombre && (
                        <p className="text-xs text-red-600">{errors.nombre}</p>
                    )}
                </div>
            </td>

            <td className="p-2 border align-top">
                <label className="sr-only" htmlFor="edit-email">Email</label>
                <div className="space-y-1">
                    <input
                        id="edit-email"
                        type="email"
                        className="w-full border rounded px-2 py-1"
                        placeholder="correo@dominio.com"
                        value={formData?.email ?? ""}
                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                        aria-invalid={!!errors.email}
                    />
                    {errors.email && (
                        <p className="text-xs text-red-600">{errors.email}</p>
                    )}
                </div>
            </td>

            <td className="p-2 border align-top">
                <label className="sr-only" htmlFor="edit-rol">Rol</label>
                <div className="space-y-1">
                    <select
                        id="edit-rol"
                        className="w-full border rounded px-2 py-1 capitalize"
                        value={formData?.rol ?? "usuario"}
                        onChange={(e) => setFormData({ ...formData, rol: e.target.value })}
                        aria-invalid={!!errors.rol}
                    >
                        <option value="admin">admin</option>
                        <option value="soporte">soporte</option>
                        <option value="usuario">usuario</option>
                    </select>
                    {errors.rol && <p className="text-xs text-red-600">{errors.rol}</p>}
                </div>
            </td>

            <td className="p-2 border">
                <div className="flex items-center gap-2">
                    <IconTooltip label="Guardar cambios (Enter)" side="top">
                        <button
                            type="button"
                            onClick={handleSave}
                            className="p-1.5 rounded bg-green-50 hover:bg-green-100 text-green-700 focus:outline-none focus:ring-2 focus:ring-green-300"
                            aria-label="Guardar cambios"
                        >
                            <Check className="w-5 h-5" />
                        </button>
                    </IconTooltip>

                    <IconTooltip label="Cancelar (Esc)" side="top">
                        <button
                            type="button"
                            onClick={onCancel}
                            className="p-1.5 rounded bg-red-50 hover:bg-red-100 text-red-700 focus:outline-none focus:ring-2 focus:ring-red-300"
                            aria-label="Cancelar edición"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </IconTooltip>
                </div>
            </td>
        </tr>
    );
}