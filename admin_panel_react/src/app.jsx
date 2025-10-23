import React from "react";
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
import "@/styles/index.css";

// Flag opcional para habilitar la página de pruebas del chat
const SHOW_HARNESS = import.meta.env.VITE_SHOW_CHAT_HARNESS === "true";

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

    const tokenFromQuery = search.get("access_token") || search.get("token") || search.get("t");
    const tokenFromHash = hashParams.get("access_token") || hashParams.get("token") || hashParams.get("t");

    const hasToken = Boolean(tokenFromQuery || tokenFromHash);

    if (isAuthenticated && !hasToken) {
        return <Navigate to={roleDefaultPath(user?.rol || user?.role)} replace />;
    }
    return children;
}

/** Carga perezosa segura para páginas públicas opcionales */
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
const ForgotPasswordPage = lazyWithFallback(() => import("@/pages/ForgotPasswordPage"), "Recuperar contraseña");

export default function App() {
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

                {/* 🔒 Protegidas (sin rol específico) */}
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

                {/* 🔐 admin/soporte */}
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

                {/* 🔐 admin-only */}
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

                {/* Admin: registro/login del panel */}
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

                {/* Catch-all → Home/Panel según sesión */}
                <Route path="*" element={<CatchAllRedirect />} />
            </Routes>
        </TooltipProvider>
    );
}