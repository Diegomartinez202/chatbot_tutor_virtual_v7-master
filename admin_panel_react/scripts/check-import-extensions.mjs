#!/usr/bin/env node
// scripts/check-import-extensions.mjs
import fs from "node:fs";
import path from "node:path";

const ROOT = process.cwd();
const TARGET_DIR = process.env.IMPORTS_CHECK_DIR || "tests";
const ABS_TARGET = path.resolve(ROOT, TARGET_DIR);
const DRY_RUN = !process.argv.includes("--fix");

const ARTIFACTS_DIR = path.resolve(ROOT, "tests/__artifacts__");
const REPORT_MD = path.join(ARTIFACTS_DIR, "imports-report.md");

const IGNORE_DIRS = new Set([
    "node_modules",
    ".git",
    "playwright-report",
    "dist",
    "build",
    "coverage",
    "__artifacts__",
]);

const TS_LIKE = new Set([".ts", ".tsx", ".mts", ".cts"]);
const JS_LIKE = new Set([".js", ".mjs", ".cjs"]);
const ALLOWED_OTHER = new Set([".json"]);
const RELATIVE_PREFIXES = ["./", "../"];

const color = {
    gray: (s) => `\x1b[90m${s}\x1b[0m`,
    red: (s) => `\x1b[31m${s}\x1b[0m`,
    yellow: (s) => `\x1b[33m${s}\x1b[0m`,
    green: (s) => `\x1b[32m${s}\x1b[0m`,
    cyan: (s) => `\x1b[36m${s}\x1b[0m`,
    bold: (s) => `\x1b[1m${s}\x1b[0m`,
};

const offenders = [];
let filesScanned = 0;
let filesChanged = 0;

ensureDir(ARTIFACTS_DIR);

function ensureDir(dir) {
    try { fs.mkdirSync(dir, { recursive: true }); } catch { }
}

function walk(dir) {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const e of entries) {
        if (IGNORE_DIRS.has(e.name)) continue;
        const p = path.join(dir, e.name);
        if (e.isDirectory()) {
            walk(p);
        } else if (
            e.isFile() &&
            !e.name.endsWith(".d.ts") &&
            (e.name.endsWith(".ts") || e.name.endsWith(".tsx"))
        ) {
            scanFile(p);
        }
    }
}

const patterns = [
    { re: /import\s+[^'"]*?\sfrom\s+(['"])([^'"]+)\1/g, kind: "import-from" },
    { re: /import\s+(['"])([^'"]+)\1/g, kind: "import-bare" },
    { re: /export\s+[^'"]*?\sfrom\s+(['"])([^'"]+)\1/g, kind: "export-from" },
    { re: /import\(\s*(['"])([^'"]+)\1\s*\)/g, kind: "dynamic-import" },
];

function isRelative(spec) {
    return RELATIVE_PREFIXES.some((p) => spec.startsWith(p));
}

function resolveCandidate(fileDir, spec, exts) {
    for (const ext of exts) {
        const asFile = path.resolve(fileDir, spec + ext);
        if (fs.existsSync(asFile)) return { type: "file", path: asFile, ext };
    }
    for (const ext of exts) {
        const asIndex = path.resolve(fileDir, spec, "index" + ext);
        if (fs.existsSync(asIndex)) return { type: "index", path: asIndex, ext };
    }
    return null;
}

function suggestFix(filePath, fileDir, spec) {
    if (/^[a-zA-Z]+:/.test(spec)) return null; // http:, data:, etc.
    if (!isRelative(spec)) return null;

    const ext = path.extname(spec);
    if (JS_LIKE.has(ext) || ALLOWED_OTHER.has(ext)) return null;

    if (TS_LIKE.has(ext)) {
        const without = spec.slice(0, -ext.length);
        return { newSpec: without + ".js", reason: `Reemplazar ${ext} → .js` };
    }

    if (ext === "") {
        const cand = resolveCandidate(fileDir, spec, [".ts", ".tsx"]);
        if (cand) {
            if (cand.type === "file") {
                return { newSpec: spec + ".js", reason: "Agregar .js (archivo TS/TSX detectado)" };
            } else if (cand.type === "index") {
                return { newSpec: path.posix.join(spec, "index.js"), reason: "Agregar /index.js (index TS/TSX detectado)" };
            }
        }
        return { newSpec: spec + ".js", reason: "Agregar .js (regla NodeNext)" };
    }
    return null; // css/svg/png/etc.
}

function scanFile(filePath) {
    filesScanned++;
    let source = fs.readFileSync(filePath, "utf8");
    let changed = false;
    const problems = [];

    for (const { re, kind } of patterns) {
        re.lastIndex = 0;
        source = source.replace(re, (full, _q, spec) => {
            const fileDir = path.dirname(filePath);
            const fix = suggestFix(filePath, fileDir, spec);
            if (fix) {
                problems.push({ kind, spec, fix, filePath });
                changed = true;
                return full.replace(spec, fix.newSpec);
            }
            return full;
        });
    }

    if (problems.length) offenders.push(...problems);
    if (!DRY_RUN && changed) {
        fs.writeFileSync(filePath, source, "utf8");
        filesChanged++;
        console.log(color.green(`✔ FIXED`), path.relative(ROOT, filePath));
    }
}

function mdEscape(s) {
    return String(s).replace(/\|/g, "\\|");
}

function writeMarkdownReport() {
    const now = new Date();
    const lines = [];
    lines.push(`# Imports Report`);
    lines.push(``);
    lines.push(`**Fecha:** ${now.toISOString()}`);
    lines.push(`**Modo:** ${DRY_RUN ? "CHECK (sin cambios)" : "FIX (cambios aplicados)"}`);
    lines.push(`**Directorio escaneado:** \`${path.relative(ROOT, ABS_TARGET) || "."}\``);
    lines.push(`**Archivos escaneados:** ${filesScanned}`);
    lines.push(`**Imports detectados para corregir:** ${offenders.length}`);
    if (!DRY_RUN) lines.push(`**Archivos modificados:** ${filesChanged}`);
    lines.push(``);

    if (offenders.length === 0) {
        lines.push(`✅ No se encontraron imports relativos sin **.js**. ¡Todo OK!`);
    } else {
        lines.push(`| Archivo | Tipo | Desde | → | Sugerido | Motivo |`);
        lines.push(`|---|---|---|---|---|---|`);
        for (const p of offenders) {
            const rel = path.relative(ROOT, p.filePath);
            lines.push(
                `| \`${mdEscape(rel)}\` | \`${mdEscape(p.kind)}\` | \`${mdEscape(p.spec)}\` | → | \`${mdEscape(
                    p.fix.newSpec
                )}\` | ${mdEscape(p.fix.reason)} |`
            );
        }
    }
    lines.push(``);
    fs.writeFileSync(REPORT_MD, lines.join("\n"), "utf8");
}

function printConsoleSummary() {
    console.log(color.cyan(`\n🔎 Import Check — NodeNext (.js en imports relativos)`));
    console.log(color.gray(`Base: ${path.relative(ROOT, ABS_TARGET) || "."}`));
    console.log(color.gray(`Archivos escaneados: ${filesScanned}`));
    console.log(color.gray(`Reporte: ${path.relative(ROOT, REPORT_MD)}`));

    if (!offenders.length) {
        console.log(color.green(`\n✅ Todo OK: no se encontraron imports relativos sin ".js".\n`));
        process.exit(0);
    }

    console.log(color.yellow(`\n⚠ Se encontraron ${offenders.length} imports a corregir.`));
    if (DRY_RUN) {
        console.log(color.yellow(`\nSugerencias volcadas en ${path.relative(ROOT, REPORT_MD)}.`));
        console.log(color.yellow(`Ejecuta con ${color.bold("--fix")} para aplicar cambios.`));
        process.exitCode = 1; // hace fallar "npm run check:imports" si hay pendientes
    } else {
        console.log(color.cyan(`\n🛠 Cambios aplicados en ${filesChanged} archivo(s).`));
        console.log(color.gray(`Detalle en: ${path.relative(ROOT, REPORT_MD)}\n`));
        process.exit(0);
    }
}

// Main
if (!fs.existsSync(ABS_TARGET)) {
    console.error(color.red(`No existe el directorio objetivo: ${ABS_TARGET}`));
    process.exit(1);
}
walk(ABS_TARGET);
writeMarkdownReport();
printConsoleSummary();