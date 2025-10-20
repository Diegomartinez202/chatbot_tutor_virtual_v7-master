// src/components/ExportIntentsButton.jsx
import { Button } from "@/components/ui/button";
import axiosClient from "@/services/axiosClient"; // ✅ cambio aplicado
import IconTooltip from "@/components/ui/IconTooltip";
import { Download } from "lucide-react";
import { toast } from "react-hot-toast";

function ExportIntentsButton() {
    const handleExport = async () => {
        try {
            const res = await axiosClient.get("/admin/intents/export", {
                responseType: "blob",
            });

            const blob = new Blob([res.data], { type: "text/csv;charset=utf-8" });
            const url = window.URL.createObjectURL(blob);

            const a = document.createElement("a");
            a.href = url;
            const date = new Date().toISOString().slice(0, 10);
            a.download = `intents_exportados_${date}.csv`; // o .json si el backend cambia
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);

            toast.success("Intents exportados correctamente", {
                icon: <Download className="w-4 h-4" />,
            });
        } catch (error) {
            console.error(error);
            toast.error("Error al exportar intents");
        }
    };

    return (
        <IconTooltip label="Exportar intents del chatbot a CSV" side="top">
            <Button onClick={handleExport} variant="outline" type="button" className="inline-flex items-center gap-2">
                <Download className="w-4 h-4" />
                Exportar Intents
            </Button>
        </IconTooltip>
    );
}

export default ExportIntentsButton;