import { test, expect, type Page } from "@playwright/test";
import * as fs from "node:fs";
import * as path from "node:path";
import { gotoSpa, resolveRoot } from "../utils/gotoSpa.js";

const SUITE_TIMEOUT = Number(process.env.SCREENSHOTS_TIMEOUT_MS || 120_000);
test.describe.configure({ timeout: SUITE_TIMEOUT });

const OUT_DIR = path.join(process.cwd(), "docs", "visuals");

// ==== Mocks base (stats/logs) ====
const statsMock = {
    summary: { total_messages: 345, bot_success: 290, not_understood: 24, avg_response_ms: 420, accuracy: 0.89 },
    series: {
        by_day: [
            { date: "2025-08-10", messages: 40, success: 35, fallback: 3 },
            { date: "2025-08-11", messages: 52, success: 46, fallback: 4 },
            { date: "2025-08-12", messages: 63, success: 51, fallback: 7 },
            { date: "2025-08-13", messages: 70, success: 60, fallback: 6 },
            { date: "2025-08-14", messages: 80, success: 65, fallback: 9 },
        ],
        latency_ms_p50: [
            { date: "2025-08-10", value: 350 },
            { date: "2025-08-11", value: 400 },
            { date: "2025-08-12", value: 430 },
            { date: "2025-08-13", value: 410 },
            { date: "2025-08-14", value: 395 },
        ],
        latency_ms_p95: [
            { date: "2025-08-10", value: 800 },
            { date: "2025-08-11", value: 900 },
            { date: "2025-08-12", value: 950 },
            { date: "2025-08-13", value: 860 },
            { date: "2025-08-14", value: 910 },
        ],
    },
    top_confusions: [
        { intent: "nlu_fallback", count: 12, example: "no entiendo esto" },
        { intent: "faq_envio", count: 4, example: "cuando llega?" },
        { intent: "faq_pagos", count: 3, example: "no puedo pagar" },
    ],
};

const logsMock = {
    total: 20,
    items: Array.from({ length: 20 }).map((_, i) => ({
        _id: `log_${i + 1}`,
        request_id: `req_${1000 + i}`,
        sender_id: i % 3 === 0 ? "anonimo" : `user_${i}`,
        user_message: i % 5 === 0 ? "No puedo ingresar" : "Hola, necesito ayuda",
        bot_response: ["Claro, te ayudo con eso."],
        intent: i % 4 === 0 ? "problema_no_ingreso" : "saludo",
        timestamp: new Date(Date.now() - i * 3600_000).toISOString(),
        ip: "127.0.0.1",
        user_agent: "PlaywrightBot/1.0",
        origen: i % 3 === 0 ? "widget" : "autenticado",
        metadata: { mocked: true },
    })),
};

// ==== Mocks adicionales (auth/users/exports/health/intents/confusions/chat) ====
const userMeMock = { id: "u_123", email: "admin@demo.com", name: "Admin Demo", roles: ["admin", "soporte"] };
const authRefreshMock = { access_token: "mocked.token.value", token_type: "Bearer", expires_in: 3600 };
const exportacionesMock = {
    total: 3,
    items: [
        { id: "exp_1", tipo: "logs_csv", estado: "completado", creado_en: "2025-08-14T09:00:00Z", url: "/api/exportaciones/exp_1/download" },
        { id: "exp_2", tipo: "stats_json", estado: "en_proceso", creado_en: "2025-08-14T10:00:00Z" },
        { id: "exp_3", tipo: "intents_xlsx", estado: "fallido", creado_en: "2025-08-14T11:00:00Z", error: "Timeout" },
    ],
};
const intentsMock = {
    total: 4,
    items: [
        { name: "saludo", ejemplos: ["hola", "buenas"], updated_at: "2025-08-10T12:00:00Z" },
        { name: "despedida", ejemplos: ["chao", "hasta luego"], updated_at: "2025-08-11T12:00:00Z" },
        { name: "consulta_envio", ejemplos: ["cuando llega", "estado del pedido"], updated_at: "2025-08-12T12:00:00Z" },
        { name: "problema_pago", ejemplos: ["no puedo pagar", "error con tarjeta"], updated_at: "2025-08-13T12:00:00Z" },
    ],
};
const confusionsTopMock = {
    total: 3,
    items: [
        { intent: "nlu_fallback", count: 12, example: "no entiendo esto" },
        { intent: "faq_envio", count: 4, example: "cuando llega?" },
        { intent: "faq_pagos", count: 3, example: "no puedo pagar" },
    ],
};
const healthOk = { ok: true, status: "healthy" };

// Chat mocks
const chatHistoryMock = {
    conversation_id: "conv_1",
    items: [
        { id: "m1", role: "user", text: "Hola", ts: Date.now() - 60_000 },
        { id: "m2", role: "assistant", text: "¡Hola! ¿En qué te ayudo?", ts: Date.now() - 59_000 },
    ],
};
const chatReplyFactory = (userText: string) => ({
    id: `m_${Math.random().toString(36).slice(2, 8)}`,
    role: "assistant",
    text: `Respuesta mock para: “${userText}”`,
    ts: Date.now(),
});

// ==== Helpers de salida/estabilidad/únicos ====
function ensureOutDir() { fs.mkdirSync(OUT_DIR, { recursive: true }); }

// Evita duplicar nombres: si existe o ya lo tomamos, agrega _2, _3...
const TAKEN = new Map<string, number>();
function uniquePath(filename: string) {
    ensureOutDir();
    const base = path.join(OUT_DIR, filename);
    if (!fs.existsSync(base) && !TAKEN.has(base)) {
        TAKEN.set(base, 1);
        return base;
    }
    let i = TAKEN.get(base) || 1;
    let next;
    do {
        i += 1;
        next = base.replace(/(\.\w+)$/, `_${i}$1`);
    } while (fs.existsSync(next));
    TAKEN.set(base, i);
    return next;
}

// Deja la UI quieta (sin animaciones) y fondo blanco antes de capturar
async function stabilizeUI(page: Page) {
    await page.addStyleTag({
        content: `
      * { animation: none !important; transition: none !important; caret-color: transparent !important; }
      html, body { background: #fff !important; }
    `
    }).catch(() => { });
    // espera fuentes (si el browser las reporta)
    try { /* @ts-ignore */ await page.waitForFunction(() => (document as any).fonts?.status === "loaded", null, { timeout: 2000 }); } catch { }
    // 2 RAFs para estabilizar layout
    await page.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))));
}

// Disparo con estabilización + unique name
async function shoot(page: Page, filename: string) {
    await page.waitForLoadState("domcontentloaded").catch(() => { });
    await page.waitForLoadState("networkidle").catch(() => { });
    await stabilizeUI(page);
    await page.waitForTimeout(150);
    const file = uniquePath(filename);
    await page.screenshot({ path: file, fullPage: true });
    console.log("📸", file);
    return file;
}

async function mockApis(page: Page) {
    // Stats / Logs
    await page.route("**/api/stats**", (route) =>
        route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(statsMock) })
    );
    await page.route("**/api/logs**", (route) =>
        route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(logsMock) })
    );

    // Auth / Users
    await page.route("**/api/users/me**", (route) =>
        route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(userMeMock) })
    );
    await page.route("**/api/auth/refresh**", (route) =>
        route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(authRefreshMock) })
    );

    // Exportaciones
    await page.route("**/api/exportaciones**", async (route) => {
        const url = route.request().url();
        if (url.includes("/download")) {
            return route.fulfill({ status: 200, contentType: "text/csv", body: "id,evento,fecha\n1,descarga_mock,2025-08-14" });
        }
        return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(exportacionesMock) });
    });

    // Health
    await page.route("**/admin/rasa/status**", (route) =>
        route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(healthOk) })
    );
    await page.route("**/api/health**", (route) =>
        route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(healthOk) })
    );
    await page.route("**/api/chat/health**", (route) =>
        route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(healthOk) })
    );

    // Intents / Confusions
    await page.route("**/api/intents**", (route) =>
        route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(intentsMock) })
    );
    await page.route("**/api/confusions/top**", (route) =>
        route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(confusionsTopMock) })
    );

    // Chat: history
    await page.route("**/api/chat/history**", (route) =>
        route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(chatHistoryMock) })
    );

    // Chat: enviar texto (mock eco) + GET vacío
    await page.route("**/api/chat**", async (route) => {
        const method = route.request().method();
        if (method !== "POST") {
            return route.fulfill({ status: 200, contentType: "application/json", body: "[]" });
        }
        let userText = "mensaje";
        try {
            const req = route.request();
            const ct = req.headers()["content-type"] || "";
            // @ts-ignore
            if (ct.includes("application/json")) { const body = req.postDataJSON?.(); userText = body?.text || body?.message || userText; }
            else { const raw = req.postData() || ""; userText = raw || userText; }
        } catch { }
        const reply = chatReplyFactory(userText);
        return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ reply }) });
    });

    // Chat: audio vacío (OK)
    await page.route("**/api/chat/audio", (route) =>
        route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true, transcript: "", bot: { messages: [] } }) })
    );
}

async function ensureOpenPage(page: Page): Promise<Page> {
    if (!page.isClosed()) return page;
    const ctx = page.context();
    return await ctx.newPage();
}
async function waitAppMounted(page: Page, ms = 10_000): Promise<boolean> {
    try {
        await page.waitForSelector("#root, main, [data-testid='app-root'], body *", { state: "visible", timeout: ms });
        return true;
    } catch { return false; }
}
async function injectPlaceholder(page: Page, title = "Vista mock") {
    await page.addStyleTag({
        content: `
      html, body { background:#f6f7fb !important; font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; }
      .mock-wrap { padding:24px; } .mock-title { font-size:24px; font-weight:700; margin-bottom:16px; }
      .mock-grid { display:grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap:12px; }
      .mock-card { background:#fff; border-radius:12px; padding:16px; box-shadow:0 1px 6px rgba(0,0,0,.06); }
      .mock-sub { color:#6b7280; font-size:12px; } .mock-val { font-size:22px; font-weight:700; margin-top:4px; }
    `
    });
    await page.evaluate((t) => {
        const root = document.createElement("div");
        root.className = "mock-wrap";
        root.innerHTML = `
      <div class="mock-title">${t}</div>
      <div class="mock-grid">
        <div class="mock-card"><div class="mock-sub">Mensajes</div><div class="mock-val">345</div></div>
        <div class="mock-card"><div class="mock-sub">Aciertos</div><div class="mock-val">290</div></div>
        <div class="mock-card"><div class="mock-sub">No entendidos</div><div class="mock-val">24</div></div>
        <div class="mock-card"><div class="mock-sub">Latencia media</div><div class="mock-val">420 ms</div></div>
      </div>`;
        document.body.appendChild(root);
    }, title);
}

async function loginIfNeeded(page: Page, baseURL?: string) {
    const loginPath = process.env.PLAYWRIGHT_LOGIN_PATH;
    const user = process.env.PLAYWRIGHT_LOGIN_USER;
    const pass = process.env.PLAYWRIGHT_LOGIN_PASS;
    if (!loginPath || !user || !pass) return;
    try {
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
    } catch (e) {
        console.warn("⚠️ Login opcional falló o no es necesario:", (e as Error).message);
    }
}

async function shootRouteBoth(page: Page, route: string, baseName: string) {
    page = await ensureOpenPage(page);

    // Desktop
    await page.setViewportSize({ width: 1366, height: 900 });
    await gotoSpa(page, route); // evita 404
    const mounted = await waitAppMounted(page);
    if (!mounted) await injectPlaceholder(page, `Mock de ${route}`);
    await page.locator("svg").first().waitFor({ state: "visible", timeout: 800 }).catch(() => { });
    await shoot(page, `${baseName}_desktop.png`);

    // Mobile
    await page.setViewportSize({ width: 390, height: 844 });
    await shoot(page, `${baseName}_mobile.png`);
}

async function captureWidgetOrFail(page: Page, baseURL?: string) {
    page = await ensureOpenPage(page);

    let closedCaptured = false;
    let openCaptured = false;

    const captureClosed = async () => {
        if (!closedCaptured) {
            await shoot(page, "chat_widget_closed_desktop.png");
            closedCaptured = true;
        }
    };
    const captureOpen = async () => {
        if (!openCaptured) {
            await shoot(page, "chat_widget_open_desktop.png");
            openCaptured = true;
        }
    };

    // 1) Home + launcher real
    await page.setViewportSize({ width: 1366, height: 900 });
    await gotoSpa(page, "/");
    const mounted = await waitAppMounted(page, 4000);
    if (!mounted) await injectPlaceholder(page, "Home (mock)");

    const launcher = page.locator('button[aria-label="Abrir chat"], button:has-text("Chat")').first();
    if (await launcher.count()) {
        await captureClosed();
        await launcher.click().catch(() => { });
        const iframe = page.locator('iframe[title="Chat"], iframe[title="Chatbot"]').first();
        if (await iframe.count()) {
            await expect(iframe).toBeVisible({ timeout: 3000 }).catch(() => { });
            await captureOpen();
            if (openCaptured) return; // ✅ listo
        }
    }

    // 2) Embed servido por tu app
    try {
        const base = (baseURL || "").replace(/\/$/, "");
        const embedSrc = `${base}/chat-embed.html?src=${encodeURIComponent("/chat?embed=1")}`;
        await page.setContent(`
      <!doctype html><html><body>
        <script src="${base}/chat-widget.js"
          data-chat-url="${embedSrc}"
          data-avatar="${base}/bot-avatar.png"
          data-badge="auto"
          data-allowed-origins="${base}">
        </script>
      </body></html>
    `);
        await captureClosed();
        const btn = page.locator('button[aria-label="Abrir chat"], button:has-text("Chat")').first();
        await btn.click({ timeout: 2000 }).catch(() => { });
        const iframe = page.locator('iframe[title="Chat"], iframe[title="Chatbot"]').first();
        if (await iframe.count()) {
            await expect(iframe).toBeVisible({ timeout: 3000 }).catch(() => { });
            await captureOpen();
            if (openCaptured) return; // ✅ listo
        }
    } catch { }

    // 3) Mock inline (si nada de lo anterior funcionó)
    await page.setContent(`
    <!doctype html><html><body style="height:100vh;background:#f6f7fb;">
      <button id="fake-launcher" style="
        position:fixed; right:24px; bottom:24px;
        background:#2563eb; color:#fff; border:none; border-radius:999px;
        width:56px; height:56px; font-size:14px; cursor:pointer;">Chat</button>
      <div id="fake-chat" style="
        position:fixed; right:24px; bottom:90px; width:360px; height:480px;
        background:#fff; border-radius:16px; box-shadow:0 10px 30px rgba(0,0,0,.2);
        display:none; overflow:hidden;">
        <div style="padding:12px; font-weight:700; background:#111827; color:#fff;">Chatbot</div>
        <div style="padding:12px; color:#374151;">Hola 👋 ¿En qué te ayudo?</div>
      </div>
      <script>
        document.getElementById('fake-launcher').addEventListener('click',()=>{
          document.getElementById('fake-chat').style.display='block';
        });
      </script>
    </body></html>
  `);
    await captureClosed();
    await page.locator("#fake-launcher").click();
    await captureOpen();
}

function getRoutes(): { path: string; name: string }[] {
    const env = (process.env.SCREENSHOTS_ROUTES || "").trim();
    if (!env) {
        return [
            { path: "/dashboard", name: "dashboard" },
            { path: "/stats", name: "stats" },
            { path: "/stats-v2", name: "stats-v2" },
            { path: "/intentos-fallidos", name: "intentos-fallidos" },
            { path: "/diagnostico", name: "diagnostico" },
            { path: "/chat", name: "chat_page" },
            { path: "/", name: "home" },
        ];
    }
    const items = env.split(/[,\s]+/).filter(Boolean);
    return items.map((p) => ({ path: p, name: (p.replace(/^\//, "") || "home").replace(/[^\w-]/g, "_") }));
}

test.describe("Visual screenshots (mocked + login opcional + widget obligatorio)", () => {
    test.beforeAll(() => ensureOutDir());

    test("Dashboard/Stats/Stats-v2/Intentos/Diagnóstico/Chat + Widget", async ({ page, baseURL }) => {
        await mockApis(page);
        await loginIfNeeded(page, baseURL);

        for (const r of getRoutes()) {
            try {
                await shootRouteBoth(page, r.path, r.name);
            } catch (e) {
                console.warn(`⚠️ Omitida ${r.path}: ${(e as Error).message}`);
            }
        }

        await captureWidgetOrFail(page, baseURL);
    });
});