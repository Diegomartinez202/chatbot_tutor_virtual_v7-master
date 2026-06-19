import fs from "node:fs/promises";
import fssync from "node:fs";
import path from "node:path";

const MODE = (process.argv[2] || "archive").toLowerCase(); // "archive" | "purge"
const OUT_DIR = path.join(process.cwd(), "docs", "visuals");
const ARCHIVE_DIR = path.join(OUT_DIR, "_archive");

async function ensureDir(p) {
    await fs.mkdir(p, { recursive: true });
}

async function archiveVisuals() {
    if (!fssync.existsSync(OUT_DIR)) {
        console.log("ℹ️  No existe docs/visuals; nada que archivar.");
        return;
    }
    await ensureDir(ARCHIVE_DIR);
    const stamp = new Date()
        .toISOString()
        .replace(/[:.]/g, "-")
        .replace("T", "_")
        .replace("Z", "");
    const dest = path.join(ARCHIVE_DIR, stamp);
    await ensureDir(dest);

    const entries = await fs.readdir(OUT_DIR, { withFileTypes: true });
    const toMove = entries.filter((e) => e.name !== "_archive");
    if (toMove.length === 0) {
        console.log("ℹ️  docs/visuals está vacío; nada que archivar.");
        return;
    }

    for (const e of toMove) {
        const src = path.join(OUT_DIR, e.name);
        const dst = path.join(dest, e.name);
        await fs.rename(src, dst);
    }
    console.log(`📦 Capturas movidas a ${path.relative(process.cwd(), dest)}`);
}

async function purgeVisuals() {
    if (!fssync.existsSync(OUT_DIR)) {
        console.log("ℹ️  No existe docs/visuals; nada que borrar.");
        return;
    }
    const entries = await fs.readdir(OUT_DIR, { withFileTypes: true });
    for (const e of entries) {
        const p = path.join(OUT_DIR, e.name);
        // Borra TODO incluyendo _archive (purga total)
        await fs.rm(p, { recursive: true, force: true });
    }
    console.log("🗑️  docs/visuals purgado por completo.");
    await ensureDir(OUT_DIR);
}

async function main() {
    if (MODE === "archive") {
        await ensureDir(OUT_DIR);
        await archiveVisuals();
    } else if (MODE === "purge") {
        // No lo usas desde package.json, pero lo dejamos disponible por si acaso.
        await purgeVisuals();
    } else {
        console.error(`Modo no reconocido: ${MODE}. Usa "archive" o "purge".`);
        process.exit(1);
    }
}

main().catch((e) => {
    console.error("❌ Error:", e);
    process.exit(1);
});