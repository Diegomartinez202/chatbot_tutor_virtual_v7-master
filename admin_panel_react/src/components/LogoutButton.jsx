import React, { useState } from "react";
import { LogOut } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import IconTooltip from "@/components/ui/IconTooltip";

export default function LogoutButton({ confirm = false, className = "" }) {
    const { logout } = useAuth();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);

    const handleLogout = async () => {
        if (loading) return;
        if (confirm && !window.confirm("¿Cerrar sesión?")) return;

        setLoading(true);
        try {
            await logout?.();
        } catch (e) {
            // Opcional: notificar error con tu sistema de toasts
            // console.error(e);
        } finally {
            setLoading(false);
            navigate("/"); // compat: vuelve al login/inicio
        }
    };

    return (
        <IconTooltip label="Cerrar sesión" side="top">
            <button
                type="button"
                onClick={handleLogout}
                className={
                    "inline-flex items-center gap-2 px-3 py-2 rounded bg-red-600 text-white hover:bg-red-700 " +
                    "focus:outline-none focus:ring-2 focus:ring-red-300 " +
                    "disabled:opacity-60 disabled:cursor-not-allowed " +
                    className
                }
                aria-label="Cerrar sesión"
                disabled={loading}
            >
                <LogOut className="w-4 h-4" aria-hidden="true" />
                <span className="hidden sm:inline">{loading ? "Saliendo…" : "Salir"}</span>
            </button>
        </IconTooltip>
    );
}