// build-tailwind.js
/**
 * 🔧 Compila Tailwind y tus estilos personalizados
 * y los deja listos en /static/css/index.css
 */

const fs = require("fs");
const path = require("path");
const postcss = require("postcss");
const tailwindcss = require("tailwindcss");
const autoprefixer = require("autoprefixer");

// 🧭 Rutas base
const input = path.join(__dirname, "../../admin_panel_react/src/styles/index.css");
const outputDir = path.join(__dirname, "static/css");
const outputFile = path.join(outputDir, "index.css");

// Crear carpeta destino si no existe
if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
}

// Leer archivo CSS base
fs.readFile(input, (err, css) => {
    if (err) throw err;

    console.log("🌀 Compilando Tailwind...");

    postcss([tailwindcss, autoprefixer])
        .process(css, { from: input, to: outputFile })
        .then((result) => {
            fs.writeFileSync(outputFile, result.css);
            console.log(`✅ CSS generado correctamente en: ${outputFile}`);

            if (result.map) {
                fs.writeFileSync(outputFile + ".map", result.map.toString());
            }
        })
        .catch((error) => {
            console.error("❌ Error al compilar Tailwind:", error);
        });
});