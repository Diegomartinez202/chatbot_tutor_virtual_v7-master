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
import { useTranslation } from "react-i18next";
import LanguageSelector from "@/components/LanguageSelector";
import ThemeToggle from "@/components/ThemeToggle";
// Mantengo este import para no romper nada que lo referencie en el futuro:
import { useJwtAuthSnapshot } from "@/hooks/useJwtAuthSnapshot";

// ⬇️ Flag de entorno: solo muestra enlaces dev cuando estás en dev
const IS_DEV =
    String(import.meta.env.MODE || import.meta.env.VITE_APP_ENV || "dev")
        .toLowerCase() === "dev";

const Header = () => {
    const { t } = useTranslation(); // defaultNS=common
    const { user, logout: doLogout } = useAuth(); // respetamos tu contexto
    const logout = doLogout || (() => { });
    const role = user?.rol || "usuario";
    const isAuthenticated = !!user;
    const navigate = useNavigate();
    const location = useLocation();

    const [openSettings, setOpenSettings] = React.useState(false);

    const AVATAR = import.meta.env.VITE_BOT_AVATAR || assets.BOT_AVATAR;

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

    const labelMap = {
        "": t("inicio"),
        dashboard: t("dashboard"),
        logs: t("logs"),
        intents: t("intents"),
        "intents-page": t("intents_pagina"),
        "intents-fallidos": t("intentos_fallidos"),
        "stadisticas-logs": t("estadisticas"),
        "exportar-logs": t("exportar_logs"),
        exportaciones: t("exportaciones"),
        users: t("usuarios"),
        "user-management": t("gestion_usuarios"),
        admin: t("admin"),
        diagnostico: t("pruebas"),
        chat: t("chat"),
        iframe: t("iframe"),
        auth: t("auth"),
        callback: t("callback"),
    };

    const path = location.pathname.replace(/^\/+|\/+$/g, "");
    const segments = path ? path.split("/") : [];
    const crumbs = [{ to: "/", label: labelMap[""], icon: HomeIcon }];
    let acc = "";
    for (const seg of segments) {
        acc += `/${seg}`;
        crumbs.push({ to: acc, label: labelMap[seg] || seg });
    }

    const navLinks = [
        {
            to: "/",
            label: t("inicio"),
            icon: HomeIcon,
            roles: ["admin", "soporte", "usuario"],
            tip: t("pagina_bienvenida"),
        },
        {
            to: "/dashboard",
            label: t("dashboard"),
            icon: LayoutDashboard,
            roles: ["admin", "soporte", "usuario"],
            tip: t("vista_general"),
        },
        {
            to: "/logs",
            label: t("logs"),
            icon: FileText,
            roles: ["admin", "soporte"],
            tip: t("historial_conversaciones"),
        },
        {
            to: "/intents",
            label: t("intents"),
            icon: MessageSquareText,
            roles: ["admin"],
            tip: t("gestion_intents"),
        },
        {
            to: "/stadisticas-logs",
            label: t("estadisticas"),
            icon: BarChart2,
            roles: ["admin"],
            tip: t("metricas_uso"),
        },
        {
            to: "/admin/diagnostico",
            label: t("pruebas"),
            icon: FlaskConical,
            roles: ["admin", "soporte"],
            tip: t("diagnostico_conexion"),
        },
        {
            to: "/user-management",
            label: t("usuarios"),
            icon: UsersIcon,
            roles: ["admin"],
            tip: t("gestion_usuarios"),
        },
        {
            to: "/chat",
            label: t("chat"),
            icon: MessageSquareText,
            roles: ["admin", "soporte", "usuario"],
            tip: t("abrir_chat"),
            isChat: true,
        },
        {
            to: "/intentos-fallidos",
            label: t("intentos_fallidos"),
            icon: BarChart2,
            roles: ["admin"],
            tip: t("intents_no_reconocidos"),
        },

        // ⬇️ Enlace temporal solo en dev y para rol admin (no afecta producción)
        ...(IS_DEV
            ? [
                {
                    to: "/dev/auth-test",
                    label: "Auth Test (dev)",
                    icon: Cog,
                    roles: ["admin"],
                    tip: "Pruebas de refresh/cookies",
                },
            ]
            : []),
    ];

    const canSee = (l) => !l.roles || l.roles.includes(role);

    return (
        <>
            <aside className="h-screen w-64 bg-gray-900 text-white flex flex-col justify-between">
                <div className="p-6">
                    {/* Brand / Home */}
                    <div className="flex items-center gap-3 mb-4">
                        <Link to="/" className="shrink-0" aria-label={t("ir_inicio")}>
                            <img
                                src={AVATAR}
                                onError={(e) => {
                                    e.currentTarget.src = "/bot-avatar.png";
                                }}
                                alt={t("inicio")}
                                className="w-10 h-10 rounded-lg object-contain bg-white/10 p-1"
                                loading="eager"
                            />
                        </Link>
                        <div className="flex-1">
                            <Link to="/" className="text-lg font-bold hover:underline">
                                Chatbot Tutor Virtual
                            </Link>
                            <div className="text-xs text-white/70">{t("panel_administracion")}</div>
                        </div>

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
                                    <Link
                                        to={c.to}
                                        className="hover:underline inline-flex items-center gap-1"
                                    >
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
                        <h2 className="text-sm font-semibold">{t("bienvenido")}</h2>
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
                                <span>
                                    {t("rol")}: {user.rol}
                                </span>
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

                {/* Config + Header actions */}
                <div className="p-6 flex items-center justify-between gap-2">
                    {/* Botón de configuración */}
                    <IconTooltip label={t("configuracion")} side="top">
                        <button
                            onClick={() => setOpenSettings(true)}
                            className="inline-flex items-center gap-2 px-3 py-2 rounded bg-white/10 hover:bg-white/20"
                            aria-label={t("configuracion")}
                            type="button"
                        >
                            <Cog size={16} /> {t("configuracion_corta")}
                        </button>
                    </IconTooltip>

                    {/* Botones de cabecera: idioma, tema, salir */}
                    <div className="header-actions flex items-center gap-2 justify-end">
                        <LanguageSelector />
                        <ThemeToggle />

                        {/* 🔐 Logout consistente con cookie httpOnly + limpiar Authorization */}
                        <LogoutButton confirm className="ml-1" />
                    </div>
                </div>

                {/* ⬇️ Bloque dev temporal (footer del aside): visible solo en dev y admin */}
                {IS_DEV && role === "admin" && (
                    <div className="px-6 pb-5">
                        <Link
                            to="/dev/auth-test"
                            className="px-2 py-1 text-xs rounded bg-gray-800 text-white hover:bg-gray-700 inline-flex items-center gap-2"
                        >
                            <Cog className="w-3.5 h-3.5" />
                            Dev Auth Test
                        </Link>
                    </div>
                )}
            </aside>

            {/* Panel de Configuración */}
            <SettingsPanel
                open={openSettings}
                onClose={() => setOpenSettings(false)}
                isAuthenticated={isAuthenticated}
                onLogout={logout} // mantiene compat con tu SettingsPanel
                onCloseChat={() => window.dispatchEvent(new CustomEvent("chat:close"))}
                onLanguageChange={(lang) =>
                    window.dispatchEvent(new CustomEvent("app:lang", { detail: { lang } }))
                }
            />
        </>
    );
};

export default Header;
