import type { Page, Locator } from "@playwright/test";

/** Navega a `path` en SPA evitando 404 directos (server sin fallback). */
export async function gotoSpa(page: Page, path: string) {
    const resp = await page.goto(path, { waitUntil: "domcontentloaded" });
    if (resp && resp.status() === 404) {
        await page.goto("/", { waitUntil: "domcontentloaded" });
        await page.evaluate((p) => history.pushState({}, "", p), path);
        await page.reload({ waitUntil: "domcontentloaded" });
    }
}

/** Devuelve un locator raíz estable, o <body> si no hay testids. */
export async function resolveRoot(page: Page): Promise<Locator> {
    const candidates = [
        "[data-testid=app-root]",
        "[data-testid=chat-root]",
        "#root",
        "main",
        "body",
    ];
    for (const sel of candidates) {
        if ((await page.locator(sel).count()) > 0) return page.locator(sel);
    }
    return page.locator("body");
}