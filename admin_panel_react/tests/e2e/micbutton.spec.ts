// tests/e2e/micbutton.spec.ts
import { test, expect } from "@playwright/test";
import { installMediaMocksInPage } from "../setup/mockMedia.js"; // ← extensión .js

const CHAT_PATH = process.env.CHAT_PATH || "/chat";

// Respuesta mínima del bot (evitamos importar JSON para no chocar con NodeNext)
const ok = [
    { text: "¡Claro! Empecemos con un ejemplo de fracciones." },
    { buttons: [{ title: "1/2 + 1/3", payload: "/resolver_12_13" }] },
];

test.describe("MicButton - audio → /api/chat/audio", () => {
    test.beforeEach(async ({ page }) => {
        // Inyecta mocks de getUserMedia + MediaRecorder en el contexto del navegador
        await installMediaMocksInPage(page);

        // Intercepta POST de texto para aislar el flujo de audio
        await page.route("**/api/chat", (route) => {
            if (route.request().method() === "POST") {
                return route.fulfill({
                    status: 200,
                    contentType: "application/json",
                    body: JSON.stringify([{ text: "Texto interceptado (mock)" }]),
                });
            }
            route.continue();
        });
    });

    test("grabar → parar → subir (200 OK): muestra transcript + respuesta del bot", async ({ page }) => {
        // Mock de /api/chat/audio: 200 OK con transcript y mensajes del bot
        await page.route("**/api/chat/audio", async (route) => {
            return route.fulfill({
                status: 200,
                contentType: "application/json",
                body: JSON.stringify({
                    ok: true,
                    transcript: "hola, necesito ayuda con fracciones (desde test)",
                    bot: { messages: ok },
                }),
            });
        });

        // Abre el chat (Harness en /chat no exige login)
        await page.goto(`${CHAT_PATH}?persona=aprendiz&lang=es-CO`);

        // 1) Grabar
        await page.getByTestId("mic-button").click();

        // 2) Detener
        await page.getByTestId("mic-stop").click();

        // 3) Enviar
        await page.getByTestId("mic-upload").click();

        // 4) Transcript del usuario visible en el chat
        await expect(
            page.getByText("hola, necesito ayuda con fracciones (desde test)")
        ).toBeVisible();

        // 5) Respuesta del bot visible
        await expect(
            page.getByText("¡Claro! Empecemos con un ejemplo de fracciones.")
        ).toBeVisible();

        // 6) Captura rápida del composer tras el flujo de audio
        const composer = page.getByTestId("chat-composer");
        await expect(composer).toBeVisible();
        await composer.screenshot({
            path: "playwright-report/composer-after-audio.png",
        });
    });
});