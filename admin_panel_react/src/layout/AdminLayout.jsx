// src/layouts/AdminLayout.jsx
import React from "react";
import { Link, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { useAuthStore } from "@/store/authStore";
import IconTooltip from "@/components/ui/IconTooltip";
import ChatWidget from "@/components/ChatWidget";
import HybridChatWidget from "@/components/HybridChatWidget"; // <- Ajusta si tu ruta difiere
import { connectRasaRest } from "@/services/chat/connectRasaRest";
import { connectWS } from "@/services/chat/connectWS";
import {
    Bot,
    Mail,
    Shield,
    LayoutDashboard,
    Brain,
    FileText,
    BarChart2,
    FlaskConical,
    LogOut,
    Mic, // 🎙️ Voice
    Cog
} from "lucide-react";

const AdminLayout = () => {
    const { logout, user } = useAuth();
    const navigate = useNavigate();

    // 👉 token desde Zustand (compat con setAccessTokenGetter ya hecho en main.jsx)
    const accessToken = useAuthStore((s) => s.accessToken) || null;

    const handleLogout = async () => {
        await logout();
        navigate("/login");
    };

    // 🚦 REST/WS por ENV (Vite)
    const transport = (import.meta.env.VITE_CHAT_TRANSPORT || "rest").toLowerCase();
    const connectFn =
        transport === "ws"
            ? () => connectWS({ wsUrl: import.meta.env.VITE_RASA_WS_URL || "wss://tu-ws" })
            : connectRasaRest;

    // 🧰 Abre SettingsPanel (lo escucha Header.jsx con window.addEventListener("settings:open", ...))
    const openSettings = () => {
        try {
            window.dispatchEvent(new CustomEvent("settings:open"));
        } catch { }
    };

    return (
        <div className="flex min-h-screen relative">
            {/* ===== Sidebar ===== */}
            <aside className="w-64 bg-gray-800 text-white flex flex-col justify-between">
                <div className="p-4">
                    <div className="flex items-center gap-2 mb-6">
                        <Bot className="w-6 h-6 text-indigo-300" />
                        <h2 className="text-2xl font-bold">Panel Admin</h2>
                    </div>

                    {user && (
                        <div className="mb-6 space-y-1 text-sm">
                            <div className="flex items-center gap-2">
                                <Mail className="w-4 h-4 opacity-80" />
                                <span>{user.email}</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <Shield className="w-4 h-4 opacity-80" />
                                <span>Rol: {user.rol}</span>
                            </div>
                        </div>
                    )}

                    <nav className="flex flex-col space-y-2">
                        <Link
                            to="/dashboard"
                            className="hover:bg-gray-700 px-3 py-2 rounded flex items-center gap-2"
                        >
                            <IconTooltip label="Dashboard" side="right">
                                <LayoutDashboard className="w-4 h-4" />
                            </IconTooltip>
                            <span>Dashboard</span>
                        </Link>

                        <Link
                            to="/intents"
                            className="hover:bg-gray-700 px-3 py-2 rounded flex items-center gap-2"
                        >
                            <IconTooltip label="Intents" side="right">
                                <Brain className="w-4 h-4" />
                            </IconTooltip>
                            <span>Intents</span>
                        </Link>

                        <Link
                            to="/logs"
                            className="hover:bg-gray-700 px-3 py-2 rounded flex items-center gap-2"
                        >
                            <IconTooltip label="Logs" side="right">
                                <FileText className="w-4 h-4" />
                            </IconTooltip>
                            <span>Logs</span>
                        </Link>

                        <Link
                            to="/stats"
                            className="hover:bg-gray-700 px-3 py-2 rounded flex items-center gap-2"
                        >
                            <IconTooltip label="Estadísticas" side="right">
                                <BarChart2 className="w-4 h-4" />
                            </IconTooltip>
                            <span>Estadísticas</span>
                        </Link>

                        {/* 🔧 coincide con App.jsx (ruta de diagnóstico/pruebas) */}
                        <Link
                            to="/diagnostico"
                            className="hover:bg-gray-700 px-3 py-2 rounded flex items-center gap-2"
                        >
                            <IconTooltip label="Pruebas/Diagnóstico" side="right">
                                <FlaskConical className="w-4 h-4" />
                            </IconTooltip>
                            <span>Pruebas</span>
                        </Link>

                        {/* 🎙️ NUEVO: Voice dashboard (ya tenías la ruta /voice en App.jsx) */}
                        <Link
                            to="/voice"
                            className="hover:bg-gray-700 px-3 py-2 rounded flex items-center gap-2"
                        >
                            <IconTooltip label="Audios (Voice)" side="right">
                                <Mic className="w-4 h-4" />
                            </IconTooltip>
                            <span>Audios (Voice)</span>
                        </Link>
                    </nav>
                </div>

                <div className="p-4 space-y-2">
                    {/* ⚙️ Configuración accesible también desde el sidebar */}
                    <button
                        onClick={openSettings}
                        type="button"
                        className="w-full bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded text-white flex items-center justify-center gap-2"
                    >
                        <Cog className="w-4 h-4" />
                        Configuración
                    </button>

                    <button
                        onClick={handleLogout}
                        className="w-full bg-red-600 hover:bg-red-700 px-4 py-2 rounded text-white flex items-center justify-center gap-2"
                        type="button"
                    >
                        <LogOut className="w-4 h-4" />
                        Cerrar sesión
                    </button>
                </div>
            </aside>

            {/* ===== Main ===== */}
            <main className="flex-1 bg-gray-100 p-6">
                <Outlet />
            </main>

            {/* ===== Botón flotante arriba-derecha para abrir SettingsPanel ===== */}
            <button
                type="button"
                onClick={openSettings}
                className="fixed top-4 right-4 z-[60] inline-flex items-center gap-2 px-3 py-2 rounded bg-gray-900 text-white hover:bg-black/80 shadow-lg"
                aria-label="Abrir configuración"
                title="Configuración"
            >
                <Cog className="w-4 h-4" />
                <span className="hidden sm:inline">Config</span>
            </button>

            {/* ===== Widgets globales ===== */}
            <ChatWidget
                connectFn={connectFn}
                title="TutorBot"
                embed={false}
                authToken={accessToken || null}
            />
            <HybridChatWidget defaultOpen={false} />
        </div>
    );
};

export default AdminLayout;
