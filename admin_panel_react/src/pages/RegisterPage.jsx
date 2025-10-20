// src/pages/RegisterPage.jsx
import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Input from "@/components/Input";
import IconTooltip from "@/components/ui/IconTooltip";
import { UserPlus, Mail, Lock } from "lucide-react";
import { toast } from "react-hot-toast";

// ✅ Import corregido: usamos el alias `register` definido en authApi.js
import { register as apiRegister } from "@/services/authApi";

export default function RegisterPage() {
    const navigate = useNavigate();

    const [nombre, setNombre] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [password2, setPassword2] = useState("");

    const [loading, setLoading] = useState(false);
    const [err, setErr] = useState("");

    const handleSubmit = async (e) => {
        e.preventDefault();
        setErr("");

        if (!nombre.trim()) return setErr("Por favor, escribe tu nombre.");
        if (!email.trim()) return setErr("El correo es obligatorio.");
        if (!password) return setErr("La contraseña es obligatoria.");
        if (password.length < 6) return setErr("La contraseña debe tener al menos 6 caracteres.");
        if (password !== password2) return setErr("Las contraseñas no coinciden.");

        setLoading(true);
        try {
            // 🔹 Se llama al alias `apiRegister` (que apunta a registerAdmin)
            await apiRegister({
                name: nombre,
                email,
                password,
            });

            toast.success("Cuenta creada. Inicia sesión para continuar.");
            navigate("/login", { replace: true });
        } catch (e2) {
            const msg =
                e2?.response?.data?.message ||
                e2?.response?.data?.error ||
                e2?.message ||
                "No se pudo completar el registro.";
            setErr(msg);
            toast.error(msg);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-[80vh] grid place-items-center p-6">
            <div className="w-full max-w-md bg-white rounded-2xl shadow p-6">
                <div className="flex items-center gap-2 mb-4">
                    <IconTooltip label="Crear cuenta" side="top">
                        <UserPlus className="w-6 h-6 text-indigo-600" />
                    </IconTooltip>
                    <h1 className="text-xl font-semibold">Crear cuenta</h1>
                </div>

                <form onSubmit={handleSubmit} aria-describedby="register-error">
                    <Input
                        label="Nombre"
                        value={nombre}
                        onChange={(e) => setNombre(e.target.value)}
                        placeholder="Tu nombre"
                        name="name"
                        required
                    />

                    <Input
                        label="Email"
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="correo@ejemplo.com"
                        name="email"
                        required
                        leadingIcon={<Mail className="w-4 h-4 text-gray-500" />}
                    />

                    <Input
                        label="Contraseña"
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        name="password"
                        required
                        placeholder="••••••••"
                        leadingIcon={<Lock className="w-4 h-4 text-gray-500" />}
                    />

                    <Input
                        label="Confirmar contraseña"
                        type="password"
                        value={password2}
                        onChange={(e) => setPassword2(e.target.value)}
                        name="password_confirm"
                        required
                        placeholder="••••••••"
                        leadingIcon={<Lock className="w-4 h-4 text-gray-500" />}
                    />

                    <button
                        type="submit"
                        disabled={loading}
                        aria-busy={loading}
                        className="mt-2 w-full inline-flex items-center justify-center rounded-lg bg-indigo-600 text-white px-5 py-2.5 text-sm font-medium hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-400 disabled:opacity-60"
                    >
                        {loading ? "Creando…" : "Crear cuenta"}
                    </button>
                </form>

                {err && (
                    <p id="register-error" className="text-red-600 mt-2" role="alert">
                        {err}
                    </p>
                )}

                <div className="mt-4 text-sm text-gray-600 flex items-center justify-between">
                    <Link to="/" className="hover:underline">
                        ← Volver al inicio
                    </Link>
                    <Link to="/login" className="hover:underline">
                        ¿Ya tienes cuenta? Inicia sesión
                    </Link>
                </div>
            </div>
        </div>
    );
}