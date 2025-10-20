import { test, expect } from "@playwright/test";

const CHAT_PATH = process.env.CHAT_PATH || "/chat";

test.describe("Chat - Texto (ECO)", () => {
    test("envía texto y el bot responde con un eco y opciones Zajuna", async ({ page }) => {
        // Intercepta /api/chat (texto)
        await page.route("**/api/chat", async (route) => {
            if (route.request().method() === "POST") {
                let text = "";
                try {
                    const body = route.request().postDataJSON?.();
                    text = body?.text || body?.message || "";
                } catch {
                    // no-op
                }

                const rasaMessages = [
                    { text: `Recibí: "${text}". ¿Te ayudo en Zajuna?` },
                    {
                        buttons: [
                            { title: "Cursos y matrícula", payload: "/faq_cursos_matricula" },
                            { title: "Navegación en la plataforma", payload: "/faq_navegacion" },
                        ],
                    },
                ];

                return route.fulfill({
                    status: 200,
                    contentType: "application/json",
                    body: JSON.stringify(rasaMessages),
                });
            }
            route.continue();
        });

        // (Opcional) Intercepta /api/chat/audio por si el MicButton hiciera alguna llamada
        await page.route("**/api/chat/audio", async (route) => {
            if (route.request().method() === "POST") {
                const mock = {
                    ok: true,
                    transcript: "transcripción simulada",
                    bot: { messages: [{ text: "Procesé tu audio (ECO mock)." }] },
                };
                return route.fulfill({
                    status: 200,
                    contentType: "application/json",
                    body: JSON.stringify(mock),
                });
            }
            route.continue();
        });

        await page.goto(CHAT_PATH);

        // Interactúa con el composer
        const input = page.getByTestId("chat-input");
        const sendBtn = page.getByTestId("chat-send");

        await expect(input).toBeVisible();
        await input.fill("¿Cómo veo mis calificaciones en Zajuna?");
        await sendBtn.click();

        // Verifica que se vea el mensaje del usuario…
        await expect(page.getByText("¿Cómo veo mis calificaciones en Zajuna?")).toBeVisible();

        // …y el eco del bot
        await expect(
            page.getByText('Recibí: "¿Cómo veo mis calificaciones en Zajuna?". ¿Te ayudo en Zajuna?', { exact: false })
        ).toBeVisible();

        // Screenshot de la conversación (snapshot visual)
        await expect(page).toHaveScreenshot("chat-text-echo.png", { fullPage: true });
    });
});