// src/components/Header.jsx
import React from "react";
import { NavLink, useNavigate, Link, useLocation } from "react-router-dom";
import LogoutButton from "@/components/LogoutButton";
import { useAuth } from "@/context/AuthContext";
import {
    UserCircle,
    Mail,
    ShieldCheck,
    LayoutDashboard,
    FileText,
    MessageSquareText,
    BarChart2,
    FlaskConical,
    Users as UsersIcon,
    Cog,
    Bell,
    Home as HomeIcon,
    ChevronRight,
} from "lucide-react";
import * as Tooltip from "@radix-ui/react-tooltip";
import SettingsPanel from "@/components/SettingsPanel";
import IconTooltip from "@/components/ui/IconTooltip";
import Badge from "@/components/Badge";
import assets from "@/config/assets";
const Header = () => {
    const { user, logout: doLogout } = useAuth();
    const logout = doLogout || (() => { });
    const role = user?.rol || "usuario";
    const isAuthenticated = !!user;
    const navigate = useNavigate();
    const location = useLocation();

    const [openSettings, setOpenSettings] = React.useState(false);

    // Avatar configurable + fallback seguro desde assets normalizados
    const AVATAR = import.meta.env.VITE_BOT_AVATAR || assets.BOT_AVATAR;

    // Abrir el widget de chat si está presente; si no, navegar a /chat
    const openChat = (e) => {
        try {
            if (window.ChatWidget?.open) {
                e?.preventDefault?.();
                window.ChatWidget.open();
            } else {
                navigate("/chat");
            }
        } catch {
            navigate("/chat");
        }
    };

    // ────────────────────────────────────────────────────────────
    // Breadcrumb simple (sin claves duplicadas)
    // ────────────────────────────────────────────────────────────
    const labelMap = {
        "": "Inicio",
        dashboard: "Dashboard",
        logs: "Logs",
        intents: "Intents",
        "intents-page": "Intents (página)",
        "intents-fallidos": "Intentos fallidos",
        "stadisticas-logs": "Estadísticas",
        "exportar-logs": "Exportar logs",
        exportaciones: "Exportaciones",
        users: "Usuarios",
        "user-management": "Usuarios",
        admin: "Admin",
        diagnostico: "Pruebas",
        chat: "Chat",
        iframe: "Iframe",
        auth: "Auth",
        callback: "Callback",
    };

    const path = location.pathname.replace(/^\/+|\/+$/g, "");
    const segments = path ? path.split("/") : [];
    const crumbs = [{ to: "/", label: labelMap[""], icon: HomeIcon }];
    let acc = "";
    for (const seg of segments) {
        acc += `/${seg}`;
        crumbs.push({ to: acc, label: labelMap[seg] || seg });
    }

    // ────────────────────────────────────────────────────────────
    // Navegación lateral (mantiene tu lógica de negocio)
    // ────────────────────────────────────────────────────────────
    const navLinks = [
        { to: "/", label: "Inicio", icon: HomeIcon, roles: ["admin", "soporte", "usuario"], tip: "Página de bienvenida" },
        { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, roles: ["admin", "soporte", "usuario"], tip: "Vista general del sistema" },
        { to: "/logs", label: "Logs", icon: FileText, roles: ["admin", "soporte"], tip: "Historial de conversaciones" },
        { to: "/intents", label: "Intents", icon: MessageSquareText, roles: ["admin"], tip: "Gestión de intents" },
        { to: "/stadisticas-logs", label: "Estadísticas", icon: BarChart2, roles: ["admin"], tip: "Métricas de uso" },
        { to: "/admin/diagnostico", label: "Pruebas", icon: FlaskConical, roles: ["admin", "soporte"], tip: "Diagnóstico y conexión" },
        { to: "/user-management", label: "Usuarios", icon: UsersIcon, roles: ["admin"], tip: "Gestión de usuarios" },
        // Compatibilidad /chat
        { to: "/chat", label: "Chat", icon: MessageSquareText, roles: ["admin", "soporte", "usuario"], tip: "Abrir chat de ayuda", isChat: true },
        { to: "/intentos-fallidos", label: "Intentos fallidos", icon: BarChart2, roles: ["admin"], tip: "Intents no reconocidos" },
    ];
    const canSee = (l) => !l.roles || l.roles.includes(role);

    return (
        <>
            <aside className="h-screen w-64 bg-gray-900 text-white flex flex-col justify-between">
                <div className="p-6">
                    {/* Brand / Home: avatar mini + título clicable al inicio */}
                    <div className="flex items-center gap-3 mb-4">
                        <Link to="/" className="shrink-0" aria-label="Ir a inicio">
                            <img
                                src={AVATAR}
                                onError={(e) => {
                                    e.currentTarget.src = "/bot-avatar.png";
                                }}
                                alt="Inicio"
                                className="w-10 h-10 rounded-lg object-contain bg-white/10 p-1"
                                loading="eager"
                            />
                        </Link>
                        <div className="flex-1">
                            <Link to="/" className="text-lg font-bold hover:underline">
                                Chatbot Tutor Virtual
                            </Link>
                            <div className="text-xs text-white/70">Panel de administración</div>
                        </div>

                        {/* Badge global de chat */}
                        <div className="ml-auto flex items-center gap-2">
                            <Bell className="w-5 h-5" />
                            <Badge mode="chat" size="xs" />
                        </div>
                    </div>

                    {/* Breadcrumb */}
                    <nav aria-label="Breadcrumb" className="mb-4">
                        <ol className="flex items-center gap-1 text-xs text-white/80">
                            {crumbs.map((c, i) => (
                                <li key={c.to} className="flex items-center">
                                    {i > 0 && <ChevronRight className="w-3 h-3 mx-1 opacity-70" />}
                                    <Link to={c.to} className="hover:underline inline-flex items-center gap-1">
                                        {c.icon ? <c.icon className="w-3.5 h-3.5" /> : null}
                                        <span className="truncate max-w-[140px]">{c.label}</span>
                                    </Link>
                                </li>
                            ))}
                        </ol>
                    </nav>

                    {/* Encabezado secundario */}
                    <div className="flex items-center gap-2 mb-4">
                        <UserCircle className="w-5 h-5" />
                        <h2 className="text-sm font-semibold">Bienvenido</h2>
                    </div>

                    {/* Info de usuario */}
                    {user && (
                        <div className="mb-6 space-y-1 text-sm">
                            <div className="flex items-center gap-2">
                                <Mail className="w-4 h-4" />
                                <span>{user.email}</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <ShieldCheck className="w-4 h-4" />
                                <span>Rol: {user.rol}</span>
                            </div>
                        </div>
                    )}

                    {/* Navegación lateral */}
                    <nav className="flex flex-col gap-2">
                        <Tooltip.Provider delayDuration={200} skipDelayDuration={150}>
                            {navLinks.filter(canSee).map(({ to, label, icon: Icon, tip, isChat }) => (
                                <Tooltip.Root key={to}>
                                    <Tooltip.Trigger asChild>
                                        <NavLink
                                            to={to}
                                            onClick={isChat ? openChat : undefined}
                                            className={({ isActive }) =>
                                                [
                                                    "hover:bg-gray-700 p-2 rounded flex items-center gap-2 transition-colors",
                                                    isActive ? "bg-gray-800 font-semibold" : "",
                                                ].join(" ")
                                            }
                                        >
                                            <Icon size={18} />
                                            <span className="truncate">{label}</span>
                                            {isChat && <Badge mode="chat" size="xs" className="ml-auto" />}
                                        </NavLink>
                                    </Tooltip.Trigger>
                                    <Tooltip.Portal>
                                        <Tooltip.Content
                                            className="rounded-md bg-black/90 text-white px-2 py-1 text-xs shadow"
                                            side="right"
                                            sideOffset={6}
                                        >
                                            {tip || label}
                                            <Tooltip.Arrow className="fill-black/90" />
                                        </Tooltip.Content>
                                    </Tooltip.Portal>
                                </Tooltip.Root>
                            ))}
                        </Tooltip.Provider>
                    </nav>
                </div>

                {/* Config + Logout */}
                <div className="p-6 flex items-center justify-between gap-2">
                    <IconTooltip label="Configuración" side="top">
                        <button
                            onClick={() => setOpenSettings(true)}
                            className="inline-flex items-center gap-2 px-3 py-2 rounded bg-white/10 hover:bg-white/20"
                            aria-label="Configuración"
                            type="button"
                        >
                            <Cog size={16} /> Config.
                        </button>
                    </IconTooltip>
                    <LogoutButton />
                </div>
            </aside>

            {/* Panel de Configuración */}
            <SettingsPanel
                open={openSettings}
                onClose={() => setOpenSettings(false)}
                isAuthenticated={isAuthenticated}
                onLogout={logout}
                onCloseChat={() => window.dispatchEvent(new CustomEvent("chat:close"))}
                onLanguageChange={(lang) =>
                    window.dispatchEvent(new CustomEvent("app:lang", { detail: { lang } }))
                }
            />
        </>
    );
};

export default Header;