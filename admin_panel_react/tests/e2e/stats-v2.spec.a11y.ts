import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test.describe("A11y StatsPageV2", () => {
    test("sin violaciones cr�ticas/serias y roles b�sicos presentes", async ({ page }) => {
        // Mock m�nimo para /api/stats (si la p�gina carga datos)
        const mock = {
            summary: { total_messages: 10, bot_success: 8, not_understood: 2, avg_response_ms: 300, accuracy: 0.8 },
            series: { by_day: [], latency_ms_p50: [], latency_ms_p95: [] },
            top_confusions: [],
        };
        await page.route("**/api/stats**", async (route) => {
            await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(mock) });
        });

        await page.goto("/stats-v2");

        // Roles/sem�ntica b�sicos
        await expect(page.getByRole("heading").first()).toBeVisible();

        // Escaneo a11y con Axe
        // (Si alg�n gr�fico dispara falsos positivos de contraste, puedes a�adir `.disableRules(['color-contrast'])`)
        const results = await new AxeBuilder({ page }).analyze();

        // Filtra solo impactos serios/cr�ticos
        const serious = results.violations.filter((v) => ["serious", "critical"].includes(v.impact ?? ""));
        if (serious.length) {
            await test.info().attach("a11y-serious", {
                body: JSON.stringify(serious, null, 2),
                contentType: "application/json",
            });
        }
        expect(
            serious.length,
            `Violaciones a11y (serious/critical):\n${JSON.stringify(serious, null, 2)}`
        ).toBe(0);
    });
});