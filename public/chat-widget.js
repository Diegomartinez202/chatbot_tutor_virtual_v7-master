/* public/chat-widget.js — launcher moderno con auth handshake + CustomEvent telemetry */
(function () {
    const LS_KEY = "ctv_widget_settings";
    const ONE = 1;

    const DEFAULTS = {
        iconUrl: new URL("bot-avatar.png", document.baseURI).pathname,
        title: "Abrir chat",
        buttonPosition: "bottom-right",
        size: 64,
        offset: 24,
        zIndex: 2147483600,
        iframeSrc: "/chat-embed.html?embed=1",
        panelWidth: "380px",
        panelHeight: "560px",
        overlay: true,
        escClose: true,
        iframeTitle: "Chat",
        allow: "clipboard-write",
        sandbox: "allow-scripts allow-forms allow-same-origin allow-popups",
        allowedOrigins: [],           // p.ej. ["https://app.zajuna.edu"]
        loginUrl: "",                 // p.ej. "https://zajuna.edu/login"
        badge: "",                    // "", "auto" o número
        autoinit: true,
    };

    const toBool = (v, def) => { if (v == null || v === "") return !!def; const s = String(v).toLowerCase(); if (["true", "1", "yes"].includes(s)) return true; if (["false", "0", "no"].includes(s)) return false; return !!def; };
    const clampInt = (v, fb) => Number.isFinite(Number(v)) ? Number(v) : fb;
    const str = (v, fb) => (v == null || v === "" ? fb : String(v));
    const arr = (v) => String(v || "").split(",").map(s => s.trim()).filter(Boolean);

    function normalizeOrigin(o) {
        return String(o || "").trim().replace(/\/+$/, "");
    }

    function readAttrsFromScript(el) {
        return {
            iconUrl: str(el.getAttribute("data-avatar"), DEFAULTS.iconUrl),
            title: str(el.getAttribute("data-title"), DEFAULTS.title),
            buttonPosition: str(el.getAttribute("data-position"), DEFAULTS.buttonPosition),
            size: clampInt(el.getAttribute("data-size"), DEFAULTS.size),
            offset: clampInt(el.getAttribute("data-offset"), DEFAULTS.offset),
            zIndex: clampInt(el.getAttribute("data-z-index"), DEFAULTS.zIndex),
            iframeSrc: str(el.getAttribute("data-chat-url"), DEFAULTS.iframeSrc),
            panelWidth: str(el.getAttribute("data-panel-width"), DEFAULTS.panelWidth),
            panelHeight: str(el.getAttribute("data-panel-height"), DEFAULTS.panelHeight),
            overlay: toBool(el.getAttribute("data-overlay"), DEFAULTS.overlay),
            escClose: toBool(el.getAttribute("data-close-on-esc"), DEFAULTS.escClose),
            iframeTitle: str(el.getAttribute("data-iframe-title"), DEFAULTS.iframeTitle),
            allow: str(el.getAttribute("data-allow"), DEFAULTS.allow),
            sandbox: str(el.getAttribute("data-sandbox"), DEFAULTS.sandbox),
            allowedOrigins: arr(el.getAttribute("data-allowed-origins")),
            loginUrl: str(el.getAttribute("data-login-url"), DEFAULTS.loginUrl),
            badge: str(el.getAttribute("data-badge"), DEFAULTS.badge),
            autoinit: toBool(el.getAttribute("data-autoinit"), DEFAULTS.autoinit),
        };
    }

    const getSavedSettings = () => {
        try {
            return { theme: "light", contrast: false, lang: "es", ...(JSON.parse(localStorage.getItem(LS_KEY) || "null") || {}) };
        } catch { return { theme: "light", contrast: false, lang: "es" }; }
    };
    const saveSettings = (s) => { try { localStorage.setItem(LS_KEY, JSON.stringify(s)); } catch { } };

    function applyPanelSkin({ panel, header, overlay, state }) {
        if (state.theme === "dark") {
            panel.style.background = "#0f172a"; panel.style.borderColor = "#1f2937"; header.style.background = "#0b1220";
            if (overlay) overlay.style.background = "rgba(0,0,0,.35)"; panel.style.color = "#e5e7eb";
        } else {
            panel.style.background = "#ffffff"; panel.style.borderColor = "#e5e7eb"; header.style.background = "#0f172a";
            if (overlay) overlay.style.background = "rgba(0,0,0,.12)"; panel.style.color = "#111827";
        }
        panel.style.borderWidth = state.contrast ? "2px" : "1px";
    }

    function buildInstance(cfg) {
        const state = getSavedSettings();

        const btn = document.createElement("button");
        btn.type = "button";
        btn.setAttribute("aria-label", cfg.title);
        btn.setAttribute("title", cfg.title);
        btn.setAttribute("aria-expanded", "false");
        btn.style.cssText = `
      position:fixed;
      ${cfg.buttonPosition.includes("left") ? "left" : "right"}:${cfg.offset}px;
      bottom:${cfg.offset}px;
      width:${cfg.size}px; height:${cfg.size}px; border-radius:50%;
      border:none; padding:0; cursor:pointer; background:#fff;
      box-shadow:0 10px 20px rgba(0,0,0,.15);
      z-index:${cfg.zIndex + ONE};
    `;
        const img = document.createElement("img");
        img.src = cfg.iconUrl; img.alt = "Chatbot";
        img.style.cssText = `width:${cfg.size}px;height:${cfg.size}px;border-radius:50%;object-fit:cover;display:block;`;
        btn.appendChild(img);

        // Badge
        let badge;
        const setBadge = (n) => {
            if (!badge) {
                badge = document.createElement("span");
                badge.style.cssText = `
          position:absolute; ${cfg.buttonPosition.includes("left") ? "left" : "right"}:-6px; top:-6px;
          min-width:18px; height:18px; padding:0 4px; border-radius:999px; background:#ef4444;
          color:white; font:11px/18px system-ui, sans-serif; text-align:center;
        `;
                btn.appendChild(badge);
            }
            badge.textContent = String(n);
            badge.style.display = n > 0 ? "inline-block" : "none";
        };
        if (cfg.badge && !isNaN(Number(cfg.badge))) setBadge(Number(cfg.badge));

        // Overlay + panel
        const ov = document.createElement("div");
        ov.style.cssText = `position:fixed; inset:0; background:rgba(0,0,0,.12); display:none; z-index:${cfg.zIndex};`;

        const panel = document.createElement("div");
        panel.setAttribute("role", "dialog"); panel.setAttribute("aria-modal", "true"); panel.setAttribute("aria-label", "Chat");
        panel.style.cssText = `
      position:fixed;
      ${cfg.buttonPosition.includes("left") ? "left" : "right"}:${cfg.offset}px;
      bottom:${cfg.offset + cfg.size + 12}px;
      width:${cfg.panelWidth}; height:${cfg.panelHeight};
      background:white; border:1px solid #e5e7eb; border-radius:16px;
      box-shadow:0 10px 30px rgba(0,0,0,.15); overflow:hidden; display:none;
      z-index:${cfg.zIndex + ONE + ONE};
    `;

        const header = document.createElement("div");
        header.style.cssText = `
      height:40px; background:#0f172a; color:#fff; display:flex; align-items:center; justify-content:space-between;
      padding:0 8px; font:13px/1 system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Arial;
    `;
        header.innerHTML = `
      <div style="display:flex;align-items:center;gap:8px">
        <img src="${cfg.iconUrl}" alt="Bot" style="width:22px;height:22px;border-radius:50%;object-fit:cover"/>
        <strong style="font-weight:600">${cfg.title || "Chat"}</strong>
      </div>
      <div style="display:flex;align-items:center;gap:8px">
        <label style="display:inline-flex;align-items:center;gap:6px;cursor:pointer">
          <input type="checkbox" id="wgt-theme" /> <span>Tema oscuro</span>
        </label>
        <label style="display:inline-flex;align-items:center;gap:6px;cursor:pointer">
          <input type="checkbox" id="wgt-contrast" /> <span>Alto contraste</span>
        </label>
        <select id="wgt-lang" aria-label="Idioma" style="background:#111827;color:#fff;border:1px solid #374151;border-radius:6px;padding:2px 6px">
          <option value="es">ES</option>
          <option value="en">EN</option>
        </select>
        <button id="wgt-close" title="Cerrar" aria-label="Cerrar"
          style="background:transparent;color:#fff;border:0;font-size:18px;cursor:pointer;line-height:1">×</button>
      </div>
    `;
        panel.appendChild(header);

        const content = document.createElement("div");
        content.style.cssText = "width:100%; height:calc(100% - 40px);";
        panel.appendChild(content);

        // Responsive
        const mq = window.matchMedia("(max-width: 480px)");
        const applyMobile = () => {
            if (mq.matches) { panel.style.width = "94vw"; panel.style.height = "70vh"; panel.style[cfg.buttonPosition.includes("left") ? "left" : "right"] = "3vw"; }
            else { panel.style.width = cfg.panelWidth; panel.style.height = cfg.panelHeight; panel.style[cfg.buttonPosition.includes("left") ? "left" : "right"] = `${cfg.offset}px`; }
        };
        applyMobile(); mq.addEventListener?.("change", applyMobile);

        // Iframe
        let frame;
        if (cfg.iframeSrc) {
            frame = document.createElement("iframe");
            frame.src = cfg.iframeSrc;
            frame.title = cfg.iframeTitle || "Chat";
            frame.loading = "eager";
            frame.referrerPolicy = "no-referrer";
            frame.allow = cfg.allow;
            frame.sandbox = cfg.sandbox;
            frame.style.cssText = "width:100%; height:100%; border:0;";
            content.appendChild(frame);
        }

        // Seguridad postMessage
        let target = "*";
        let originAllowedStrict = () => false;

        if (frame) {
            const frameURL = new URL(frame.src, window.location.href);
            const frameOrigin = normalizeOrigin(frameURL.origin);
            const allowedSet = new Set(
                (cfg.allowedOrigins && cfg.allowedOrigins.length ? cfg.allowedOrigins : [frameOrigin])
                    .map(normalizeOrigin)
            );
            originAllowedStrict = (origin, source) =>
                source === frame.contentWindow && allowedSet.has(normalizeOrigin(origin));
            target = frameOrigin;
        }

        const open = () => {
            if (cfg.overlay) ov.style.display = "block";
            panel.style.display = "block";
            btn.setAttribute("aria-expanded", "true");
            if (cfg.badge === "auto") setBadge(0);
            // 🔔 Telemetría
            try { window.dispatchEvent(new CustomEvent("ctv:widget-opened")); } catch { }
            if (frame?.contentWindow) {
                frame.contentWindow.postMessage({ type: "chat:settings", ...state }, target);
                frame.contentWindow.postMessage({ type: "chat:visibility", open: true }, target);
            }
        };
        const close = () => {
            if (cfg.overlay) ov.style.display = "none";
            panel.style.display = "none";
            btn.setAttribute("aria-expanded", "false");
            // 🔔 Telemetría
            try { window.dispatchEvent(new CustomEvent("ctv:widget-closed")); } catch { }
            if (frame?.contentWindow) {
                frame.contentWindow.postMessage({ type: "chat:visibility", open: false }, target);
            }
        };

        btn.addEventListener("click", () => (panel.style.display === "block" ? close() : open()));
        if (cfg.overlay) ov.addEventListener("click", (e) => { if (e.target === ov) close(); });
        document.addEventListener("keydown", (e) => { if (cfg.escClose && e.key === "Escape") close(); });

        document.body.appendChild(btn);
        if (cfg.overlay) document.body.appendChild(ov);
        document.body.appendChild(panel);

        // Header toggles
        const themeToggle = header.querySelector("#wgt-theme");
        const contrastToggle = header.querySelector("#wgt-contrast");
        const langSelect = header.querySelector("#wgt-lang");
        const closeBtn = header.querySelector("#wgt-close");

        const applyAndNotify = () => {
            applyPanelSkin({ panel, header, overlay: ov, state });
            saveSettings(state);
            if (frame?.contentWindow) frame.contentWindow.postMessage({ type: "chat:settings", ...state }, target);
        };
        themeToggle.checked = state.theme === "dark";
        contrastToggle.checked = !!state.contrast;
        langSelect.value = state.lang || "es";
        themeToggle.addEventListener("change", () => { state.theme = themeToggle.checked ? "dark" : "light"; applyAndNotify(); });
        contrastToggle.addEventListener("change", () => { state.contrast = contrastToggle.checked; applyAndNotify(); });
        langSelect.addEventListener("change", () => { state.lang = langSelect.value || "es"; applyAndNotify(); });
        closeBtn.addEventListener("click", close);
        applyAndNotify();

        // Handshake + badge
        window.addEventListener("message", (ev) => {
            if (!originAllowedStrict(ev.origin, ev.source)) return;
            const data = ev.data || {};

            // badge auto
            if (data.type === "chat:badge" && typeof data.count === "number") {
                const isOpen = panel.style.display === "block";
                if (cfg.badge === "auto") setBadge(isOpen ? 0 : data.count);
                // 🔔 Telemetría
                try { window.dispatchEvent(new CustomEvent("ctv:badge", { detail: { count: data.count } })); } catch { }
            }

            // auth handshake
            if (data.type === "auth:needed" && frame?.contentWindow) {
                const token =
                    (typeof window.getZajunaToken === "function" && window.getZajunaToken()) ||
                    window.ZAJUNA_TOKEN ||
                    localStorage.getItem("zajuna_token");

                if (token) {
                    frame.contentWindow.postMessage({ type: "auth:token", token }, target);
                } else if (cfg.loginUrl) {
                    const redirect = location.href;
                    window.top.location.assign(`${cfg.loginUrl}?redirect=${encodeURIComponent(redirect)}`);
                }
            }
        });

        // Reenvía settings al cargar
        frame?.addEventListener("load", () => {
            try { frame.contentWindow.postMessage({ type: "chat:settings", ...state }, target); } catch { }
        });

        return {
            cfg,
            btn,
            overlay: ov,
            panel,
            iframe: frame,
            open,
            close,
            destroy() { try { btn.remove(); ov.remove(); panel.remove(); } catch { } }
        };
    }

    function unmount() {
        const inst = window.__ChatWidgetInstance;
        if (!inst) return;
        inst.destroy();
        window.__ChatWidgetInstance = null;
        const st = document.querySelector('style[data-chat-widget]');
        if (st) st.remove();
    }
    function mount(options = {}) {
        unmount();
        const inst = buildInstance({ ...DEFAULTS, ...options });
        window.__ChatWidgetInstance = inst;
        return inst;
    }
    function open() { window.__ChatWidgetInstance?.open?.(); }
    function close() { window.__ChatWidgetInstance?.close?.(); }
    window.ChatWidget = { mount, unmount, open, close };

    try {
        const el = document.currentScript;
        if (!el) return;
        const cfg = readAttrsFromScript(el);
        if (!cfg.autoinit) return;
        const hasData = [
            "data-chat-url", "data-avatar", "data-title", "data-position",
            "data-panel-width", "data-panel-height", "data-login-url", "data-allowed-origins"
        ].some(a => el.hasAttribute(a));
        if (hasData) mount({
            iconUrl: cfg.iconUrl, title: cfg.title, buttonPosition: cfg.buttonPosition, size: cfg.size, offset: cfg.offset,
            zIndex: cfg.zIndex, iframeSrc: cfg.iframeSrc, panelWidth: cfg.panelWidth, panelHeight: cfg.panelHeight,
            overlay: cfg.overlay, escClose: cfg.escClose, iframeTitle: cfg.iframeTitle, allow: cfg.allow, sandbox: cfg.sandbox,
            allowedOrigins: cfg.allowedOrigins, loginUrl: cfg.loginUrl, badge: cfg.badge,
        });
    } catch { }
})();