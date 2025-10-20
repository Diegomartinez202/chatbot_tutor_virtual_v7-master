import { test, expect } from "@playwright/test";

test.describe("Chat (/chat) con mock API y latencia simulada", () => {
    test("envía mensaje y recibe respuesta del bot", async ({ page }) => {
        const handler = async (route: any) => {
            const req = route.request();
            expect(req.method()).toBe("POST");

            let body: any = {};
            try { body = req.postDataJSON?.() ?? {}; } catch { }
            expect(typeof body.message).toBe("string");

            await new Promise((r) => setTimeout(r, 200)); // latencia simulada

            const response = [{ text: "¡Hola! Soy TutorBot. (mock, 200ms)" }];
            await route.fulfill({
                status: 200,
                contentType: "application/json",
                body: JSON.stringify(response),
            });
        };

        await page.route("**/api/chat", handler);
        await page.route("**/chat", handler);

        await page.goto("/chat");

        // input robusto (mejor si agregas data-testid; abajo te dejo snippet)
        const input = page.locator('[data-testid="chat-input"], textarea, input[type="text"]');
        await expect(input.first()).toBeVisible({ timeout: 5000 });
        await input.first().fill("Hola desde E2E");

        // botón enviar si existe; si no, Enter
        const sendBtn = page.locator('[data-testid="chat-send"], button[aria-label="Enviar"], button:has-text("Enviar")');
        if (await sendBtn.first().isVisible().catch(() => false)) {
            await sendBtn.first().click();
        } else {
            await page.keyboard.press("Enter");
        }

        await expect(page.locator("text=Hola desde E2E").first()).toBeVisible();
        await expect(page.locator("text=mock, 200ms")).toBeVisible();
    });
});