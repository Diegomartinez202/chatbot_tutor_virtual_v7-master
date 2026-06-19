// src/components/EditUserModal.jsx
import { useState, useEffect, useCallback } from "react";
import { X, Pencil, Loader2, Check } from "lucide-react";
import IconTooltip from "@/components/ui/IconTooltip";
import { Button } from "@/components/ui/button";

const EditUserModal = ({ user, onUpdate, onClose }) => {
    const [formData, setFormData] = useState({
        nombre: "",
        email: "",
        rol: "usuario",
    });
    const [errors, setErrors] = useState({});
    const [saving, setSaving] = useState(false);

    const userId = user?._id || user?.id; // compat

    useEffect(() => {
        if (user) {
            setFormData({
                nombre: user.nombre || "",
                email: user.email || "",
                rol: user.rol || "usuario",
            });
        }
    }, [user]);

    const validate = () => {
        const e = {};
        if (!formData.nombre.trim()) e.nombre = "El nombre es obligatorio";
        if (!formData.email.trim()) e.email = "El email es obligatorio";
        else if (!/\S+@\S+\.\S+/.test(formData.email)) e.email = "Email no válido";
        if (!formData.rol) e.rol = "Selecciona un rol";
        setErrors(e);
        return Object.keys(e).length === 0;
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData((prev) => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!validate() || !userId) return;
        try {
            setSaving(true);
            await onUpdate(userId, formData);
            onClose?.();
        } finally {
            setSaving(false);
        }
    };

    const handleKeyDown = useCallback(
        (e) => {
            if (e.key === "Escape") onClose?.();
        },
        [onClose]
    );

    useEffect(() => {
        document.addEventListener("keydown", handleKeyDown);
        return () => document.removeEventListener("keydown", handleKeyDown);
    }, [handleKeyDown]);

    const handleBackdrop = (e) => {
        if (e.target === e.currentTarget) onClose?.();
    };

    return (
        <div
            className="fixed inset-0 flex items-center justify-center bg-black/50 z-50"
            onMouseDown={handleBackdrop}
        >
            <div
                className="bg-white p-6 rounded shadow-md w-full max-w-md relative"
                role="dialog"
                aria-modal="true"
                aria-labelledby="edit-user-title"
                onMouseDown={(e) => e.stopPropagation()} // evita cerrar al click dentro
            >
                <IconTooltip label="Cerrar" side="left">
                    <button
                        onClick={onClose}
                        className="absolute top-2 right-2 text-red-500 p-1 rounded hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-300"
                        aria-label="Cerrar modal"
                        type="button"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </IconTooltip>

                <h2
                    id="edit-user-title"
                    className="text-xl font-bold mb-4 flex items-center gap-2"
                >
                    <IconTooltip label="Editar usuario" side="top">
                        <Pencil className="w-5 h-5 text-gray-700" />
                    </IconTooltip>
                    Editar Usuario
                </h2>

                <form onSubmit={handleSubmit} noValidate>
                    <div className="space-y-3">
                        <div>
                            <label htmlFor="eu-nombre" className="text-sm font-medium">
                                Nombre
                            </label>
                            <input
                                id="eu-nombre"
                                name="nombre"
                                type="text"
                                className="mt-1 w-full border rounded px-3 py-2"
                                placeholder="Nombre"
                                value={formData.nombre}
                                onChange={handleChange}
                                required
                                autoFocus
                                aria-invalid={errors.nombre ? "true" : "false"}
                                aria-describedby={errors.nombre ? "eu-nombre-err" : undefined}
                            />
                            {errors.nombre && (
                                <p id="eu-nombre-err" className="text-xs text-red-600 mt-1">
                                    {errors.nombre}
                                </p>
                            )}
                        </div>

                        <div>
                            <label htmlFor="eu-email" className="text-sm font-medium">
                                Email
                            </label>
                            <input
                                id="eu-email"
                                name="email"
                                type="email"
                                className="mt-1 w-full border rounded px-3 py-2"
                                placeholder="correo@dominio.com"
                                value={formData.email}
                                onChange={handleChange}
                                required
                                autoComplete="email"
                                aria-invalid={errors.email ? "true" : "false"}
                                aria-describedby={errors.email ? "eu-email-err" : undefined}
                            />
                            {errors.email && (
                                <p id="eu-email-err" className="text-xs text-red-600 mt-1">
                                    {errors.email}
                                </p>
                            )}
                        </div>

                        <div>
                            <label htmlFor="eu-rol" className="text-sm font-medium">
                                Rol
                            </label>
                            <select
                                id="eu-rol"
                                name="rol"
                                className="mt-1 w-full border rounded px-3 py-2 capitalize bg-white"
                                value={formData.rol}
                                onChange={handleChange}
                                required
                                aria-invalid={errors.rol ? "true" : "false"}
                                aria-describedby={errors.rol ? "eu-rol-err" : undefined}
                            >
                                <option value="admin">admin</option>
                                <option value="soporte">soporte</option>
                                <option value="usuario">usuario</option>
                            </select>
                            {errors.rol && (
                                <p id="eu-rol-err" className="text-xs text-red-600 mt-1">
                                    {errors.rol}
                                </p>
                            )}
                        </div>
                    </div>

                    <div className="mt-4 flex gap-2">
                        <Button
                            type="submit"
                            disabled={saving}
                            className="inline-flex items-center gap-2"
                        >
                            {saving ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    Guardando…
                                </>
                            ) : (
                                <>
                                    <Check className="w-4 h-4" />
                                    Guardar cambios
                                </>
                            )}
                        </Button>

                        <Button
                            type="button"
                            variant="outline"
                            onClick={onClose}
                            disabled={saving}
                        >
                            Cancelar
                        </Button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default EditUserModal;