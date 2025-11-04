// src/components/Sidebar.jsx
import { NavLink } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import {
    LayoutDashboard,
    User as UserIcon,
    Brain,
    BarChart,
    FlaskConical,
    FileText,
    Users,
    Download,
    Bug,
    PanelLeft,
} from "lucide-react";
import IconTooltip from "@/components/ui/IconTooltip";
import { useTranslation } from "react-i18next";

const ENABLE_INTENTOS_FALLIDOS = true;

const Sidebar = () => {
    const { user } = useAuth();
    const role = user?.rol || "usuario";
    const { t } = useTranslation(); // defaultNS = common

    const menuSections = {
        Cuenta: [
            { to: "/dashboard", label: t("dashboard"), icon: LayoutDashboard, roles: ["admin", "soporte", "usuario"] },
            // "Perfil" no está en el JSON; dejamos literal para NO romper
            { to: "/profile", label: "Perfil", icon: UserIcon, roles: ["admin", "soporte", "usuario"] },
        ],
        IA: [
            { to: "/intents", label: t("intents"), icon: Brain, roles: ["admin"] },
            { to: "/stadisticas-logs", label: t("estadisticas"), icon: BarChart, roles: ["admin"] },
            // Mantengo tu ruta original "admin/diagnostico"
            { to: "/admin/diagnostico", label: t("pruebas"), icon: FlaskConical, roles: ["admin", "soporte"] },
        ],
        Administración: [
            { to: "/logs", label: t("logs"), icon: FileText, roles: ["admin", "soporte"] },
            { to: "/user-management", label: t("usuarios"), icon: Users, roles: ["admin"] },
            { to: "/exportaciones", label: t("exportaciones"), icon: Download, roles: ["admin"] },
            // Oculto por defecto hasta que exista la ruta:
            { to: "/intentos-fallidos", label: t("intentos_fallidos"), icon: Bug, roles: ["admin"], hidden: !ENABLE_INTENTOS_FALLIDOS },
        ],
    };

    const canSee = (link) => (!link.roles || link.roles.includes(role)) && !link.hidden;

    return (
        <aside className="bg-gray-900 text-white w-64 min-h-screen p-4 space-y-4">
            <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                <PanelLeft size={22} /> Panel Admin
            </h2>

            {Object.entries(menuSections).map(([section, links]) => (
                <div key={section}>
                    <p className="text-gray-400 uppercase text-sm mt-6 px-4">{section}</p>
                    {links.filter(canSee).map(({ to, label, icon: Icon }) => (
                        <IconTooltip key={to} label={label} side="right">
                            <NavLink
                                to={to}
                                className={({ isActive }) =>
                                    [
                                        "flex items-center gap-2 py-2 px-4 rounded hover:bg-gray-700 transition-colors",
                                        isActive ? "bg-gray-800 font-semibold" : "",
                                    ].join(" ")
                                }
                            >
                                <Icon size={18} />
                                <span>{label}</span>
                            </NavLink>
                        </IconTooltip>
                    ))}
                </div>
            ))}
        </aside>
    );
};

export default Sidebar;
