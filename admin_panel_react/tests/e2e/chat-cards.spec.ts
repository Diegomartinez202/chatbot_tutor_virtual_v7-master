// tests/e2e/chat-cards.spec.ts
import { test, expect } from "@playwright/test";
import { readFile } from "node:fs/promises";

const CHAT_PATH = process.env.CHAT_PATH || "/chat";

let cards: unknown;

// Cargamos el JSON de forma compatible con NodeNext sin import attributes
test.beforeAll(async () => {
    const url = new URL("../fixtures/bot.response.cards.json", import.meta.url);
    const raw = await readFile(url, "utf8");
    cards = JSON.parse(raw);
});

test.describe("Chat - Cards", () => {
    test("muestra cards de respuesta", async ({ page }) => {
        await page.route("**/api/chat", async (route) => {
            if (route.request().method() === "POST") {
                await route.fulfill({
                    status: 200,
                    contentType: "application/json",
                    body: JSON.stringify(cards),
                });
                return;
            }
            route.continue();
        });

        await page.goto(CHAT_PATH);
        await page.getByTestId("chat-input").fill("Ver cursos recomendados");
        await page.getByTestId("chat-send").click();

        await expect(page.getByTestId("chat-card").first()).toBeVisible();
        await expect(page).toHaveScreenshot("chat-cards.png", { fullPage: true });
    });
});