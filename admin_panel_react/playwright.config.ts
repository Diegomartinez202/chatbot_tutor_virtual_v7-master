/// <reference types="@playwright/test" />
/// <reference types="node" />
import { defineConfig, devices } from "@playwright/test";

const PORT = Number(process.env.PORT ?? 5173);
const BASE_URL =
    process.env.PLAYWRIGHT_BASE_URL || `http://localhost:${PORT}`;
const isExternal =
    !!process.env.PLAYWRIGHT_BASE_URL && !BASE_URL.includes("localhost");

export default defineConfig({
    testDir: "tests",
    timeout: 30_000,
    expect: { timeout: 5_000 },
    retries: process.env.CI ? 1 : 0,
    forbidOnly: !!process.env.CI,
    reporter: [
        ["line"],
        ["html", { outputFolder: "playwright-report", open: "never" }],
        ["json", { outputFile: "playwright-report/results.json" }],
    ],
    use: {
        baseURL: BASE_URL,
        headless: true,
        trace: "retain-on-failure",
        screenshot: "only-on-failure",
        video: "retain-on-failure",
    },
    projects: [
        { name: "chromium", use: { ...devices["Desktop Chrome"] } },
        { name: "firefox", use: { ...devices["Desktop Firefox"] } },
        { name: "webkit", use: { ...devices["Desktop Safari"] } },
    ],
    webServer: isExternal
        ? undefined
        : [
            {
                command: `npm run dev -- --port ${PORT}`,
                port: PORT,
                reuseExistingServer: true,
                timeout: 60_000,
            },
        ],
});