import React, { useRef } from "react";
import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import { TooltipProvider } from "@/components/ui/IconTooltip";
import { useAuth } from "@/context/AuthContext";
import ProtectedRoute from "@/components/ProtectedRoute";
import RequireRole from "@/components/RequireRole";

// Páginas públicas
import HomePage from "@/pages/HomePage";
import LoginPage from "@/pages/LoginPage";
import Unauthorized from "@/pages/Unauthorized";
import AuthCallback from "@/pages/AuthCallback";
import AdminRegisterPage from "@/pages/AdminRegisterPage";
import AdminLoginPage from "@/pages/AdminLoginPage";

// Páginas principales (protegidas)
import Dashboard from "@/pages/Dashboard";
import ProfilePage from "@/pages/ProfilePage";
import TestPage from "@/pages/TestPage";
import LogsPage from "@/pages/LogsPage";
import IntentsPage from "@/pages/IntentsPage";
import StatsPage from "@/pages/StatsPage";
import StatsPageV2 from "@/pages/StatsPageV2";
import UserManagementPage from "@/pages/UserManagementPage";
import AssignRoles from "@/pages/AssignRoles";
import UploadIntentsCSV from "@/components/UploadIntentsCSV";
import ExportacionesPage from "@/pages/ExportacionesPage";
import IntentosFallidosPage from "@/pages/IntentosFallidosPage";

// Chat
import ChatPage from "@/pages/ChatPage";
import Harness from "@/pages/Harness";

// Bubble embebido
import HostChatBubbleRef from "@/embed/HostChatBubbleRef.jsx";
import "@/i18n";

// =========================
// ✅ Variables de entorno
// =========================
const BOT_AVATAR = import.meta.env.VITE_BOT_AVATAR || "/mi-avatar.png";
const SHOW_HARNESS = import.meta.env.VITE_SHOW_CHAT_HARNESS === "true";
const SHOW_BUBBLE_DEBUG = import.meta.env.VITE_SHOW_BUBBLE_DEBUG === "true";

// =========================
// Helpers
// =========================

/** Ruta por defecto según rol */
function roleDefaultPath(role) {
    const r = (role || "").toLowerCase();
    return r === "admin" || r === "soporte" ? "/dashboard" : "/";
}

/** Redirección catch-all según sesión/rol */
function CatchAllRedirect() {
    const { isAuthenticated, user } = useAuth();
    const to = isAuthenticated ? roleDefaultPath(user?.rol || user?.role) : "/";
    return <Navigate to={to} replace />;
}

/** Rutas públicas que NO deben verse si ya hay sesión */
function PublicOnlyRoute({ children }) {
    const { isAuthenticated, user } = useAuth();
    if (!isAuthenticated) return children;
    return <Navigate to={roleDefaultPath(user?.rol || user?.role)} replace />;
}

/** Permite AuthCallback si trae token en query/hash */
function PublicOnlyOrToken({ children }) {
    const { isAuthenticated, user } = useAuth();
    const location = useLocation();

    const search = new URLSearchParams(location.search || "");
    const hashParams = new URLSearchParams(String(location.hash || "").replace(/^#/, ""));

    const tokenFromQuery =
        search.get("access_token") || search.get("token") || search.get("t");
    const tokenFromHash =
        hashParams.get("access_token") || hashParams.get("token") || hashParams.get("t");

    const hasToken = Boolean(tokenFromQuery || tokenFromHash);
    if (isAuthenticated && !hasToken) {
        return <Navigate to={roleDefaultPath(user?.rol || user?.role)} replace />;
    }
    return children;
}

/** Carga perezosa segura */
function lazyWithFallback(loader, name) {
    return React.lazy(async () => {
        try {
            const mod = await loader();
            return mod;
        } catch {
            return {
                default: () => (
                    <div className="p-6 text-sm text-gray-600">
                        La página <strong>{name}</strong> no está disponible.
                    </div>
                ),
            };
        }
    });
}

const RegisterPage = lazyWithFallback(() => import("@/pages/RegisterPage"), "Registro");
const ForgotPasswordPage = lazyWithFallback(
    () => import("@/pages/ForgotPasswordPage"),
    "Recuperar contraseña"
);

// Config UI
const ui = {
    avatar: BOT_AVATAR,
};

// =========================
// App principal
// =========================
export default function App() {
    const bubbleRef = useRef(null);
    const { isAuthenticated, accessToken } = useAuth();

    // Detecta si está embebido
    const params = new URLSearchParams(window.location.search);
    const isEmbedded = params.get("embed") === "1" || window.self !== window.top;

    const handleSendToken = () => {
        if (isAuthenticated && accessToken) {
            bubbleRef.current?.sendAuthToken?.(accessToken);
        }
    };

    const handleLoginDemo = () => {
        bubbleRef.current?.sendAuthToken?.("FAKE_TOKEN_ZAJUNA");
        bubbleRef.current?.open?.();
    };

    return (
        <TooltipProvider>
            <Routes>
                {/* 🌐 Públicas */}
                <Route path="/" element={<HomePage />} />
                <Route
                    path="/login"
                    element={
                        <PublicOnlyRoute>
                            <LoginPage />
                        </PublicOnlyRoute>
                    }
                />
                <Route path="/unauthorized" element={<Unauthorized />} />
                <Route
                    path="/auth/callback"
                    element={
                        <PublicOnlyOrToken>
                            <AuthCallback />
                        </PublicOnlyOrToken>
                    }
                />
                <Route
                    path="/register"
                    element={
                        <PublicOnlyRoute>
                            <React.Suspense fallback={<div className="p-6 text-sm">Cargando…</div>}>
                                <RegisterPage />
                            </React.Suspense>
                        </PublicOnlyRoute>
                    }
                />
                <Route
                    path="/forgot-password"
                    element={
                        <PublicOnlyRoute>
                            <React.Suspense fallback={<div className="p-6 text-sm">Cargando…</div>}>
                                <ForgotPasswordPage />
                            </React.Suspense>
                        </PublicOnlyRoute>
                    }
                />

                {/* 💬 Chat */}
                <Route path="/chat" element={<ChatPage />} />
                <Route path="/chat-embed" element={<ChatPage forceEmbed />} />
                <Route path="/iframe/chat" element={<ChatPage forceEmbed />} />
                <Route path="/widget" element={<ChatPage forceEmbed embedHeight="100vh" />} />
                {SHOW_HARNESS && <Route path="/chat-harness" element={<Harness />} />}

                {/* 🔒 Protegidas */}
                <Route
                    path="/dashboard"
                    element={
                        <ProtectedRoute>
                            <Dashboard />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/profile"
                    element={
                        <ProtectedRoute>
                            <ProfilePage />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/diagnostico"
                    element={
                        <ProtectedRoute>
                            <TestPage />
                        </ProtectedRoute>
                    }
                />

                {/* 🔐 admin */}
                <Route
                    path="/logs"
                    element={
                        <ProtectedRoute>
                            <RequireRole allowedRoles={["admin", "soporte"]}>
                                <LogsPage />
                            </RequireRole>
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/intents"
                    element={
                        <ProtectedRoute>
                            <RequireRole allowedRoles={["admin"]}>
                                <IntentsPage />
                            </RequireRole>
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/stats"
                    element={
                        <ProtectedRoute>
                            <RequireRole allowedRoles={["admin"]}>
                                <StatsPage />
                            </RequireRole>
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/stats-v2"
                    element={
                        <ProtectedRoute>
                            <RequireRole allowedRoles={["admin"]}>
                                <StatsPageV2 />
                            </RequireRole>
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/users"
                    element={
                        <ProtectedRoute>
                            <RequireRole allowedRoles={["admin"]}>
                                <UserManagementPage />
                            </RequireRole>
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/assign-roles"
                    element={
                        <ProtectedRoute>
                            <RequireRole allowedRoles={["admin"]}>
                                <AssignRoles />
                            </RequireRole>
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/upload-intents"
                    element={
                        <ProtectedRoute>
                            <RequireRole allowedRoles={["admin"]}>
                                <UploadIntentsCSV />
                            </RequireRole>
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/admin/exportaciones"
                    element={
                        <ProtectedRoute>
                            <RequireRole allowedRoles={["admin"]}>
                                <ExportacionesPage />
                            </RequireRole>
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/intentos-fallidos"
                    element={
                        <ProtectedRoute>
                            <RequireRole allowedRoles={["admin"]}>
                                <IntentosFallidosPage />
                            </RequireRole>
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/admin/register"
                    element={
                        <PublicOnlyRoute>
                            <AdminRegisterPage />
                        </PublicOnlyRoute>
                    }
                />
                <Route
                    path="/admin/login"
                    element={
                        <PublicOnlyRoute>
                            <AdminLoginPage />
                        </PublicOnlyRoute>
                    }
                />
                <Route path="*" element={<CatchAllRedirect />} />
            </Routes>

            {/* 🫧 Widget embebido */}
            {!isEmbedded && (
                <HostChatBubbleRef
                    ref={bubbleRef}
                    iframeUrl={`${window.location.origin}/?embed=1&guest=1`}
                    allowedOrigin={window.location.origin}
                    title="Tutor Virtual"
                    subtitle="Sustentación"
                    startOpen={true}
                    theme="auto"
                    showDebug={false}
                    avatar={BOT_AVATAR}
                    onAuthNeeded={handleSendToken}
                    onTelemetry={(evt) =>
                        import.meta.env.DEV && console.log("[telemetry]", evt)
                    }
                />
            )}

            {/* 🔧 Debug opcional */}
            {!isEmbedded && SHOW_BUBBLE_DEBUG && (
                <div
                    style={{
                        position: "fixed",
                        right: 10,
                        bottom: 10,
                        zIndex: 2147483000,
                    }}
                >
                    <div
                        style={{
                            background: "rgba(2,6,23,.75)",
                            color: "#E5E7EB",
                            border: "1px solid #334155",
                            borderRadius: 12,
                            padding: 10,
                            display: "flex",
                            gap: 8,
                            flexWrap: "wrap",
                        }}
                    >
                        <button onClick={() => bubbleRef.current?.open?.()} className="btn">
                            Abrir Chat
                        </button>
                        <button onClick={() => bubbleRef.current?.close?.()} className="btn">
                            Cerrar Chat
                        </button>
                        <button onClick={handleLoginDemo} className="btn">
                            Login & Enviar Token
                        </button>
                        <button
                            onClick={() => bubbleRef.current?.setTheme?.("dark")}
                            className="btn"
                        >
                            Tema: Dark
                        </button>
                        <button
                            onClick={() => bubbleRef.current?.setTheme?.("light")}
                            className="btn"
                        >
                            Tema: Light
                        </button>
                        <button
                            onClick={() => bubbleRef.current?.setLanguage?.("en")}
                            className="btn"
                        >
                            Idioma: EN
                        </button>
                        <button
                            onClick={() => bubbleRef.current?.setLanguage?.("es")}
                            className="btn"
                        >
                            Idioma: ES
                        </button>
                    </div>
                </div>
            )}
        </TooltipProvider>
    );
}
