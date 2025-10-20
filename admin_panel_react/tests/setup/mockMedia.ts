// tests/setup/mockMedia.ts
/**
 * Mocks de MediaDevices.getUserMedia y MediaRecorder para correr en browser context.
 * - NO reasigna navigator.mediaDevices (es read-only), usa defineProperty.
 * - getUserMedia devuelve un MediaStream real (vacío) → evita errores TS/lib.dom.
 * - MediaRecorder mock emite unos chunks y permite stop().
 */
import type { Page } from "@playwright/test";

export async function installMediaMocksInPage(page: Page) {
    await page.addInitScript(() => {
        // Definir mediaDevices si no existe (sin reasignar la propiedad)
        if (!("mediaDevices" in navigator)) {
            Object.defineProperty(navigator, "mediaDevices", {
                value: {},
                configurable: true
            });
        }

        // getUserMedia que retorna un MediaStream real (evita errores de tipos)
        Object.defineProperty(navigator.mediaDevices, "getUserMedia", {
            configurable: true,
            value: async () => new MediaStream()
        });

        // Mock de MediaRecorder
        class MockMediaRecorder {
            public ondataavailable: ((e: any) => void) | null = null;
            public onstop: (() => void) | null = null;
            public state: "inactive" | "recording" | "paused" = "inactive";
            private _interval: number | null = null;
            private _ticks = 0;

            constructor(_stream: MediaStream, _opts: any = {}) { }

            static isTypeSupported() {
                return true;
            }

            start() {
                this.state = "recording";
                this._ticks = 0;
                this._interval = window.setInterval(() => {
                    this._ticks++;
                    this.ondataavailable?.({
                        data: new Blob([`chunk-${this._ticks}`], { type: "audio/webm" })
                    });
                    if (this._ticks >= 3 && this._interval) {
                        window.clearInterval(this._interval);
                        this._interval = null;
                    }
                }, 100);
            }

            stop() {
                if (this._interval) {
                    window.clearInterval(this._interval);
                    this._interval = null;
                }
                this.state = "inactive";
                this.onstop?.();
            }
        }

        (window as any).MediaRecorder = MockMediaRecorder;
    });
}