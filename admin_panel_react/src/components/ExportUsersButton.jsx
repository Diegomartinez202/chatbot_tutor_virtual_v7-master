// src/components/ExportUserButton.jsx
import { saveAs } from "file-saver";
import axiosClient from "@/services/axiosClient";
import { Button } from "@/components/ui/button";
import IconTooltip from "@/components/ui/IconTooltip";
import { Download, XCircle } from "lucide-react";
import { toast } from "react-hot-toast";

function filenameWithStamp(prefix = "usuarios", ext = "csv") {
    const d = new Date();
    const pad = (n) => String(n).padStart(2, "0");
    const stamp = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}_${pad(d.getHours())}-${pad(d.getMinutes())}-${pad(d.getSeconds())}`;
    return `${prefix}_${stamp}.${ext}`;
}

const ExportUserButton = () => {
    const exportarUsuarios = async () => {
        try {
            const res = await axiosClient.get("/admin/users/export", {
                responseType: "blob",
            });

            const blob = new Blob([res.data], { type: "text/csv;charset=utf-8;" });
            saveAs(blob, filenameWithStamp());

            toast.success("Usuarios exportados correctamente", {
                icon: <Download className="w-4 h-4" />,
            });
        } catch (error) {
            console.error("Error exportando usuarios:", error);
            toast.error("Error al exportar usuarios", {
                icon: <XCircle className="w-4 h-4" />,
            });
        }
    };

    return (
        <IconTooltip label="Exportar usuarios a CSV" side="top">
            <Button onClick={exportarUsuarios} className="inline-flex items-center gap-2" type="button">
                <Download className="w-4 h-4" />
                Exportar Usuarios (CSV)
            </Button>
        </IconTooltip>
    );
};

export default ExportUserButton;