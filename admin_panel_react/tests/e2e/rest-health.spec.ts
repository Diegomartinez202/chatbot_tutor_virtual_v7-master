import { test, expect } from '@playwright/test';

test('backend /api/chat/health responde 2xx (skip si no hay CHAT_BASE)', async ({ request, baseURL }) => {
    const chatBase = process.env.CHAT_BASE; // Usa esto para prod/CI
    if (!chatBase) {
        test.skip(true, 'CHAT_BASE no definido: skipping health en local si no hay backend levantado');
    }
    const url = `${chatBase!.replace(/\/$/, '')}/health`;
    const res = await request.get(url);
    expect(res.ok()).toBeTruthy();
});