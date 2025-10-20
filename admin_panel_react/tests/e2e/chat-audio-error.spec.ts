import { test, expect } from "@playwright/test";

const CHAT_PATH = process.env.CHAT_PATH || "/chat";

test.describe("Chat - Mic (errores /api/chat/audio)", () => {
    test.beforeEach(async ({ page }) => {
        // Mock getUserMedia + MediaRecorder
        await page.addInitScript(() => {
            // @ts-ignore
            navigator.mediaDevices = {
                getUserMedia: async () => ({
                    getTracks: () => [{ stop() { } }],
                }),
            };

            // @ts-ignore
            window.MediaRecorder = class {
                ondataavailable: ((ev: any) => void) | null = null;
                onstop: (() => void) | null = null;
                state = "inactive";
                constructor(_stream: any, _opts?: any) { }
                start() {
                    this.state = "recording";
                    setTimeout(() => {
                        const blob = new Blob(["dummy"], { type: "audio/webm" });
                        this.ondataavailable && this.ondataavailable({ data: blob });
                    }, 40);
                }
                stop() {
                    this.state = "inactive";
                    this.onstop && this.onstop();
                }
            };
        });

        // Evita hits reales de texto si los hubiera
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

    test("muestra error 413 (audio demasiado grande)", async ({ page }) => {
        // Backend devuelve 413
        await page.route("**/api/chat/audio", async (route) => {
            await route.fulfill({
                status: 413,
                contentType: "text/plain",
                // En español para que el assert sea más claro en la UI
                body: "Audio demasiado grande (máx. 15 MB)",
            });
        });

        await page.goto(CHAT_PATH);

        // Grabar
        await page.getByRole("button", { name: "Grabar audio" }).click();
        // Detener
        await page.getByRole("button", { name: "Detener grabación" }).click();
        // Enviar
        const uploadBtn = page.getByRole("button", { name: "Enviar audio" });
        await expect(uploadBtn).toBeVisible();
        await uploadBtn.click();

        // Valida error (MicButton pinta el error inline como texto rojo)
        await expect(
            page.getByText(/(Audio demasiado grande|413|Too Large)/i)
        ).toBeVisible();

        // Snapshot visual
        await expect(page).toHaveScreenshot("chat-mic-413.png", { fullPage: true });
    });

    test("muestra error 415 (tipo de audio no soportado)", async ({ page }) => {
        // Backend devuelve 415
        await page.route("**/api/chat/audio", async (route) => {
            await route.fulfill({
                status: 415,
                contentType: "text/plain",
                body: "Tipo de audio no soportado",
            });
        });

        await page.goto(CHAT_PATH);

        // Grabar
        await page.getByRole("button", { name: "Grabar audio" }).click();
        // Detener
        await page.getByRole("button", { name: "Detener grabación" }).click();
        // Enviar
        const uploadBtn = page.getByRole("button", { name: "Enviar audio" });
        await expect(uploadBtn).toBeVisible();
        await uploadBtn.click();

        // Valida error (inline/toast)
        await expect(
            page.getByText(/(Tipo de audio no soportado|415|Unsupported)/i)
        ).toBeVisible();

        // Snapshot visual
        await expect(page).toHaveScreenshot("chat-mic-415.png", { fullPage: true });
    });
});