// tests/e2e/chat-text.spec.ts
import { test, expect } from "@playwright/test";
import { readFile } from "node:fs/promises";

const CHAT_PATH = process.env.CHAT_PATH || "/chat";

let ok: unknown;

test.beforeAll(async () => {
    const url = new URL("../fixtures/bot.response.ok.json", import.meta.url);
    const raw = await readFile(url, "utf8");
    ok = JSON.parse(raw);
});

test.describe("Chat - Texto (REST)", () => {
    test("envía texto y muestra respuesta del bot", async ({ page }) => {
        await page.route("**/api/chat", async (route) => {
            if (route.request().method() === "POST") {
                await route.fulfill({
                    status: 200,
                    contentType: "application/json",
                    body: JSON.stringify(ok),
                });
                return;
            }
            route.continue();
        });

        await page.goto(CHAT_PATH);
        await page.getByTestId("chat-input").fill("Necesito ayuda con fracciones");
        await page.getByTestId("chat-send").click();

        await expect(
            page.getByText(/Te ayudo con fracciones/i, { exact: false })
        ).toBeVisible();

        await expect(page).toHaveScreenshot("chat-text.png", { fullPage: true });
    });
});