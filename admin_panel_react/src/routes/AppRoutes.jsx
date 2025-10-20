// src/routes/AppRoutes.jsx
import { Routes, Route, Navigate } from "react-router-dom";

// Páginas públicas
import HomePage from "@/pages/HomePage";
import LoginPage from "@/pages/LoginPage";
import Unauthorized from "@/pages/Unauthorized";
import AuthCallback from "@/pages/AuthCallback";

// Páginas protegidas
import Dashboard from "@/pages/Dashboard";
import LogsPage from "@/pages/LogsPage";
import IntentsPage from "@/pages/IntentsPage";
import UserManagement from "@/pages/UserManagement";
import TestPage from "@/pages/TestPage";
import CrearIntentPage from "@/pages/CrearIntentPage";
import BuscarIntentPage from "@/pages/BuscarIntentPage";
import StadisticasLogsPage from "@/pages/StadisticasLogsPage";
import IntentosFallidosPage from "@/pages/IntentosFallidosPage";
import ExportarLogsPage from "@/pages/ExportarLogsPage";
import ExportacionesPage from "@/pages/ExportacionesPage";
import TrainBotPage from "@/pages/TrainBotPage";

// Nota: compat → DiagnosticoPage apunta a TestPage
import DiagnosticoPage from "@/pages/TestPage";

// Chat contenedor
import ChatPage from "@/pages/ChatPage";

// Intents CRUD
import IntentEdit from "@/pages/IntentEdit";
import IntentDetail from "@/pages/IntentDetail";

// Autorización
import ProtectedRoute from "@/routes/ProtectedRoute";
import RequireRole from "@/components/RequireRole";

// Consolidado: una sola fuente de ListIntents
import ListIntents from "@/pages/ListIntents";

const AppRoutes = () => {
    return (
        <Routes>
            {/* 🌐 Públicas */}
            <Route path="/" element={<HomePage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/unauthorized" element={<Unauthorized />} />
            <Route path="/auth/callback" element={<AuthCallback />} />

            {/* ✅ Chat públicas */}
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/iframe/chat" element={<ChatPage forceEmbed />} />
            <Route path="/chat-embed" element={<ChatPage forceEmbed />} />
            <Route path="/chat-embed.html" element={<Navigate to="/chat-embed" replace />} />

            {/* 🔐 Protegidas */}
            <Route
                path="/dashboard"
                element={
                    <ProtectedRoute>
                        <RequireRole allowedRoles={["admin", "soporte"]}>
                            <Dashboard />
                        </RequireRole>
                    </ProtectedRoute>
                }
            />

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

            {/* Intents */}
            <Route
                path="/intents"
                element={
                    <ProtectedRoute>
                        <RequireRole allowedRoles={["admin"]}>
                            <CrearIntentPage />
                        </RequireRole>
                    </ProtectedRoute>
                }
            />
            <Route
                path="/intents/buscar"
                element={
                    <ProtectedRoute>
                        <RequireRole allowedRoles={["admin", "soporte"]}>
                            <BuscarIntentPage />
                        </RequireRole>
                    </ProtectedRoute>
                }
            />
            <Route
                path="/intents/list"
                element={
                    <ProtectedRoute>
                        <RequireRole allowedRoles={["admin", "soporte"]}>
                            <ListIntents />
                        </RequireRole>
                    </ProtectedRoute>
                }
            />
            <Route
                path="/intents-page"
                element={
                    <ProtectedRoute>
                        <RequireRole allowedRoles={["admin", "soporte"]}>
                            <IntentsPage />
                        </RequireRole>
                    </ProtectedRoute>
                }
            />

            {/* Intents CRUD */}
            <Route
                path="/intents/new"
                element={
                    <ProtectedRoute>
                        <RequireRole allowedRoles={["admin"]}>
                            <IntentEdit />
                        </RequireRole>
                    </ProtectedRoute>
                }
            />
            <Route
                path="/intents/:id/edit"
                element={
                    <ProtectedRoute>
                        <RequireRole allowedRoles={["admin"]}>
                            <IntentEdit />
                        </RequireRole>
                    </ProtectedRoute>
                }
            />
            <Route
                path="/intents/:id"
                element={
                    <ProtectedRoute>
                        <RequireRole allowedRoles={["admin", "soporte"]}>
                            <IntentDetail />
                        </RequireRole>
                    </ProtectedRoute>
                }
            />

            {/* Usuarios */}
            <Route
                path="/user-management"
                element={
                    <ProtectedRoute>
                        <RequireRole allowedRoles={["admin"]}>
                            <UserManagement />
                        </RequireRole>
                    </ProtectedRoute>
                }
            />

            {/* Herramientas / Tests */}
            <Route
                path="/test"
                element={
                    <ProtectedRoute>
                        <RequireRole allowedRoles={["admin", "soporte"]}>
                            <TestPage />
                        </RequireRole>
                    </ProtectedRoute>
                }
            />
            <Route
                path="/intentos-fallidos"
                element={
                    <ProtectedRoute>
                        <RequireRole allowedRoles={["admin", "soporte"]}>
                            <IntentosFallidosPage />
                        </RequireRole>
                    </ProtectedRoute>
                }
            />

            {/* Estadísticas (ruta real) */}
            <Route
                path="/stadisticas-logs"
                element={
                    <ProtectedRoute>
                        <RequireRole allowedRoles={["admin", "soporte"]}>
                            <StadisticasLogsPage />
                        </RequireRole>
                    </ProtectedRoute>
                }
            />

            <Route
                path="/exportar-logs"
                element={
                    <ProtectedRoute>
                        <RequireRole allowedRoles={["admin", "soporte"]}>
                            <ExportarLogsPage />
                        </RequireRole>
                    </ProtectedRoute>
                }
            />

            <Route
                path="/exportaciones"
                element={
                    <ProtectedRoute>
                        <RequireRole allowedRoles={["admin", "soporte"]}>
                            <ExportacionesPage />
                        </RequireRole>
                    </ProtectedRoute>
                }
            />

            <Route
                path="/entrenar-bot"
                element={
                    <ProtectedRoute>
                        <RequireRole allowedRoles={["admin", "soporte"]}>
                            <TrainBotPage />
                        </RequireRole>
                    </ProtectedRoute>
                }
            />

            {/* Diagnóstico (ruta real) */}
            <Route
                path="/admin/diagnostico"
                element={
                    <ProtectedRoute>
                        <RequireRole allowedRoles={["admin", "soporte"]}>
                            <DiagnosticoPage />
                        </RequireRole>
                    </ProtectedRoute>
                }
            />

            {/* Catch-all → Home */}
            <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
    );
};

export default AppRoutes;