import type { Page, Route } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

export async function routeZajuna(page: Page) {
    const fixturesPath = path.resolve(process.cwd(), "tests/e2e/mocks/zajuna.fixtures.json");
    const raw = fs.readFileSync(fixturesPath, "utf8");
    const zajuna = JSON.parse(raw);

    await page.route("**/api/chat", async (route: Route) => {
        if (route.request().method() !== "POST") return route.fallback();

        const body = {
            messages: [
                { type: "text", text: "Preguntas frecuentes Zajuna:" },
                { type: "list", items: zajuna.faqs.map((f: any) => `• ${f.q}`) },
                { type: "text", text: "Cursos recomendados:" },
                {
                    type: "cards",
                    cards: zajuna.cursos.map((c: any) => ({
                        title: c.titulo,
                        subtitle: `${c.duracion} · ${c.modalidad}`,
                        image: "https://placehold.co/600x360?text=Curso",
                        buttons: [{ label: "Ver curso", url: c.url }]
                    }))
                }
            ]
        };

        await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify(body)
        });
    });
}