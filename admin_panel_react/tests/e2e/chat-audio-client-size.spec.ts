import { test, expect } from "@playwright/test";

const CHAT_PATH = process.env.CHAT_PATH || "/chat";

test.describe("Chat - Mic (error de cliente: archivo >15MB)", () => {
    test.beforeEach(async ({ page }) => {
        // Mock getUserMedia + MediaRecorder que genera un Blob > 15MB
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
                    // Emite un chunk ~16MB para gatillar la validación del MicButton (15MB máx.)
                    setTimeout(() => {
                        const big = new Uint8Array(16 * 1024 * 1024); // 16MB
                        const blob = new Blob([big], { type: "audio/webm" });
                        this.ondataavailable && this.ondataavailable({ data: blob });
                    }, 30);
                }

                stop() {
                    this.state = "inactive";
                    this.onstop && this.onstop();
                }
            };
        });
    });

    test("no hace request y muestra 'El audio es demasiado grande (máx. 15 MB).'", async ({ page }) => {
        // Si el cliente intentara llamar al backend, lo detectamos
        let hit = false;
        await page.route("**/api/chat/audio", async (route) => {
            hit = true;
            // Devolvemos algo imposible para romper la prueba si llega aquí
            await route.fulfill({ status: 418, contentType: "text/plain", body: "NO DEBÍA ENVIAR" });
        });

        await page.goto(CHAT_PATH);

        // Grabar (mock), detener y enviar
        await page.getByRole("button", { name: "Grabar audio" }).click();
        await page.getByRole("button", { name: "Detener grabación" }).click();

        const uploadBtn = page.getByRole("button", { name: "Enviar audio" });
        await expect(uploadBtn).toBeVisible();
        await uploadBtn.click();

        // Valida el mensaje de error del propio MicButton (cliente)
        await expect(
            page.getByText("El audio es demasiado grande (máx. 15 MB).")
        ).toBeVisible();

        // Asegura que NO se llamó al backend
        expect(hit).toBe(false);

        // Screenshot
        await expect(page).toHaveScreenshot("chat-mic-client-size.png", { fullPage: true });
    });
});
