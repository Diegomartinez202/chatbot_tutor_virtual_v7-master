/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
        // opcional si previsualizas algo fuera de src:
        "./public/**/*.html"
    ],
    darkMode: "class", // ⬅️ modo oscuro por clase .dark en <html>
    safelist: [
        // para no “purgear” si togglean dinámico
        "dark",
        "high-contrast"
    ],
    theme: {
        extend: {
            colors: {
                primary: "#6366F1",   // Indigo-500
                secondary: "#10B981", // Green-500
                accent: "#FBBF24",    // Yellow-400
            },
            // (opcional) sombras gentiles para UI
            boxShadow: {
                soft: "0 10px 30px rgba(0,0,0,.15)",
            }
        },
    },
    plugins: [
        // si usas formularios o textos ricos:
        // require('@tailwindcss/forms'),
        // require('@tailwindcss/typography'),
    ],
};