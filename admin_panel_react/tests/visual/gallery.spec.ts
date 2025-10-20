// admin_panel_react/tests/visual/gallery.spec.ts
import { test, expect, type Page, type Locator } from "@playwright/test";
import { routeZajuna } from "../e2e/mocks/zajuna.route.js";      // ← ESM con .js
import { gotoSpa } from "../utils/gotoSpa.js";                    // ← evita 404

const CHAT_PATH = process.env.CHAT_PATH || "/chat";

// --- mocks mínimos adicionales para que el Chat monte sin backend real ---
async function mockChatBasics(page: Page) {
    // health
    const healthOk = { ok: true, status: "healthy" };
    await page.route("**/api/health**", (r) =>
        r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(healthOk) })
    );
    await page.route("**/api/chat/health**", (r) =>
        r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(healthOk) })
    );
    // history vacío
    await page.route("**/api/chat/history**", (r) =>
        r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ conversation_id: "conv_1", items: [] }) })
    );
}

// Mock para /api/chat/audio: 1ª llamada OK, 2ª llamada error 413
function mockAudioSequence() {
    let calls = 0;
    return async function (route: any) {
        if (route.request().method() !== "POST") return route.fallback();
        calls++;
        if (calls === 1) {
            const ok = { messages: [{ type: "text", text: "Audio recibido (lang=es-CO, persona=aprendiz)." }] };
            return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(ok) });
        }
        const err = { detail: "Archivo demasiado grande" };
        return route.fulfill({ status: 413, contentType: "application/json", body: JSON.stringify(err) });
    };
}

// Localizador robusto del “chat root”
async function getChatRoot(page: Page): Promise<Locator> {
    const candidates = [
        "[data-testid=chat-root]",
        "[data-testid=chat]",
        "[data-testid=chatui]",
        "#chat-root",
        "#root [data-testid='chat-root']",
        "main [data-testid='chat-root']",
    ];
    for (const sel of candidates) {
        const loc = page.locator(sel);
        if (await loc.count()) return loc.first();
    }
    // Último recurso: si existe el input del mensaje, usa su contenedor
    const input = page.getByPlaceholder(/escribe tu mensaje/i);
    if (await input.count()) {
        const parent = input.locator("xpath=ancestor-or-self::*[1]");
        return parent;
    }
    // Falla explícita con ayuda
    throw new Error(
        "No encontré el root del chat. Revisa que tu componente tenga data-testid='chat-root' o ajusta los selectores en getChatRoot()."
    );
}

test.describe("Galería completa – bienvenida → cards → audio OK → audio error → FAQs/certificados", () => {
    test("recorrido y capturas", async ({ page }) => {
        // mocks para que la SPA y el chat monten
        await mockChatBasics(page);
        await routeZajuna(page);                         // mock conversa (cards + FAQs + cursos)
        await page.route("**/api/chat/audio", mockAudioSequence()); // mock audio secuencial

        // 1) Bienvenida
        await gotoSpa(page, `${CHAT_PATH}?lang=es-CO&persona=aprendiz`);  // ← evita 404 directo
        await page.waitForLoadState("networkidle");
        const chat = await getChatRoot(page);                              // ← selector robusto
        await expect(chat).toBeVisible({ timeout: 10000 });
        await expect(chat).toHaveScreenshot("gallery_01_bienvenida.png", { animations: "disabled" });

        // 2) Cards (cursos / certificados / soporte)
        await page.getByPlaceholder(/escribe tu mensaje/i).fill("Ver cursos recomendados");
        await page.getByRole("button", { name: /enviar/i }).click();
        const cards = page.locator("[data-testid=chat-card]");
        await expect(cards.first()).toBeVisible({ timeout: 10000 });
        await expect(chat).toHaveScreenshot("gallery_02_cards.png", { animations: "disabled" });
        await expect(page.getByRole("link", { name: /certificados/i })).toBeVisible();

        // 3) Audio OK
        await page.getByTestId("mic-button").click();
        await page.getByTestId("mic-stop").click();
        await expect(page.getByText(/Audio recibido/)).toBeVisible({ timeout: 10000 });
        await expect(chat).toHaveScreenshot("gallery_03_audio_ok.png", { animations: "disabled" });

        // 4) Audio error (2ª llamada)
        await page.getByTestId("mic-button").click();
        await page.getByTestId("mic-stop").click();
        await expect(page.getByText(/Archivo demasiado grande|límite|excede/i)).toBeVisible({ timeout: 10000 });
        const toastErr = page.locator("[data-testid=toast-error]");
        if (await toastErr.count()) {
            await expect(toastErr).toHaveScreenshot("gallery_04_audio_error.png", { animations: "disabled" });
        } else {
            await expect(chat).toHaveScreenshot("gallery_04_audio_error.png", { animations: "disabled" });
        }

        // 5) FAQs explícitas
        await page.getByPlaceholder(/escribe tu mensaje/i).fill("FAQs Zajuna");
        await page.getByRole("button", { name: /enviar/i }).click();
        await expect(chat).toHaveScreenshot("gallery_05_faqs.png", { animations: "disabled" });
    });
});