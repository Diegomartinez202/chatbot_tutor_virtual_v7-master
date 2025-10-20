// src/utils/exportCsvHelper.js

function toCsvCell(value) {
    const s = String(value ?? "");
    const needsQuotes = /[",\n]/.test(s);
    const escaped = s.replace(/"/g, '""');
    return needsQuotes ? `"${escaped}"` : escaped;
}

/**
 * Exporta un arreglo de objetos a CSV.
 * - data: Array<Object>
 * - filename: string (por defecto "exportacion.csv")
 * - headers: string[] opcional para forzar orden/columnas
 */
export function exportToCsv(data, filename = "exportacion.csv", headers) {
    if (!Array.isArray(data) || data.length === 0) return;

    const cols = headers && headers.length ? headers : Object.keys(data[0]);
    const lines = [
        cols.join(","),
        ...data.map((row) => cols.map((h) => toCsvCell(row[h])).join(",")),
    ];

    // BOM para Excel (UTF-8)
    const bom = "\uFEFF";
    const csvContent = bom + lines.join("\n");

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.style.display = "none";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    URL.revokeObjectURL(url);
}

// Alias por compatibilidad con otros módulos (si usaban exportCsv)
export const exportCsv = exportToCsv;