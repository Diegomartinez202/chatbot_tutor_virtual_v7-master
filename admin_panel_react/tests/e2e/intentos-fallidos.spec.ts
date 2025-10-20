import { test, expect } from "@playwright/test";

test.describe("Intentos fallidos (/intentos-fallidos) con mocks", () => {
    test("muestra la lista/tabla de intents no reconocidos", async ({ page }) => {
        const failures = {
            items: [
                { intent: "nlu_fallback", count: 12, example: "no entiendo esto" },
                { intent: "saludo_desconocido", count: 5, example: "hola hola???" },
            ],
            total: 17,
            updated_at: "2025-08-12T10:00:00Z",
        };

        const statsWithConfusions = {
            summary: {},
            series: {},
            top_confusions: failures.items,
        };

        // Cubre las dos rutas posibles
        await page.route("**/api/intentos-fallidos**", async (route) => {
            await route.fulfill({
                status: 200,
                contentType: "application/json",
                body: JSON.stringify(failures),
            });
        });

        await page.route("**/api/stats**", async (route) => {
            await route.fulfill({
                status: 200,
                contentType: "application/json",
                body: JSON.stringify(statsWithConfusions),
            });
        });

        await page.goto("/intentos-fallidos");

        // Título/encabezado visible
        await expect(page.getByRole("heading")).toBeVisible();

        // Presencia de filas o tarjetas con intents fallidos
        await expect(page.getByText("nlu_fallback")).toBeVisible();
        await expect(page.getByText("saludo_desconocido")).toBeVisible();

        // Conteos visibles (ajusta si tu UI formatea distinto)
        await expect(page.getByText("12")).toBeVisible();
        await expect(page.getByText("5")).toBeVisible();

        // Ejemplos visibles
        await expect(page.getByText("no entiendo esto")).toBeVisible();
        await expect(page.getByText("hola hola???")).toBeVisible();
    });
});