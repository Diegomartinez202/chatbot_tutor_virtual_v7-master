// tests/e2e/chat-mic-upload-seq.spec.ts
import { test, expect } from "@playwright/test";
// Con NodeNext/ESM hay que importar con extensión .js aunque el archivo sea .ts
import { installMediaMocksInPage } from "../setup/mockMedia.js";

const CHAT_PATH = process.env.CHAT_PATH || "/chat-old?embed=1";

//const CHAT_PATH = process.env.CHAT_PATH || "/chat?persona=aprendiz&lang=es-CO"; // Se usa para tests de chat en modo embed
// Si no tienes CHAT_PATH definido, puedes usar el valor por defecto "/chat-old?embed=1"
// Respuesta mínima del bot (evitamos importar JSON)
const ok = [
    { text: "¡Claro! Empecemos con un ejemplo de fracciones." },
    { buttons: [{ title: "1/2 + 1/3", payload: "/resolver_12_13" }] }
];

test.describe("Chat – Mic (grabar → parar → subir) con mock secuencial 200→413", () => {
    test.beforeEach(async ({ page }) => {
        // 1) Mocks de audio correctos (sin reasignar mediaDevices)
        await installMediaMocksInPage(page);

        // 2) Intercepta toda la API del chat:
        await page.route("**/api/chat**", (route) => {
            const req = route.request();
            // POST de texto → eco controlado
            if (req.method() === "POST") {
                return route.fulfill({
                    status: 200,
                    contentType: "application/json",
                    body: JSON.stringify([{ text: "Texto interceptado (mock)" }])
                });
            }
            // GET/HEAD/OPTIONS (incluye /api/chat/health) → 200 vacío
            return route.fulfill({
                status: 200,
                contentType: "application/json",
                body: "{}"
            });
        });
    });

    test("1ª subida OK (200) y 2ª subida 413 muestra error", async ({ page }) => {
        // 3) Mock secuencial solo para /api/chat/audio
        let calls = 0;
        await page.route("**/api/chat/audio", async (route) => {
            calls++;
            if (calls === 1) {
                return route.fulfill({
                    status: 200,
                    contentType: "application/json",
                    body: JSON.stringify({
                        ok: true,
                        transcript: "mi audio de prueba sobre fracciones",
                        bot: { messages: ok }
                    })
                });
            }
            // Segunda subida → simulamos 413
            return route.fulfill({
                status: 413,
                contentType: "application/json",
                body: JSON.stringify({ detail: "Archivo demasiado grande" })
            });
        });

        // 4) Abre ChatPage en modo embed (o tu Harness si prefieres /chat)
        await page.goto(CHAT_PATH);

        // 5) Espera robusta: si aparece "Reintentar", haz click y sigue esperando
        const retryButton = page.getByRole("button", { name: /reintentar/i });
        if (await retryButton.isVisible().catch(() => false)) {
            await retryButton.click();
        }

        // 6) Ahora espera al composer
        await page.getByTestId("chat-composer").waitFor({ state: "visible" });

        // ——— Ciclo 1: grabar → parar → subir (OK) ———
        await page.getByTestId("mic-button").click(); // grabar
        await page.getByTestId("mic-stop").click();   // detener
        await page.getByTestId("mic-upload").click(); // subir

        // Ver transcript del usuario
        await expect(
            page.getByText("mi audio de prueba sobre fracciones", { exact: false })
        ).toBeVisible();

        // Ver contenido del bot
        await expect(page.getByText(/fracciones/i)).toBeVisible();

        // ——— Ciclo 2: nuevo audio → 413 ———
        await page.getByTestId("mic-button").click();
        await page.getByTestId("mic-stop").click();
        await page.getByTestId("mic-upload").click();

        // Error inline del MicButton
        await expect(page.getByTestId("mic-error")).toBeVisible();
        await expect(page.getByTestId("mic-error")).toContainText(/demasiado grande|413|error/i);

        // Screenshot del estado final del chat
        await expect(page).toHaveScreenshot("chat-mic-upload-seq.png", { fullPage: true });
    });
});