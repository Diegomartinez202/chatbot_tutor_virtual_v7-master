// src/utils/formatDate.js
/**
 * Convierte una fecha a dd/mm/yyyy (ES-CO).
 * { withTime: true } para incluir hora (HH:mm).
 */
export function formatDate(dateInput, options = {}) {
    if (!dateInput) return "";
    const date = new Date(dateInput);
    if (isNaN(date)) return "";

    const { withTime = true } = options;

    const dateStr = date.toLocaleDateString("es-CO", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
    });

    if (!withTime) return dateStr;

    const timeStr = date.toLocaleTimeString("es-CO", {
        hour: "2-digit",
        minute: "2-digit",
    });

    return `${dateStr} ${timeStr}`;
}