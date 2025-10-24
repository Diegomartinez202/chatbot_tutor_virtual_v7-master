/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
        "./public/**/*.html"
    ],
    darkMode: "class",
    safelist: ["dark", "high-contrast"], // ✅ Mantiene clases incluso sin uso directo
    theme: {
        extend: {
            colors: {
                primary: "#6366F1",
                secondary: "#10B981",
                accent: "#FBBF24",
            },
            boxShadow: {
                soft: "0 10px 30px rgba(0,0,0,.15)",
            },
        },
    },
    plugins: [],
};