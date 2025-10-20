import { test, expect } from "@playwright/test";

test.describe("StatsPage (/stats) con mocks", () => {
    test("renderiza resumen, filtros, <svg> de Recharts y top_confusions", async ({ page }) => {
        const mock = {
            summary: {
                total_messages: 345,
                bot_success: 290,
                not_understood: 24,
                avg_response_ms: 420,
                accuracy: 0.89,
            },
            series: {
                by_day: [
                    { date: "2025-08-10", messages: 40, success: 35, fallback: 3 },
                    { date: "2025-08-11", messages: 52, success: 46, fallback: 4 },
                    { date: "2025-08-12", messages: 63, success: 51, fallback: 7 },
                ],
                latency_ms_p50: [
                    { date: "2025-08-10", value: 350 },
                    { date: "2025-08-11", value: 400 },
                    { date: "2025-08-12", value: 430 },
                ],
                latency_ms_p95: [
                    { date: "2025-08-10", value: 800 },
                    { date: "2025-08-11", value: 900 },
                    { date: "2025-08-12", value: 950 },
                ],
            },
            top_confusions: [
                { intent: "nlu_fallback", count: 12, example: "no entiendo esto" },
                { intent: "faq_envio", count: 4, example: "cuando llega?" },
            ],
        };

        await page.route("**/api/stats**", async (route) => {
            await route.fulfill({
                status: 200,
                contentType: "application/json",
                body: JSON.stringify(mock),
            });
        });

        await page.goto("/stats");

        // Título/encabezado visible
        await expect(page.getByRole("heading").first()).toBeVisible();

        // Filtros de fecha (si existen en la página)
        const desde = page.locator('input[type="date"]').first();
        const hasta = page.locator('input[type="date"]').nth(1);
        if (await desde.isVisible().catch(() => false)) {
            await desde.fill("2025-08-10");
            await hasta.fill("2025-08-12");
        }

        // Al menos 1 <svg> (Recharts)
        const svgCount = await page.locator("svg").count();
        expect(svgCount).toBeGreaterThan(0);

        // Top confusions visibles (ajusta a tu UI si cambian los textos)
        await expect(page.getByText("nlu_fallback")).toBeVisible();
        await expect(page.getByText("faq_envio")).toBeVisible();

        // Stats por testId (si los añadiste en tu UI)
        const total = page.getByTestId("stat-total");
        const success = page.getByTestId("stat-success");
        const fallback = page.getByTestId("stat-fallback");
        const latency = page.getByTestId("stat-latency");

        if (await total.count()) await expect(total).toHaveText(/\d+/);
        if (await success.count()) await expect(success).toBeVisible();
        if (await fallback.count()) await expect(fallback).toBeVisible();
        if (await latency.count()) await expect(latency).toContainText("ms");
    });
});