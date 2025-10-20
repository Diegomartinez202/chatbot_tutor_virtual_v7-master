import { test, expect } from "@playwright/test";

test("backend /health responde 2xx (skip si no hay base)", async ({ request }) => {
    const chatBase = process.env.CHAT_BASE || process.env.PROD_BACKEND_CHAT_BASE;
    if (!chatBase) test.skip(true, "CHAT_BASE/PROD_BACKEND_CHAT_BASE no definido");

    const base = chatBase!.replace(/\/$/, "");
    const candidates = ["/health", "/api/chat/health", "/chat/health"];

    let ok = false;
    for (const p of candidates) {
        const res = await request.get(base + p);
        if (res.ok()) { ok = true; break; }
    }
    expect(ok).toBeTruthy();
});