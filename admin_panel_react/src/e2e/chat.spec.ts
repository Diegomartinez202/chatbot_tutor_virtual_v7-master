import { test, expect } from '@playwright/test';

test('carga /chat', async ({ page }) => {
    await page.goto('http://localhost:5173/chat');
    await expect(page.getByText('Asistente')).toBeVisible(); // título si no es embed
    await expect(page.getByPlaceholder('Escribe un mensaje…')).toBeVisible();
});

test('carga chat-embed.html con src=/chat?embed=1', async ({ page }) => {
    await page.goto('http://localhost:5173/chat-embed.html?src=%2Fchat%3Fembed%3D1');
    // el iframe interno debería cargar ChatUI
    const inner = page.frameLocator('iframe');
    await expect(inner.getByPlaceholder('Escribe un mensaje…')).toBeVisible();
});
