/* public/zajuna-widget.bubble.sustentacion.js
 * Bubble embebible para Sustentación
 * - Minimizable a “pill”
 * - Sync de tema/idioma via postMessage (prefs:update)
 * - Telemetría (open/close/minimize/restore/message_sent/message_received/prefs)
 * - Auth modes: none | demo | custom (window.__zajunaGetAuthToken)
 *
 * Uso:
 * <script
 *   src="/zajuna-widget.bubble.sustentacion.js"
 *   data-src="http://localhost:5173/chat?embed=1"
 *   data-auth-mode="none"
 *   data-title="Tutor Virtual"
 *   data-width="min(420px,92vw)"
 *   data-height="min(640px,85vh)"
 *   data-icon="bot"
 *   data-color="#4f46e5"
 * ></script>
 */

(function () {
    if (window.ZajunaBubble) return; // singleton

    // --- helpers ---
    const q = (s, d = document) => d.querySelector(s);
    const ce = (tag, attrs = {}) => {
        const el = document.createElement(tag);
        Object.entries(attrs).forEach(([k, v]) => {
            if (k === "style" && typeof v === "object") Object.assign(el.style, v);
            else if (k === "class") el.className = v;
            else if (v != null) el.setAttribute(k, v);
        });
        return el;
    };
    const norm = (s) => String(s || "").trim();
    const getAttr = (name, def = "") =>
        norm((scriptEl.getAttribute(name) ?? def));

    const scriptEl =
        document.currentScript ||
        document.querySelector('script[src*="zajuna-widget.bubble.sustentacion.js"]');

    if (!scriptEl) return;

    // --- config desde data-* ---
    const SRC = getAttr("data-src"); // required
    if (!SRC) {
        console.error("[ZajunaBubble] Falta data-src con /chat?embed=1");
        return;
    }
    const TITLE = getAttr("data-title", "Tutor Virtual");
    const WIDTH = getAttr("data-width", "min(420px,92vw)");
    const HEIGHT = getAttr("data-height", "min(640px,85vh)");
    const COLOR = getAttr("data-color", "#4f46e5");
    const ICON = (getAttr("data-icon", "bot") || "bot").toLowerCase();
    const Z = getAttr("data-z-index", "999999");
    const OFFSET_X = getAttr("data-offset-x", "20px");
    const OFFSET_Y = getAttr("data-offset-y", "20px");
    const ALLOW = getAttr(
        "data-allow",
        "microphone; clipboard-read; clipboard-write;"
    );
    const SANDBOX = getAttr(
        "data-sandbox",
        "allow-same-origin allow-scripts allow-forms allow-popups allow-downloads"
    );
    const AUTH_MODE = (getAttr("data-auth-mode", "none") || "none").toLowerCase();

    // --- estado runtime ---
    const state = {
        open: false,
        minimized: false,
        theme: "light", // sincronizado desde iframe
        language: "es", // sincronizado desde iframe
        onEvent: null, // callback(event)
    };

    // --- UI base: bubble + panel ---
    const root = ce("div", {
        class: "zajuna-bubble-root",
        style: {
            position: "fixed",
            inset: "auto 0 0 auto",
            right: OFFSET_X,
            bottom: OFFSET_Y,
            zIndex: Z,
            fontFamily:
                "-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif",
        },
    });

    // bubble btn
    const bubble = ce("button", {
        class: "zajuna-bubble-btn",
        type: "button",
        style: {
            width: "56px",
            height: "56px",
            borderRadius: "9999px",
            background: COLOR,
            color: "#fff",
            border: "0",
            cursor: "pointer",
            boxShadow:
                "0 10px 15px -3px rgba(0,0,0,.1), 0 4px 6px -2px rgba(0,0,0,.05)",
            display: "grid",
            placeItems: "center",
        },
        "aria-label": "Abrir chat",
    });

    const icon = ce("span", {
        class: "zajuna-bubble-icon",
        style: { display: "block", width: "22px", height: "22px" },
    });
    icon.innerHTML =
        ICON === "chat"
            ? `<svg viewBox="0 0 24 24" fill="currentColor" width="22" height="22" aria-hidden="true"><path d="M4 4h16a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H8l-4 4V6a2 2 0 0 1 2-2z"/></svg>`
            : `<svg viewBox="0 0 24 24" fill="currentColor" width="22" height="22" aria-hidden="true"><path d="M12 2a5 5 0 0 0-5 5v2H6a4 4 0 0 0-4 4v5h20v-5a4 4 0 0 0-4-4h-1V7a5 5 0 0 0-5-5z"/></svg>`;
    bubble.appendChild(icon);

    // pill minimizada (aparece cuando minimized=true)
    const pill = ce("button", {
        class: "zajuna-bubble-pill",
        type: "button",
        style: {
            display: "none",
            alignItems: "center",
            gap: "8px",
            maxWidth: "240px",
            borderRadius: "9999px",
            background: "#fff",
            color: "#111827",
            border: "1px solid rgba(0,0,0,.08)",
            padding: "8px 12px",
            boxShadow:
                "0 10px 15px -3px rgba(0,0,0,.1), 0 4px 6px -2px rgba(0,0,0,.05)",
            cursor: "pointer",
        },
        "aria-label": "Restaurar chat",
    });
    const pillDot = ce("span", {
        style: {
            width: "10px",
            height: "10px",
            borderRadius: "9999px",
            background: COLOR,
            display: "inline-block",
        },
    });
    const pillText = ce("span", {
        style: { fontSize: "12px", fontWeight: 600 },
    });
    pill.appendChild(pillDot);
    pill.appendChild(pillText);

    // panel
    const panel = ce("div", {
        class: "zajuna-bubble-panel",
        style: {
            position: "fixed",
            right: OFFSET_X,
            bottom: `calc(${OFFSET_Y} + 64px)`,
            width: WIDTH,
            height: HEIGHT,
            maxWidth: "92vw",
            maxHeight: "85vh",
            background: "#fff",
            color: "#111827",
            borderRadius: "16px",
            overflow: "hidden",
            border: "1px solid rgba(0,0,0,.08)",
            boxShadow:
                "0 25px 50px -12px rgba(0,0,0,.25), 0 10px 15px -3px rgba(0,0,0,.1)",
            display: "none",
        },
    });
    const header = ce("div", {
        class: "zajuna-bubble-header",
        style: {
            height: "44px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "0 12px",
            background: "#f8fafc",
            borderBottom: "1px solid rgba(0,0,0,.06)",
            fontSize: "14px",
            fontWeight: 600,
        },
    });
    const title = ce("div", { textContent: TITLE });
    const headerBtns = ce("div", { style: { display: "flex", gap: "6px" } });

    const btnMin = ce("button", {
        type: "button",
        "aria-label": "Minimizar",
        style: baseTinyBtn(),
    });
    btnMin.innerHTML =
        '<svg viewBox="0 0 24 24" width="16" height="16"><rect x="4" y="11" width="16" height="2" fill="currentColor"/></svg>';

    const btnClose = ce("button", {
        type: "button",
        "aria-label": "Cerrar",
        style: baseTinyBtn(),
    });
    btnClose.innerHTML =
        '<svg viewBox="0 0 24 24" width="16" height="16"><path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>';

    headerBtns.appendChild(btnMin);
    headerBtns.appendChild(btnClose);
    header.appendChild(title);
    header.appendChild(headerBtns);

    const iframe = ce("iframe", {
        src: SRC,
        allow: ALLOW,
        sandbox: SANDBOX,
        referrerpolicy: "strict-origin-when-cross-origin",
        style: { width: "100%", height: `calc(100% - 44px)`, border: "0" },
    });

    panel.appendChild(header);
    panel.appendChild(iframe);

    // montar
    root.appendChild(panel);
    root.appendChild(pill);
    root.appendChild(bubble);
    document.body.appendChild(root);

    // --- estilos tema/contraste reflectados en contenedor ---
    function applyThemeToChrome(theme) {
        const isDark = theme === "dark";
        panel.style.background = isDark ? "#0b0f1a" : "#fff";
        panel.style.color = isDark ? "#e5e7eb" : "#111827";
        header.style.background = isDark ? "#0f172a" : "#f8fafc";
        header.style.color = isDark ? "#e5e7eb" : "#111827";
        pill.style.background = isDark ? "#111827" : "#fff";
        pill.style.color = isDark ? "#e5e7eb" : "#111827";
    }

    // --- API pública ---
    function emit(type, payload) {
        try {
            state.onEvent && state.onEvent({ type, payload, ts: Date.now() });
        } catch (e) {
            // no-op
        }
    }

    function open() {
        state.open = true;
        state.minimized = false;
        panel.style.display = "block";
        pill.style.display = "none";
        bubble.style.display = "none";
        emit("open");
        // focus
        setTimeout(() => iframe?.contentWindow?.focus?.(), 0);
    }

    function close() {
        state.open = false;
        panel.style.display = "none";
        pill.style.display = "none";
        bubble.style.display = "grid";
        emit("close");
    }

    function toggle() {
        if (state.open) close();
        else open();
    }

    function minimize() {
        state.minimized = true;
        state.open = false;
        panel.style.display = "none";
        pill.style.display = "inline-flex";
        bubble.style.display = "none";
        refreshPill();
        emit("minimize");
    }

    function restore() {
        state.minimized = false;
        open();
        emit("restore");
    }

    function onEvent(fn) {
        state.onEvent = typeof fn === "function" ? fn : null;
    }

    // pill texto/emoji segun tema/idioma
    function refreshPill() {
        const lang = (state.language || "es").toUpperCase();
        const emoji = state.theme === "dark" ? "🌙" : "☀️";
        pillText.textContent = `Tutor Virtual · ${emoji} ${lang}`;
    }

    // eventos UI
    bubble.addEventListener("click", toggle);
    pill.addEventListener("click", restore);
    btnClose.addEventListener("click", close);
    btnMin.addEventListener("click", minimize);

    // --- Mensajería con iframe ---
    const iframeOrigin = (() => {
        try {
            return new URL(SRC).origin;
        } catch {
            return "*";
        }
    })();

    // auth bridge
    async function handleAuthNeeded() {
        if (AUTH_MODE === "demo") {
            sendAuthToken("FAKE_TOKEN_ZAJUNA");
            return;
        }
        if (AUTH_MODE === "custom" && typeof window.__zajunaGetAuthToken === "function") {
            try {
                const tok = await window.__zajunaGetAuthToken();
                if (tok) sendAuthToken(tok);
            } catch (e) {
                console.warn("[ZajunaBubble] __zajunaGetAuthToken() falló:", e);
            }
            return;
        }
        // none → no hacemos nada
    }

    function sendAuthToken(token) {
        try {
            iframe.contentWindow?.postMessage({ type: "auth:token", token }, iframeOrigin);
        } catch { }
    }

    // receptor global
    window.addEventListener("message", (ev) => {
        if (iframeOrigin !== "*" && ev.origin !== iframeOrigin) return;
        const data = ev.data || {};
        if (!data || typeof data !== "object") return;

        switch (data.type) {
            case "auth:needed":
                handleAuthNeeded();
                break;

            case "prefs:update": {
                const prevTheme = state.theme;
                const prevLang = state.language;
                if (data.prefs) {
                    if (data.prefs.theme) state.theme = data.prefs.theme;
                    if (data.prefs.language) state.language = data.prefs.language;
                    applyThemeToChrome(state.theme);
                    refreshPill();
                    if (prevTheme !== state.theme || prevLang !== state.language) {
                        emit("prefs", { theme: state.theme, language: state.language });
                    }
                }
                break;
            }

            case "telemetry": {
                // { type:"telemetry", event:"message_sent"|"message_received"|... , payload?:{} }
                if (data.event) emit(data.event, data.payload || {});
                break;
            }

            default:
                break;
        }
    });

    // iniciar
    applyThemeToChrome(state.theme);
    refreshPill();

    // Exponer API
    window.ZajunaBubble = {
        open,
        close,
        toggle,
        minimize,
        restore,
        onEvent,
        // lectura rápida de estado
        get state() {
            return { open: state.open, minimized: state.minimized, theme: state.theme, language: state.language };
        },
    };

    // estilos accesibles (focus)
    injectA11yStyles();

    // utils style
    function baseTinyBtn() {
        return {
            appearance: "none",
            border: "0",
            background: "transparent",
            color: "inherit",
            width: "28px",
            height: "28px",
            display: "grid",
            placeItems: "center",
            borderRadius: "8px",
            cursor: "pointer",
        };
    }

    function injectA11yStyles() {
        const s = ce("style");
        s.textContent = `
      .zajuna-bubble-btn:focus-visible,
      .zajuna-bubble-pill:focus-visible,
      .zajuna-bubble-panel button:focus-visible {
        outline: 2px solid ${COLOR};
        outline-offset: 2px;
      }
      .zajuna-bubble-panel button:hover { background: rgba(0,0,0,.05); }
    `;
        document.head.appendChild(s);
    }
})();
