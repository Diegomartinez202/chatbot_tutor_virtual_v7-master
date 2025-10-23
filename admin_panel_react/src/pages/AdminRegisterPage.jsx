// src/pages/admin/AdminRegisterPage.jsx
import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Input from "@/components/Input";
import IconTooltip from "@/components/ui/IconTooltip";
import { UserPlus, Mail, Lock, Shield, LogIn, KeyRound } from "lucide-react";
import { toast } from "react-hot-toast";
import { registerAdmin } from "@/services/adminApi";

export default function AdminRegisterPage() {
    const navigate = useNavigate();

    // Variables de entorno
    const canRegister = import.meta.env.MODE !== "production"; // 🚫 Desactiva en producción
    const registerKey = import.meta.env.VITE_ADMIN_REGISTER_KEY || "";
    const zajunaSSO =
        import.meta.env.VITE_ZAJUNA_SSO_URL ||
        import.meta.env.VITE_ZAJUNA_LOGIN_URL ||
        "";

    // Estado del formulario
    const [nombre, setNombre] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [password2, setPassword2] = useState("");
    const [accept, setAccept] = useState(false);
    const [accessKey, setAccessKey] = useState(""); // 🔑 clave opcional
    const [loading, setLoading] = useState(false);
    const [err, setErr] = useState("");

    const goZajuna = () => {
        if (zajunaSSO) window.location.href = zajunaSSO;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setErr("");

        if (!canRegister)
            return setErr("🚫 El registro manual está deshabilitado en producción.");

        if (registerKey && accessKey.trim() !== registerKey.trim())
            return setErr("Clave de acceso incorrecta.");

        if (!nombre.trim()) return setErr("Por favor, escribe tu nombre.");
        if (!email.trim()) return setErr("El correo es obligatorio.");
        if (!password) return setErr("La contraseña es obligatoria.");
        if (password.length < 6)
            return setErr("La contraseña debe tener al menos 6 caracteres.");
        if (password !== password2)
            return setErr("Las contraseñas no coinciden.");
        if (!accept)
            return setErr("Debes aceptar las condiciones y restricciones.");

        setLoading(true);
        try {
            await registerAdmin({ name: nombre, email, password });
            toast.success("Cuenta creada correctamente. Ahora inicia sesión.");
            navigate("/admin/login", { replace: true });
        } catch (e) {
            const msg =
                e?.response?.data?.message ||
                e?.response?.data?.error ||
                e?.message ||
                "No se pudo completar el registro.";

            if (msg.toLowerCase().includes("duplicate"))
                setErr("Ya existe un administrador con ese correo.");
            else setErr(msg);

            toast.error(msg);
        } finally {
            setLoading(false);
        }
    };

    // 🚫 Mostrar aviso si está deshabilitado en producción
    if (!canRegister) {
        return (
            <div className="min-h-[80vh] grid place-items-center p-6">
                <div className="max-w-md bg-white rounded-2xl shadow p-6 text-center">
                    <Shield className="w-10 h-10 text-indigo-600 mx-auto mb-3" />
                    <h2 className="text-xl font-semibold text-gray-800">
                        Registro Deshabilitado
                    </h2>
                    <p className="mt-2 text-gray-600 text-sm">
                        El registro manual está desactivado en el entorno de producción por
                        motivos de seguridad.
                    </p>
                    {zajunaSSO && (
                        <button
                            onClick={goZajuna}
                            className="mt-4 inline-flex items-center gap-2 rounded-lg bg-indigo-600 text-white px-5 py-2.5 text-sm font-medium hover:bg-indigo-700"
                        >
                            <LogIn className="w-4 h-4" />
                            Ingresar con Zajuna
                        </button>
                    )}
                </div>
            </div>
        );
    }

    // ✅ Formulario normal (solo si no es producción)
    return (
        <div className="min-h-[80vh] grid place-items-center p-6">
            <div className="w-full max-w-md bg-white rounded-2xl shadow p-6">
                <div className="flex items-center gap-2 mb-4">
                    <IconTooltip label="Registro Panel Administrativo" side="top">
                        <Shield className="w-6 h-6 text-indigo-600" />
                    </IconTooltip>
                    <h1 className="text-xl font-semibold">
                        Registro (Panel Administrativo)
                    </h1>
                </div>

                <form onSubmit={handleSubmit} aria-describedby="admin-register-error">
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

                    {registerKey && (
                        <Input
                            label="Clave de acceso (interna)"
                            type="password"
                            value={accessKey}
                            onChange={(e) => setAccessKey(e.target.value)}
                            placeholder="Clave interna de registro"
                            leadingIcon={<KeyRound className="w-4 h-4 text-gray-500" />}
                        />
                    )}

                    <label className="mt-2 flex items-center gap-2 text-sm text-gray-700">
                        <input
                            type="checkbox"
                            checked={accept}
                            onChange={(e) => setAccept(e.target.checked)}
                        />
                        Acepto las condiciones y restricciones.
                    </label>

                    <button
                        type="submit"
                        disabled={loading}
                        aria-busy={loading}
                        className="mt-3 w-full inline-flex items-center justify-center rounded-lg bg-indigo-600 text-white px-5 py-2.5 text-sm font-medium hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-400 disabled:opacity-60"
                    >
                        {loading ? "Registrando…" : "Registrar"}
                    </button>
                </form>

                {err && (
                    <p
                        id="admin-register-error"
                        className="text-red-600 mt-2 text-sm"
                        role="alert"
                    >
                        {err}
                    </p>
                )}

                <div className="mt-4 text-sm text-gray-600 flex items-center justify-between">
                    <Link to="/" className="hover:underline">
                        ← Volver al inicio
                    </Link>
                    <Link to="/admin/login" className="hover:underline">
                        ¿Ya estás registrado? Iniciar sesión
                    </Link>
                </div>

                {zajunaSSO && (
                    <div className="mt-4">
                        <button
                            type="button"
                            onClick={goZajuna}
                            className="w-full inline-flex items-center justify-center gap-2 rounded-lg bg-white text-gray-900 px-5 py-2.5 text-sm font-medium border hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-400"
                        >
                            <LogIn className="w-4 h-4" />
                            Registrarse con Zajuna
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}