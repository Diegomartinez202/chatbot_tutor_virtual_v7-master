// admin_panel_react/tests/visual/chatui-visual.spec.ts
import { test, expect } from "@playwright/test";

test("ChatUI carga composer (mock /api/chat)", async ({ page }) => {
    // Evita llamadas reales al escribir
    await page.route("**/api/chat", (route) =>
        route.fulfill({ status: 200, contentType: "application/json", body: "[]" })
    );

    await page.goto("/chat");
    await expect(page.getByTestId("chat-composer")).toBeVisible();
    await expect(page.getByTestId("chat-input")).toBeVisible();
    await expect(page.getByTestId("chat-send")).toBeVisible();

    await expect(page).toHaveScreenshot("chatui-initial.png", { fullPage: true });
});