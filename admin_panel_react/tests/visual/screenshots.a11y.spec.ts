// admin_panel_react/tests/visual/screenshots.a11y.spec.ts
import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

// === Mocks: evita llamadas reales a tu backend ===
const statsMock = {
    summary: { total_messages: 345, bot_success: 290, not_understood: 24, avg_response_ms: 420, accuracy: 0.89 },
    series: {
        by_day: [
            { date: "2025-08-10", messages: 40, success: 35, fallback: 3 },
            { date: "2025-08-11", messages: 52, success: 46, fallback: 4 },
            { date: "2025-08-12", messages: 63, success: 51, fallback: 7 },
        ],
        latency_ms_p50: [
            { date: "2025-08-10", value: 350 },
            { date: "2025-08-11", value: 400 },
            { date: "2025-08-12", value: 430 },
        ],
        latency_ms_p95: [
            { date: "2025-08-10", value: 800 },
            { date: "2025-08-11", value: 900 },
            { date: "2025-08-12", value: 950 },
        ],
    },
    top_confusions: [
        { intent: "nlu_fallback", count: 12, example: "no entiendo esto" },
        { intent: "faq_envio", count: 4, example: "cuando llega?" },
    ],
};

const logsMock = {
    total: 6,
    items: Array.from({ length: 6 }).map((_, i) => ({
        _id: `log_${i + 1}`,
        request_id: `req_${1000 + i}`,
        sender_id: i % 2 ? "anonimo" : `user_${i}`,
        user_message: i % 3 === 0 ? "No puedo ingresar" : "Hola, necesito ayuda",
        bot_response: ["Claro, te ayudo con eso."],
        intent: i % 2 ? "problema_no_ingreso" : "saludo",
        timestamp: new Date(Date.now() - i * 3600_000).toISOString(),
        ip: "127.0.0.1",
        user_agent: "PlaywrightBot/1.0",
        origen: i % 2 ? "widget" : "autenticado",
        metadata: { mocked: true },
    })),
};

async function mockApis(page: import("@playwright/test").Page) {
    await page.route("**/api/stats**", (route) =>
        route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(statsMock) }),
    );
    await page.route("**/api/logs**", (route) =>
        route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(logsMock) }),
    );
    // Evita posts reales del chat si se monta /chat
    await page.route("**/api/chat", (route) =>
        route.fulfill({ status: 200, contentType: "application/json", body: "[]" }),
    );
}

// Login opcional por ENV
async function loginIfNeeded(page: import("@playwright/test").Page, baseURL?: string) {
    const loginPath = process.env.PLAYWRIGHT_LOGIN_PATH;
    const user = process.env.PLAYWRIGHT_LOGIN_USER;
    const pass = process.env.PLAYWRIGHT_LOGIN_PASS;
    if (!loginPath || !user || !pass) return;

    await page.goto(new URL(loginPath, baseURL || page.url()).toString());
    const userInput = page.locator('input[name="email"], input[name="username"], [data-testid="login-email"]').first();
    const passInput = page.locator('input[type="password"], [data-testid="login-password"]').first();
    const submitBtn = page
        .locator('button[type="submit"], [data-testid="login-submit"], button:has-text("Ingresar"), button:has-text("Login")]')
        .first();

    if (await userInput.count()) await userInput.fill(user);
    if (await passInput.count()) await passInput.fill(pass);
    if (await submitBtn.count()) await submitBtn.click();
    await page.waitForLoadState("networkidle");
}

// Rutas a evaluar
function getRoutes(): string[] {
    const env = (process.env.SCREENSHOTS_ROUTES || "").trim();
    if (env) return env.split(/[,\s]+/).filter(Boolean);
    return ["/dashboard", "/stats", "/stats-v2", "/intentos-fallidos", "/diagnostico", "/chat", "/"];
}

// Chequeo Axe
async function assertNoSeriousOrCritical(page: import("@playwright/test").Page, route: string) {
    const results = await new AxeBuilder({ page }).analyze();
    const bad = results.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
    expect(bad, `Violaciones (serious/critical) en ${route}`).toHaveLength(0);
}

test.describe("A11y (Axe) en vistas principales", () => {
    test("sin issues críticas/serias por vista", async ({ page, baseURL }) => {
        await mockApis(page);
        await loginIfNeeded(page, baseURL);

        for (const route of getRoutes()) {
            await page.goto(route);
            await page.waitForLoadState("domcontentloaded");
            await assertNoSeriousOrCritical(page, route);
        }

        await page.goto("/");
        await assertNoSeriousOrCritical(page, "/");
    });
});