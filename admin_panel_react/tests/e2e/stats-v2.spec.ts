import { test, expect } from "@playwright/test";

test.describe("StatsPageV2 (/stats-v2) con mocks", () => {
    test("muestra tarjetas de resumen, filtra por fechas y renderiza múltiples <svg>", async ({ page }) => {
        // Mock de /api/stats (mismo contrato que en StatsPage)
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

        await page.goto("/stats-v2");

        // Encabezado visible
        await expect(page.getByRole("heading")).toBeVisible();

        // Tarjetas: textos comunes (ajusta si tu UI usa otros labels)
        await expect(page.getByText(/total/i)).toBeVisible();
        await expect(page.getByText(/acierto|éxito|success/i)).toBeVisible();
        await expect(page.getByText(/no entendido|fallback/i)).toBeVisible();
        await expect(page.getByText(/latencia|respuesta/i)).toBeVisible();

        // Valores numéricos del summary visibles (si tu UI los muestra tal cual)
        await expect(page.getByText("345")).toBeVisible(); // total
        await expect(page.getByText("290")).toBeVisible(); // aciertos
        await expect(page.getByText("24")).toBeVisible();  // no entendidos

        // Debe haber al menos 2 gráficos (Recharts <svg>)
        const svgs = page.locator("svg");
        await expect(svgs.first()).toBeVisible();
        await expect(svgs.nth(1)).toBeVisible(); // garantiza 2 o más

        // Filtros de fecha (si existen)
        const desde = page.locator('input[type="date"]').first();
        const hasta = page.locator('input[type="date"]').nth(1);
        if (await desde.isVisible().catch(() => false)) {
            await desde.fill("2025-08-10");
            await hasta.fill("2025-08-12");
            // Tras filtrar, los gráficos siguen visibles
            await expect(svgs.first()).toBeVisible();
            await expect(svgs.nth(1)).toBeVisible();
        }

        // Top confusions visibles (intents y ejemplos)
        await expect(page.getByText("nlu_fallback")).toBeVisible();
        await expect(page.getByText("faq_envio")).toBeVisible();
        await expect(page.getByText(/no entiendo esto/i)).toBeVisible();
        await expect(page.getByText(/cuando llega\?/i)).toBeVisible();
        await expect(page.getByTestId("stat-total")).toHaveText(/\d+/);
        await expect(page.getByTestId("stat-success")).toBeVisible();
        await expect(page.getByTestId("stat-fallback")).toBeVisible();
        await expect(page.getByTestId("stat-latency")).toContainText("ms");

    });
});