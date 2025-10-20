// src/layouts/AdminLayout.jsx
import { Link, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import IconTooltip from "@/components/ui/IconTooltip";
import ChatWidget from "@/components/ChatWidget";
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
} from "lucide-react";

const AdminLayout = () => {
    const { logout, user } = useAuth();
    const navigate = useNavigate();

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

    return (
        <div className="flex min-h-screen">
            {/* Sidebar */}
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
                        <Link to="/dashboard" className="hover:bg-gray-700 px-3 py-2 rounded flex items-center gap-2">
                            <IconTooltip label="Dashboard" side="right">
                                <LayoutDashboard className="w-4 h-4" />
                            </IconTooltip>
                            <span>Dashboard</span>
                        </Link>

                        <Link to="/intents" className="hover:bg-gray-700 px-3 py-2 rounded flex items-center gap-2">
                            <IconTooltip label="Intents" side="right">
                                <Brain className="w-4 h-4" />
                            </IconTooltip>
                            <span>Intents</span>
                        </Link>

                        <Link to="/logs" className="hover:bg-gray-700 px-3 py-2 rounded flex items-center gap-2">
                            <IconTooltip label="Logs" side="right">
                                <FileText className="w-4 h-4" />
                            </IconTooltip>
                            <span>Logs</span>
                        </Link>

                        <Link to="/stats" className="hover:bg-gray-700 px-3 py-2 rounded flex items-center gap-2">
                            <IconTooltip label="Estadísticas" side="right">
                                <BarChart2 className="w-4 h-4" />
                            </IconTooltip>
                            <span>Estadísticas</span>
                        </Link>

                        {/* 🔧 coincide con App.jsx */}
                        <Link to="/diagnostico" className="hover:bg-gray-700 px-3 py-2 rounded flex items-center gap-2">
                            <IconTooltip label="Pruebas/Diagnóstico" side="right">
                                <FlaskConical className="w-4 h-4" />
                            </IconTooltip>
                            <span>Pruebas</span>
                        </Link>
                    </nav>
                </div>

                <div className="p-4">
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

            {/* Main */}
            <main className="flex-1 bg-gray-100 p-6">
                <Outlet />
            </main>

            {/* ✅ Un solo widget global (REST/WS según ENV) */}
            <ChatWidget connectFn={connectFn} title="TutorBot" />
        </div>
    );
};

export default AdminLayout;