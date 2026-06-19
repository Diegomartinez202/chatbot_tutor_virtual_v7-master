// Intenta cargar primero la variante Zajuna y cae por defecto al genérico.
import fs from "fs";
import path from "path";


export function loadBotResponse() {
    const base = path.resolve(process.cwd(), "tests/e2e/fixtures");
    const zajuna = path.join(base, "bot.response.cards.zajuna.json");
    const generic = path.join(base, "bot.response.cards.json");


    if (fs.existsSync(zajuna)) {
        return JSON.parse(fs.readFileSync(zajuna, "utf8"));
    }
    return JSON.parse(fs.readFileSync(generic, "utf8"));
}