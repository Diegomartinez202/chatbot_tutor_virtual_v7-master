// src/pages/LoginPage.jsx
import { useEffect, useState, useMemo } from "react";
import { useNavigate, Link } from "react-router-dom";
import Input from "@/components/Input";
import IconTooltip from "@/components/ui/IconTooltip";
import { Lock } from "lucide-react";

import { useAuth } from "@/context/AuthContext";
import { login as apiLogin, me as apiMe } from "@/services/authApi"; // si no existen, haremos fallback
import axiosClient, { setAuthToken } from "@/services/axiosClient";
import { STORAGE_KEYS } from "@/lib/constants";

// Flags de entorno
const ENABLE_LOCAL = String(import.meta.env.VITE_ENABLE_LOCAL_LOGIN) === "true";
const ZAJUNA_SSO =
    import.meta.env.VITE_ZAJUNA_SSO_URL ||
    import.meta.env.VITE_ZAJUNA_LOGIN_URL ||
    "";
const SHOW_GUEST = String(import.meta.env.VITE_SHOW_GUEST ?? "true") !== "false";

export default function LoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const navigate = useNavigate();
    const { login: ctxLogin, redirectToZajunaSSO } = useAuth();

    useEffect(() => {
        document.title = "Iniciar sesión – Chatbot";
    }, []);

    // URL de retorno estándar para SSO (si no se usa helper del AuthContext)
    const zajunaLoginUrl = useMemo(() => {
        if (ZAJUNA_SSO) return ZAJUNA_SSO;
        const back = `${window.location.origin}/auth/callback`;
        return `/api/auth/zajuna/login?redirect_uri=${encodeURIComponent(back)}`;
    }, []);

    // ——— LOGIN LOCAL (si está habilitado) ———
    const handleLogin = async (e) => {
        e.preventDefault();
        if (!ENABLE_LOCAL) return;

        setLoading(true);
        setError("");

        try {
            // 1) Login local — usa authApi si existe, si no, fallback directo a axiosClient
            let access = null;

            if (typeof apiLogin === "function") {
                const r = await apiLogin({ email, password });
                access = r?.access_token || r?.token || r?.data?.access_token;
            } else {
                const r = await axiosClient.post("/auth/login", { email, password });
                access = r?.data?.access_token;
            }

            if (!access) throw new Error("No llegó access_token");

            // 2) Persistir y fijar Authorization por defecto
            try {
                localStorage.setItem(STORAGE_KEYS.accessToken, String(access));
            } catch { }
            setAuthToken(String(access));

            // 3) Notificar al contexto (si implementa login)
            try {
                if (typeof ctxLogin === "function") {
                    await ctxLogin(access);
                }
            } catch {
                // opcional
            }

            // 4) Consultar perfil para decidir la redirección
            let role = "usuario";
            try {
                let profile = null;
                if (typeof apiMe === "function") {
                    profile = await apiMe();
                } else {
                    const pr = await axiosClient.get("/auth/me");
                    profile = pr?.data;
                }
                role = profile?.rol || profile?.role || "usuario";
            } catch {
                // si falla /me, continúa con rol "usuario"
            }

            if (role === "admin" || role === "soporte") {
                navigate("/dashboard", { replace: true });
            } else {
                navigate("/chat", { replace: true });
            }
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

    // ——— SSO Zajuna (intacto + robusto para iframes) ———
    const handleZajuna = () => {
        try {
            if (typeof redirectToZajunaSSO === "function") {
                redirectToZajunaSSO();
                return;
            }
            const url = zajunaLoginUrl;
            if (window.self !== window.top) window.top.location.href = url;
            else window.location.href = url;
        } catch (err) {
            console.error("Error al redirigir al SSO:", err);
            setError("Error al conectar con el servicio de autenticación.");
        }
    };

    const handleGuest = () => navigate("/chat");

    const goBack = () => {
        if (window.history.length > 1) navigate(-1);
        else navigate("/", { replace: true });
    };

    return (
        <div className="min-h-[80vh] grid place-items-center px-4 py-8">
            <div className="w-full max-w-md rounded-2xl bg-white shadow-sm ring-1 ring-gray-100 p-6 sm:p-7">
                {/* Header */}
                <div className="flex items-center justify-between mb-5">
                    <div className="flex items-center gap-2">
                        <IconTooltip label="Iniciar sesión" side="top">
                            <Lock className="w-6 h-6 text-gray-700" aria-hidden="true" />
                        </IconTooltip>
                        <h2 className="text-xl font-semibold" id="login-title">
                            Iniciar sesión
                        </h2>
                    </div>

                    <button
                        type="button"
                        onClick={goBack}
                        className="px-3 py-1.5 rounded-md border text-sm hover:bg-gray-50"
                    >
                        ← Volver
                    </button>
                </div>

                {/* —— SSO de Zajuna (principal) —— */}
                {zajunaLoginUrl ? (
                    <div className="flex flex-col gap-3" aria-labelledby="login-title">
                        <button
                            type="button"
                            onClick={handleZajuna}
                            disabled={loading}
                            data-testid="login-zajuna"
                            className="inline-flex items-center justify-center rounded-lg bg-indigo-600 text-white px-5 py-2.5 text-sm font-medium hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:ring-offset-2 disabled:opacity-60"
                        >
                            Ingresar con Zajuna
                        </button>

                        {SHOW_GUEST && (
                            <button
                                type="button"
                                onClick={handleGuest}
                                disabled={loading}
                                data-testid="login-guest"
                                className="inline-flex items-center justify-center rounded-lg bg-gray-50 text-gray-900 px-5 py-2.5 text-sm font-medium border hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-300"
                            >
                                Entrar como invitado (sin registro)
                            </button>
                        )}
                    </div>
                ) : (
                    <p className="text-sm text-gray-600">
                        Configura <code>VITE_ZAJUNA_SSO_URL</code> o{" "}
                        <code>VITE_ZAJUNA_LOGIN_URL</code> en tu <code>.env</code> para
                        habilitar el acceso SSO de Zajuna.
                    </p>
                )}

                {/* —— Formulario local (opcional) —— */}
                {ENABLE_LOCAL && (
                    <>
                        <div className="my-5 h-px bg-gray-200" role="separator" />
                        <form onSubmit={handleLogin} aria-describedby="login-error" noValidate>
                            <Input
                                label="Email"
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                autoComplete="username"
                                name="email"
                                placeholder="correo@ejemplo.com"
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
                                placeholder="••••••••"
                                data-testid="login-password"
                                aria-required="true"
                            />

                            <button
                                type="submit"
                                disabled={loading}
                                aria-busy={loading}
                                data-testid="login-submit"
                                className="mt-3 w-full inline-flex items-center justify-center rounded-lg bg-white text-gray-900 px-5 py-2.5 text-sm font-medium border hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:ring-offset-2 disabled:opacity-60"
                            >
                                {loading ? "Ingresando..." : "Ingresar (login local)"}
                            </button>
                        </form>
                    </>
                )}

                {error && (
                    <p
                        id="login-error"
                        className="text-red-600 mt-3"
                        role="alert"
                        aria-live="polite"
                        data-testid="login-error"
                    >
                        {error}
                    </p>
                )}

                <div className="mt-5 text-sm text-gray-600 flex flex-wrap items-center justify-between gap-3">
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
        </div>
    );
}
