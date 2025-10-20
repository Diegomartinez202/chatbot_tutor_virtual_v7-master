import { test, expect } from "@playwright/test";

const CHAT_PATH = process.env.CHAT_PATH || "/chat";

test.describe("Chat – Mic (validación local tamaño > 15MB, sin backend)", () => {
    test.beforeEach(async ({ page }) => {
        // Stub getUserMedia + MediaRecorder → genera blob ~16MB
        await page.addInitScript(() => {
            // @ts-ignore
            navigator.mediaDevices = {
                getUserMedia: async () => ({
                    getTracks: () => [{ stop() { } }]
                })
            };

            // @ts-ignore
            window.MediaRecorder = class {
                ondataavailable = null;
                onstop = null;
                state = "inactive";
                constructor(_stream, _opts) { }
                start() {
                    this.state = "recording";
                    setTimeout(() => {
                        const big = new Uint8Array(16 * 1024 * 1024); // 16MB
                        const blob = new Blob([big], { type: "audio/webm" });
                        this.ondataavailable && this.ondataavailable({ data: blob });
                    }, 40);
                }
                stop() {
                    this.state = "inactive";
                    this.onstop && this.onstop();
                }
                static isTypeSupported() { return true; }
            };
        });

        // Evita POST /api/chat de texto
        await page.route("**/api/chat", (route) => {
            if (route.request().method() === "POST") {
                return route.fulfill({
                    status: 200,
                    contentType: "application/json",
                    body: JSON.stringify([{ text: "Texto interceptado (mock)" }])
                });
            }
            route.continue();
        });

        // Bloquea /api/chat/audio por seguridad (no debería llamarse)
        await page.route("**/api/chat/audio", (route) =>
            route.fulfill({ status: 500, contentType: "text/plain", body: "NO DEBERÍA LLAMAR" })
        );
    });

    test("muestra el mensaje local de 'El audio es demasiado grande'", async ({ page }) => {
        await page.goto(`${CHAT_PATH}?persona=aprendiz&lang=es-CO`);

        // 1) Grabar (mock)
        await page.getByRole("button", { name: "Grabar audio" }).click();
        // 2) Detener
        await page.getByRole("button", { name: "Detener grabación" }).click();
        // 3) Enviar → debe gatillar validación local (sin request)
        await page.getByRole("button", { name: "Enviar audio" }).click();

        // Error inline del MicButton (aria o testid si lo agregaste)
        await expect(page.getByText(/demasiado grande|15\s*MB/i)).toBeVisible();

        // Screenshot del estado de error
        await expect(page).toHaveScreenshot("chat-mic-size-error.png", { fullPage: true });
    });
});