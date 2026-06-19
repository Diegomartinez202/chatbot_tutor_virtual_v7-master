// admin_panel_react/src/components/LogoutButton.jsx
import React, { useState } from "react";
import { LogOut } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import IconTooltip from "@/components/ui/IconTooltip";

// 👉 añadidos: usamos tu cliente y helper para limpiar Authorization
import axiosClient, { setAuthToken } from "@/services/axiosClient";
import { STORAGE_KEYS } from "@/lib/constants";

export default function LogoutButton({ confirm = false, className = "" }) {
    const { logout } = useAuth();     // respeta tu contexto (si hace más cosas internas)
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);

    const handleLogout = async () => {
        if (loading) return;
        if (confirm && !window.confirm("¿Cerrar sesión?")) return;

        setLoading(true);
        try {
            // 1) Intenta tu flujo del backend (borra cookie httpOnly)
            await axiosClient.post("/auth/logout").catch(() => { });

            // 2) Limpia access del storage y del header por defecto
            try { localStorage.removeItem(STORAGE_KEYS.accessToken); } catch { }
            setAuthToken(null);

            // 3) Llama a tu logout del contexto (no rompemos negocio)
            await logout?.();
        } catch (_e) {
            // opcional: toast de error
        } finally {
            setLoading(false);
            // redirige a login (o a "/")
            navigate("/login");
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
                <span className="hidden sm:inline">
                    {loading ? "Saliendo…" : "Salir"}
                </span>
            </button>
        </IconTooltip>
    );
}
