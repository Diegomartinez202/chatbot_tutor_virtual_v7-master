// src/components/examples/BackButtonDemo.jsx
import React from "react";
import BackButton from "@/components/BackButton";
import assets from "@/config/assets";

export default function BackButtonDemo() {
    return (
        <div className="flex flex-col gap-4 p-6 bg-gray-50 dark:bg-gray-900 min-h-screen">
            <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">
                Demo de BackButton con animaciones de Tooltip
            </h2>

            {/* FadeIn por defecto */}
            <BackButton
                to="/home"
                label="Volver a Home"
                tooltip="Tooltip FadeIn (default)"
            />

            {/* FadeOut */}
            <BackButton
                to="/dashboard"
                label="Ir al Dashboard"
                tooltip="Tooltip FadeOut"
                animation="fadeOut"
                variant="secondary"
            />

            {/* Pulse */}
            <BackButton
                to="/settings"
                label="Configuración"
                tooltip="Tooltip Pulse"
                animation="pulse"
                variant="outline"
            />

            {/* Bounce */}
            <BackButton
                to="/profile"
                label="Mi Perfil"
                tooltip="Tooltip Bounce"
                animation="bounce"
                variant="ghost"
            />
        </div>
    );
}