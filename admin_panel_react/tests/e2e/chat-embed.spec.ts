import { test, expect } from "@playwright/test";

test("chat-embed muestra el iframe del chat interno", async ({ page, baseURL }) => {
    await page.goto(`${baseURL}/chat-embed.html?src=/chat%3Fembed%3D1`);
    const iframeEl = page.locator('iframe[title="Chatbot"], iframe[title="Chat"]');
    await expect(iframeEl).toBeVisible();
    await expect(iframeEl).toHaveAttribute("src", /\/chat(\?|%3F)embed=1/);
});