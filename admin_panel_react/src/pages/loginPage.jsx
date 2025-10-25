// src/pages/LoginPage.jsx
import { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import Input from "@/components/Input";
import IconTooltip from "@/components/ui/IconTooltip";
import { Lock } from "lucide-react";

import { useAuth } from "@/context/AuthContext";
import { login as apiLogin, me as apiMe } from "@/services/authApi";

// Flags de entorno
const ENABLE_LOCAL = String(import.meta.env.VITE_ENABLE_LOCAL_LOGIN) === "true";
const ZAJUNA_SSO = import.meta.env.VITE_ZAJUNA_SSO_URL || "";
const SHOW_GUEST = String(import.meta.env.VITE_SHOW_GUEST ?? "true") !== "false";

function LoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const navigate = useNavigate();
    const { login, redirectToZajunaSSO } = useAuth(); // ✅ Integrado correctamente

    useEffect(() => {
        document.title = "Iniciar sesión – Chatbot";
    }, []);

    // —— LOGIN LOCAL (si está habilitado) ——
    const handleLogin = async (e) => {
        e.preventDefault();
        if (!ENABLE_LOCAL) return;
        setLoading(true);
        setError("");

        try {
            // 👉 Centralizado: apiLogin usa axiosClient (baseURL=/api) internamente
            const { token } = await apiLogin({ email, password });
            await login(token);

            let role = "usuario";
            try {
                // 👉 Centralizado: apiMe usa axiosClient (Authorization auto)
                const profile = await apiMe();
                role = profile?.rol || profile?.role || "usuario";
            } catch { /* perfil opcional */ }

            if (role === "admin" || role === "soporte") navigate("/dashboard", { replace: true });
            else navigate("/chat", { replace: true });
        } catch (err) {
            setError(
                err?.response?.data?.message ||
                err?.message ||
                "Error de red, intenta nuevamente."
            );
        } finally {
            setLoading(false);
        }
    };

    // —— SSO Zajuna (ya integrado) ——
    const handleZajuna = () => {
        try {
            if (typeof redirectToZajunaSSO === "function") {
                redirectToZajunaSSO(); // ✅ inicia flujo federado
            } else if (ZAJUNA_SSO) {
                window.location.href = ZAJUNA_SSO; // fallback directo
            } else {
                setError("No se configuró la URL del proveedor SSO.");
            }
        } catch (err) {
            console.error("Error al redirigir al SSO:", err);
            setError("Error al conectar con el servicio de autenticación.");
        }
    };

    const handleGuest = () => navigate("/chat");

    return (
        <div className="p-6 max-w-md mx-auto">
            <div className="flex items-center gap-2 mb-4">
                <IconTooltip label="Iniciar sesión" side="top">
                    <Lock className="w-6 h-6 text-gray-700" aria-hidden="true" />
                </IconTooltip>
                <h2 className="text-xl font-semibold" id="login-title">
                    Iniciar sesión
                </h2>
            </div>

            {/* —— SSO de Zajuna (principal) —— */}
            {ZAJUNA_SSO ? (
                <div className="flex flex-col gap-3" aria-labelledby="login-title">
                    <button
                        type="button"
                        onClick={handleZajuna}
                        disabled={loading}
                        data-testid="login-zajuna"
                        className="inline-flex items-center justify-center rounded-lg bg-indigo-600 text-white px-5 py-2.5 text-sm font-medium hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-400 disabled:opacity-60"
                    >
                        Ingresar con Zajuna
                    </button>

                    {SHOW_GUEST && (
                        <button
                            type="button"
                            onClick={handleGuest}
                            disabled={loading}
                            data-testid="login-guest"
                            className="inline-flex items-center justify-center rounded-lg bg-transparent text-gray-900 px-5 py-2.5 text-sm font-medium hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-300"
                        >
                            Entrar como invitado (sin registro)
                        </button>
                    )}
                </div>
            ) : (
                <p className="text-sm text-gray-600">
                    Configura <code>VITE_ZAJUNA_SSO_URL</code> en tu <code>.env</code> para habilitar el acceso
                    SSO de Zajuna.
                </p>
            )}

            {/* —— Formulario local (opcional) —— */}
            {ENABLE_LOCAL && (
                <>
                    <div className="my-4 h-px bg-gray-200" role="separator" />
                    <form onSubmit={handleLogin} aria-describedby="login-error" noValidate>
                        <Input
                            label="Email"
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                            autoComplete="username"
                            name="email"
                            placeholder="Correo"
                            data-testid="login-email"
                            aria-required="true"
                        />
                        <Input
                            label="Contraseña"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            autoComplete="current-password"
                            name="password"
                            placeholder="Contraseña"
                            data-testid="login-password"
                            aria-required="true"
                        />

                        <div className="flex flex-col gap-3 mt-2">
                            <button
                                type="submit"
                                disabled={loading}
                                aria-busy={loading}
                                data-testid="login-submit"
                                className="inline-flex items-center justify-center rounded-lg bg-white text-gray-900 px-5 py-2.5 text-sm font-medium border hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-400 disabled:opacity-60"
                            >
                                {loading ? "Ingresando..." : "Ingresar (login local)"}
                            </button>
                        </div>
                    </form>
                </>
            )}

            {error && (
                <p
                    id="login-error"
                    className="text-red-600 mt-2"
                    role="alert"
                    aria-live="polite"
                    data-testid="login-error"
                >
                    {error}
                </p>
            )}

            <div className="mt-4 text-sm text-gray-600 flex items-center justify-between">
                <Link to="/" className="hover:underline">
                    ← Volver al inicio
                </Link>
                <div className="flex items-center gap-3">
                    <Link to="/auth/callback" className="hover:underline">
                        ¿Tienes token? Procesar callback
                    </Link>
                    <Link to="/admin/login" className="hover:underline">
                        Panel admin
                    </Link>
                </div>
            </div>

            {!ENABLE_LOCAL && (
                <p className="mt-3 text-xs text-gray-500">
                    Para habilitar el formulario local, ajusta{" "}
                    <code>VITE_ENABLE_LOCAL_LOGIN=true</code> en tu <code>.env</code>.
                </p>
            )}
        </div>
    );
}

export default LoginPage;