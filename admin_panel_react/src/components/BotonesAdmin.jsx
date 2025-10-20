// src/components/BotonesAdmin.jsx
import React, { useState } from "react";
import { useAdminActions } from "@/services/useAdminActions";
import { Button } from "@/components/ui"; // ← barrel
import toast from "react-hot-toast";
import { useAuth } from "@/context/AuthContext";
import { BrainCog, Upload, RefreshCw, Download, CheckCircle, XCircle, Bot, Search, ListChecks, MessagesSquare } from "lucide-react";
import FiltrosFecha from "./FiltrosFecha";
import IconTooltip from "@/components/ui/IconTooltip";
import { Link } from "react-router-dom";
import TrainBotButton from "@/components/TrainBotButton";

function BotonesAdmin() {
    const { trainMutation, uploadMutation, restartMutation, exportMutation } = useAdminActions();
    const { user } = useAuth();

    const allowed = user?.rol === "admin" || user?.rol === "soporte";
    if (!allowed) return null;

    const [desde, setDesde] = useState("");
    const [hasta, setHasta] = useState("");

    const handleTrain = () =>
        trainMutation.mutate(null, {
            onSuccess: () =>
                toast.success("Bot entrenado correctamente", {
                    icon: <CheckCircle className="w-4 h-4" />,
                }),
            onError: () =>
                toast.error("Error al entrenar el bot", {
                    icon: <XCircle className="w-4 h-4" />,
                }),
        });

    const handleUpload = () =>
        uploadMutation.mutate(null, {
            onSuccess: () =>
                toast.success("Intents subidos correctamente", {
                    icon: <CheckCircle className="w-4 h-4" />,
                }),
            onError: () =>
                toast.error("Error al subir intents", {
                    icon: <XCircle className="w-4 h-4" />,
                }),
        });

    const handleRestart = () =>
        restartMutation.mutate(null, {
            onSuccess: () =>
                toast.success("Servidor reiniciado", {
                    icon: <RefreshCw className="w-4 h-4" />,
                }),
            onError: () =>
                toast.error("Error al reiniciar servidor", {
                    icon: <XCircle className="w-4 h-4" />,
                }),
        });

    const handleExport = () =>
        exportMutation.mutate(
            { desde, hasta },
            {
                onSuccess: () =>
                    toast.success("Export en curso/descargado", {
                        icon: <Download className="w-4 h-4" />,
                    }),
                onError: () =>
                    toast.error("Error al exportar CSV", {
                        icon: <XCircle className="w-4 h-4" />,
                    }),
            }
        );

    return (
        <>
            <FiltrosFecha desde={desde} hasta={hasta} setDesde={setDesde} setHasta={setHasta} />

            <div className="flex flex-wrap gap-4">
                {/* Entrenar (con hook) */}
                <IconTooltip label="Reentrenar modelo con nuevos intents" side="top">
                    <Button
                        onClick={handleTrain}
                        disabled={trainMutation.isPending}
                        className="flex items-center gap-2"
                        aria-label="Entrenar bot"
                        type="button"
                    >
                        <BrainCog className="w-5 h-5" />
                        {trainMutation.isPending ? "Entrenando..." : "Entrenar Bot"}
                    </Button>
                </IconTooltip>

                {/* Entrenar alternativo con componente standalone */}
                <IconTooltip label="Reentrenar (alternativo)" side="top">
                    <span>
                        {/* Puedes pasar mode="ci" branch="main" si quieres disparar CI desde aquí */}
                        <TrainBotButton />
                    </span>
                </IconTooltip>

                <IconTooltip label="Cargar intents desde archivo o panel" side="top">
                    <Button
                        onClick={handleUpload}
                        disabled={uploadMutation.isPending}
                        className="flex items-center gap-2"
                        aria-label="Subir intents"
                        type="button"
                    >
                        <Upload className="w-5 h-5" />
                        {uploadMutation.isPending ? "Subiendo..." : "Subir Intents"}
                    </Button>
                </IconTooltip>

                <IconTooltip label="Reiniciar servidor de backend" side="top">
                    <Button
                        onClick={handleRestart}
                        disabled={restartMutation.isPending}
                        className="flex items-center gap-2"
                        aria-label="Reiniciar servidor"
                        type="button"
                    >
                        <RefreshCw className="w-5 h-5" />
                        {restartMutation.isPending ? "Reiniciando..." : "Reiniciar"}
                    </Button>
                </IconTooltip>

                <IconTooltip label="Exportar logs del chatbot por rango de fechas" side="top">
                    <Button
                        onClick={handleExport}
                        disabled={exportMutation.isPending}
                        className="flex items-center gap-2"
                        aria-label="Exportar CSV de logs"
                        type="button"
                    >
                        <Download className="w-5 h-5" />
                        {exportMutation.isPending ? "Exportando..." : "Exportar CSV"}
                    </Button>
                </IconTooltip>

                {/* Navegación rápida */}
                <IconTooltip label="Crear intent (ruta clásica /intents)" side="top">
                    <Link to="/intents">
                        <Button variant="outline" className="inline-flex items-center gap-2">
                            <MessagesSquare className="w-5 h-5" />
                            Crear Intent
                        </Button>
                    </Link>
                </IconTooltip>

                <IconTooltip label="Crear intent (editor avanzado /intents/new)" side="top">
                    <Link to="/intents/new">
                        <Button variant="outline" className="inline-flex items-center gap-2">
                            <MessagesSquare className="w-5 h-5" />
                            Crear (Editor)
                        </Button>
                    </Link>
                </IconTooltip>

                <IconTooltip label="Buscar intents con filtros" side="top">
                    <Link to="/intents/buscar">
                        <Button variant="outline" className="inline-flex items-center gap-2">
                            <Search className="w-5 h-5" />
                            Buscar Intents
                        </Button>
                    </Link>
                </IconTooltip>

                <IconTooltip label="Listado de intents" side="top">
                    <Link to="/intents/list">
                        <Button variant="outline" className="inline-flex items-center gap-2">
                            <ListChecks className="w-5 h-5" />
                            Lista de Intents
                        </Button>
                    </Link>
                </IconTooltip>

                {/* Alias /chat */}
                <IconTooltip label="Abrir chat (alias /chat)" side="top">
                    <Link to="/chat">
                        <Button variant="outline" className="inline-flex items-center gap-2">
                            <Bot className="w-5 h-5" />
                            Ir al Chat
                        </Button>
                    </Link>
                </IconTooltip>
            </div>
        </>
    );
}

export default BotonesAdmin;