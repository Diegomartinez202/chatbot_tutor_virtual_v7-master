// src/components/UserForm.jsx
import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import IconTooltip from "@/components/ui/IconTooltip";
import { toast } from "react-hot-toast";
import { UserPlus, User, Mail, Lock, Shield, Info, Loader2 } from "lucide-react";

const UserForm = ({ onSubmit }) => {
    const [formData, setFormData] = useState({
        nombre: "",
        email: "",
        password: "",
        rol: "usuario",
    });
    const [submitting, setSubmitting] = useState(false);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData((prev) => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!formData.email || !formData.password) {
            toast.error("Email y contraseña son obligatorios");
            return;
        }

        try {
            setSubmitting(true);
            // onSubmit puede ser sync o async
            await Promise.resolve(onSubmit?.(formData));
            toast.success("Usuario creado correctamente");
            setFormData({ nombre: "", email: "", password: "", rol: "usuario" });
        } catch (err) {
            console.error(err);
            toast.error("No se pudo crear el usuario");
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <form
            onSubmit={handleSubmit}
            className="mb-6 p-4 border rounded bg-green-100"
            aria-labelledby="crear-usuario-title"
        >
            <div className="flex items-center gap-2 mb-3">
                <UserPlus className="w-5 h-5 text-gray-700" aria-hidden="true" />
                <h3 id="crear-usuario-title" className="font-semibold">
                    Crear Nuevo Usuario
                </h3>
                <IconTooltip label="Completa los datos y asigna un rol. Email y contraseña son obligatorios.">
                    <Info className="w-3.5 h-3.5 text-gray-600" aria-hidden="true" />
                </IconTooltip>
            </div>

            <div className="flex flex-wrap items-center gap-2">
                {/* Nombre */}
                <div className="flex items-center gap-2">
                    <IconTooltip label="Nombre completo (opcional)">
                        <User className="w-4 h-4 text-gray-600" aria-hidden="true" />
                    </IconTooltip>
                    <label htmlFor="uf-nombre" className="sr-only">
                        Nombre
                    </label>
                    <input
                        id="uf-nombre"
                        className="border px-2 py-1 rounded"
                        name="nombre"
                        value={formData.nombre}
                        onChange={handleChange}
                        placeholder="Nombre"
                        type="text"
                        autoComplete="name"
                    />
                </div>

                {/* Email */}
                <div className="flex items-center gap-2">
                    <IconTooltip label="Correo electrónico (obligatorio)">
                        <Mail className="w-4 h-4 text-gray-600" aria-hidden="true" />
                    </IconTooltip>
                    <label htmlFor="uf-email" className="sr-only">
                        Email
                    </label>
                    <input
                        id="uf-email"
                        className="border px-2 py-1 rounded"
                        name="email"
                        value={formData.email}
                        onChange={handleChange}
                        placeholder="Email"
                        type="email"
                        required
                        autoComplete="email"
                    />
                </div>

                {/* Password */}
                <div className="flex items-center gap-2">
                    <IconTooltip label="Contraseña (obligatoria)">
                        <Lock className="w-4 h-4 text-gray-600" aria-hidden="true" />
                    </IconTooltip>
                    <label htmlFor="uf-password" className="sr-only">
                        Contraseña
                    </label>
                    <input
                        id="uf-password"
                        className="border px-2 py-1 rounded"
                        name="password"
                        value={formData.password}
                        onChange={handleChange}
                        placeholder="Contraseña"
                        type="password"
                        required
                        autoComplete="new-password"
                    />
                </div>

                {/* Rol */}
                <div className="flex items-center gap-2">
                    <IconTooltip label="Rol del usuario (permisos)">
                        <Shield className="w-4 h-4 text-gray-600" aria-hidden="true" />
                    </IconTooltip>
                    <label htmlFor="uf-rol" className="sr-only">
                        Rol
                    </label>
                    <select
                        id="uf-rol"
                        className="border px-2 py-1 rounded"
                        name="rol"
                        value={formData.rol}
                        onChange={handleChange}
                    >
                        <option value="admin">Admin</option>
                        <option value="soporte">Soporte</option>
                        <option value="usuario">Usuario</option>
                    </select>
                </div>

                {/* Submit */}
                <div className="ml-auto">
                    <IconTooltip label={submitting ? "Creando…" : "Crear usuario"}>
                        <span>
                            <Button
                                type="submit"
                                disabled={submitting}
                                className="inline-flex items-center gap-2"
                                aria-label="Crear usuario"
                            >
                                {submitting ? (
                                    <>
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                        Creando…
                                    </>
                                ) : (
                                    <>
                                        <UserPlus className="w-4 h-4" />
                                        Crear
                                    </>
                                )}
                            </Button>
                        </span>
                    </IconTooltip>
                </div>
            </div>
        </form>
    );
};

export default UserForm;