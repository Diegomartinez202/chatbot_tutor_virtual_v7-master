import { test, expect } from '@playwright/test';

test('chat-widget.js monta y abre', async ({ page }) => {
    await page.setContent(`
    <html><body>
      <script
        src="/chat-widget.js"
        data-chat-url="/chat-embed.html?src=%2Fchat%3Fembed%3D1"
        data-avatar="/bot-avatar.png"
        defer></script>
    </body></html>
  `);
    // espera a que aparezca el botón (img del avatar)
    const btn = page.locator('img[alt="Chatbot"]');
    await expect(btn).toBeVisible();
    await btn.click();
    // tras abrir, debe existir iframe
    await expect(page.locator('iframe[title="Chat"]')).toBeVisible();
});
