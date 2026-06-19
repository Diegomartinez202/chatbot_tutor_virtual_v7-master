// src/components/ExportLogsButton.jsx
import React from "react";
import axiosClient from "@/services/axiosClient"; // ✅ corregido
import { Button } from "@/components/ui/button";
import IconTooltip from "@/components/ui/IconTooltip";
import { Download } from "lucide-react";
import { toast } from "react-hot-toast";

function ExportLogsButton() {
    const exportarLogs = async () => {
        try {
            const res = await axiosClient.get("/admin/logs/export", {
                responseType: "blob",
            });

            const blob = new Blob([res.data], { type: "text/csv;charset=utf-8" });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `logs_exportados_${new Date().toISOString().slice(0, 10)}.csv`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);

            toast.success("CSV exportado", {
                icon: <Download className="w-4 h-4" />,
            });
        } catch (error) {
            toast.error("Error al exportar logs");
            console.error("Error al exportar logs:", error);
        }
    };

    return (
        <IconTooltip label="Exportar registros del chatbot a CSV" side="top">
            <Button
                onClick={exportarLogs}
                className="bg-purple-600 hover:bg-purple-700 text-white px-3 py-2"
                type="button"
            >
                <Download className="w-4 h-4 mr-2" />
                Exportar Logs a CSV
            </Button>
        </IconTooltip>
    );
}

export default ExportLogsButton;