/* public/zajuna-widget.sustentacion.js
 * Chatbot embebido • Tutor Virtual (Sustentación)
 * - Auto-inserta un iframe con /chat?embed=1
 * - Opcional: autenticación por postMessage (envía token cuando el iframe lo pide)
 * - Config vía data-attrs en la etiqueta <script> que lo carga
 *
 * Atributos soportados:
 *  data-src              → URL del frontend que sirve /chat?embed=1 (ej: https://host/chat?embed=1)
 *  data-width            → ancho del contenedor (ej: "100%" | "420px")
 *  data-height           → alto del contenedor (ej: "560" | "560px" | "100vh")
 *  data-allow            → permisos (ej: "microphone; clipboard-read; clipboard-write")
 *  data-sandbox          → sandbox policy (opcional; por defecto ya es segura)
 *  data-theme            → "light" | "dark" (opcional, solo como hint visual del wrapper)
 *  data-auth-mode        → "none" | "demo" | "custom"
 *     - none  → no envía token
 *     - demo  → envía FAKE_TOKEN_ZAJUNA (útil con DEMO_MODE=true en backend)
 *     - custom→ invoca window.__zajunaGetAuthToken() si existe
 *
 *  data-target           → selector CSS del contenedor donde inyectar; por defecto crea uno al final <body>
 *  data-border           → "true" | "false" (borde del wrapper, por defecto true)
 *  data-radius           → border-radius (ej: "12px")
 *
 * API opcional del host:
 *  window.__zajunaGetAuthToken = async () => "JWT_REAL_DEL_HOST"
 */

(function () {
    try {
        const currentScript = document.currentScript || (function () {
            const scripts = document.getElementsByTagName('script');
            return scripts[scripts.length - 1];
        })();

        const attrs = (name, fallback = "") => (currentScript.getAttribute(name) || fallback);
        const src = attrs("data-src", "").trim();
        if (!src) {
            console.error("[zajuna-widget] data-src es requerido, ej: data-src='http://localhost:5173/chat?embed=1'");
            return;
        }

        const width = attrs("data-width", "100%");
        const height = attrs("data-height", "560");
        const allow = attrs("data-allow", "microphone; clipboard-read; clipboard-write");
        const sandbox = attrs("data-sandbox", "allow-forms allow-scripts allow-same-origin allow-popups allow-downloads allow-modals");
        const theme = attrs("data-theme", "light");
        const targetSelector = attrs("data-target", "");
        const borderOn = (attrs("data-border", "true") + "").toLowerCase() !== "false";
        const radius = attrs("data-radius", "12px");
        const authMode = (attrs("data-auth-mode", "none") || "none").toLowerCase(); // none | demo | custom

        const targetEl = targetSelector ? document.querySelector(targetSelector) : null;

        // Wrapper
        const wrapper = document.createElement("div");
        wrapper.className = "zajuna-embed-wrapper";
        wrapper.style.cssText = `
      width: ${/^\d+$/.test(width) ? width + "px" : width};
      height: ${/^\d+$/.test(height) ? height + "px" : height};
      border: ${borderOn ? "1px solid #e5e7eb" : "0"};
      border-radius: ${radius};
      overflow: hidden;
      background: ${theme === "dark" ? "#0b0b0b" : "#ffffff"};
      box-shadow: 0 8px 30px rgba(2, 6, 23, 0.08);
    `;

        // Iframe
        const iframe = document.createElement("iframe");
        iframe.src = src;
        iframe.style.cssText = "width:100%;height:100%;border:0;display:block;";
        iframe.allow = allow;
        iframe.referrerPolicy = "strict-origin-when-cross-origin";
        iframe.sandbox = sandbox;

        wrapper.appendChild(iframe);

        if (targetEl) {
            targetEl.appendChild(wrapper);
        } else {
            document.body.appendChild(wrapper);
        }

        // Seguridad: limitamos el origin de vuelta al 'src' del iframe
        let iframeOrigin = "*";
        try { iframeOrigin = new URL(src).origin; } catch { }

        // Auth: postMessage → token
        async function getAuthToken() {
            if (authMode === "none") return null;
            if (authMode === "demo") return "FAKE_TOKEN_ZAJUNA"; // requiere DEMO_MODE=true en backend
            if (authMode === "custom" && typeof window.__zajunaGetAuthToken === "function") {
                try { return await window.__zajunaGetAuthToken(); } catch { return null; }
            }
            return null;
        }

        // Si el iframe nos pide token (auth:needed), respondemos
        window.addEventListener("message", async (ev) => {
            if (iframeOrigin !== "*" && ev.origin !== iframeOrigin) return;
            const data = ev.data || {};
            if (data.type === "auth:needed") {
                const token = await getAuthToken();
                if (token) {
                    iframe.contentWindow?.postMessage({ type: "auth:token", token }, iframeOrigin);
                }
            }
        });

        // (Opcional) enviar token proactivo al cargar
        window.addEventListener("load", async () => {
            const token = await getAuthToken();
            if (token) {
                setTimeout(() => {
                    iframe.contentWindow?.postMessage({ type: "auth:token", token }, iframeOrigin);
                }, 300);
            }
        });
    } catch (e) {
        console.error("[zajuna-widget] error inicializando widget:", e);
    }
})();
