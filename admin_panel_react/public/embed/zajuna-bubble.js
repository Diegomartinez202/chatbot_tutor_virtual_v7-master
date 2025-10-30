/* public/embed/zajuna-bubble.js */
; (() => {
    const DEFAULTS = {
        iframeUrl: `${window.location.origin}/?embed=1`,
        allowedOrigin: window.location.origin, // Usa "*" si hospedas el chat en otro dominio
        title: "Tutor Virtual",
        subtitle: "Sustentación",
        position: "bottom-right", // bottom-right | bottom-left | top-right | top-left
        startOpen: false,          // ⬅️ NO se abre solo al cargar
        theme: "auto",             // auto | light | dark
        zIndex: 2147483000,
        showLabel: false,          // false => botón flotante redondo
        padding: 20,
        width: 360,
        height: 520,
        draggable: true,           // ⬅️ Arrastrable
        closeOnEsc: true,
        closeOnOutsideClick: false,
        // 🖼️ avatar por defecto (puedes cambiarlo al inicializar)
        avatar: "/bot-avatar.png",
        // Permisos modernos para el iframe
        permissions: "microphone; camera; autoplay; clipboard-write; fullscreen",
        // Sandbox (no incluimos allow-same-origin si no hace falta para cookies)
        sandbox: "allow-scripts allow-forms allow-popups",
    };

    function css(el, styles) { Object.assign(el.style, styles); }

    function injectCssOnce() {
        if (document.getElementById("zj-bubble-styles")) return;
        const s = document.createElement("style");
        s.id = "zj-bubble-styles";
        s.textContent = `
      [data-zj-bubble]{opacity:0;transition:opacity .15s ease}
      .zj-bubble-button{
        display:flex;align-items:center;gap:.5rem;
        border:0;outline:0;cursor:pointer;
        border-radius:999px;padding:.5rem .75rem;
        box-shadow:0 10px 25px rgba(0,0,0,.18);
        background:#0f172a;color:#fff;font:600 14px/1 system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial, "Apple Color Emoji","Segoe UI Emoji";
      }
      .zj-bubble-button.zj-compact{
        width:56px;height:56px;justify-content:center;padding:0;border-radius:50%;
      }
      .zj-avatar-wrap{display:inline-flex}
      .zj-avatar{width:28px;height:28px;border-radius:50%;object-fit:cover}
      .zj-bubble-title{font-weight:700}
      .zj-bubble-sub{font-weight:400;opacity:.8;font-size:12px}
      .zj-bubble-iframe-wrap{
        position:relative; margin-bottom:.5rem;
        box-shadow:0 20px 48px rgba(0,0,0,.22);
        border-radius:16px; overflow:hidden; background:#fff;
      }
      .zj-bubble-iframe{border:0;display:block;width:100%;height:100%}
      .zj-drag-overlay{position:fixed;inset:0;cursor:grabbing;z-index:2147483646}
    `;
        document.head.appendChild(s);
    }

    function create(options = {}) {
        injectCssOnce();
        const opts = { ...DEFAULTS, ...options };

        let root, btn, iframeWrap, iframeEl;
        let isMounted = false;
        let opened = false;
        let dragging = false;
        let dragStart = null;
        let dragOrigin = null;

        const listeners = new Set();
        const onEvent = (cb) => (typeof cb === "function" ? (listeners.add(cb), () => listeners.delete(cb)) : () => { });
        const emit = (evt) => { for (const cb of listeners) { try { cb(evt); } catch { } } };

        function post(msg) {
            try {
                iframeEl?.contentWindow?.postMessage(
                    msg,
                    opts.allowedOrigin === "*" ? "*" : opts.allowedOrigin
                );
            } catch { }
        }

        function handleMessage(e) {
            if (opts.allowedOrigin !== "*" && e.origin !== opts.allowedOrigin) return;
            const data = e?.data || {};
            // Control remoto desde el iframe (opcional)
            if (data?.type === "widget:open") open();
            else if (data?.type === "widget:close") close();
            else if (data?.type === "widget:toggle") toggle();
            emit(data);
        }

        function applyPosition() {
            const pad = (opts.padding ?? 16) + "px";
            const positions = {
                "bottom-right": { right: pad, bottom: pad, left: "auto", top: "auto" },
                "bottom-left": { left: pad, bottom: pad, right: "auto", top: "auto" },
                "top-right": { right: pad, top: pad, left: "auto", bottom: "auto" },
                "top-left": { left: pad, top: pad, right: "auto", bottom: "auto" },
            };
            css(root, positions[opts.position] || positions["bottom-right"]);
        }

        function open() {
            if (!isMounted) return;
            iframeWrap.style.display = "block";
            opened = true;
            btn.setAttribute("aria-expanded", "true");
            post({ type: "host:open" });
            emit({ type: "telemetry", event: "open" });
        }

        function close() {
            if (!isMounted) return;
            iframeWrap.style.display = "none";
            opened = false;
            btn.setAttribute("aria-expanded", "false");
            post({ type: "host:close" });
            emit({ type: "telemetry", event: "close" });
        }

        const toggle = () => (opened ? close() : open());
        const isOpen = () => opened;

        const setTheme = (theme) => {
            post({ type: "host:setTheme", theme });
            emit({ type: "prefs:update", source: "host", prefs: { theme } });
        };
        const setLanguage = (language) => {
            post({ type: "host:setLanguage", language });
            emit({ type: "prefs:update", source: "host", prefs: { language } });
        };
        const sendAuthToken = (token) => {
            post({ type: "auth:token", token });
            emit({ type: "telemetry", event: "auth_sent" });
        };

        function clamp(v, min, max) { return Math.max(min, Math.min(max, v)); }

        function startDrag(ev) {
            if (!opts.draggable) return;
            dragging = true;
            const r = root.getBoundingClientRect();
            dragOrigin = { left: r.left, top: r.top };
            const p = ev.touches?.[0] || ev;
            dragStart = { x: p.clientX, y: p.clientY };

            // Para que no “tape” clicks mientras arrastras, usamos un overlay
            const overlay = document.createElement("div");
            overlay.className = "zj-drag-overlay";
            overlay.dataset.zjDrag = "1";
            document.body.appendChild(overlay);
        }

        function moveDrag(ev) {
            if (!dragging || !dragStart || !dragOrigin) return;
            const p = ev.touches?.[0] || ev;
            const dx = p.clientX - dragStart.x;
            const dy = p.clientY - dragStart.y;

            // Pasamos a posicionamiento absoluto para libre arrastre
            css(root, { right: "auto", bottom: "auto", left: "auto", top: "auto" });

            const nextLeft = dragOrigin.left + dx;
            const nextTop = dragOrigin.top + dy;

            const vw = Math.max(document.documentElement.clientWidth, window.innerWidth || 0);
            const vh = Math.max(document.documentElement.clientHeight, window.innerHeight || 0);
            const rect = root.getBoundingClientRect();
            const clampedLeft = clamp(nextLeft, 0, vw - rect.width);
            const clampedTop = clamp(nextTop, 0, vh - rect.height);

            css(root, { position: "fixed", left: `${clampedLeft}px`, top: `${clampedTop}px` });
        }

        function endDrag() {
            dragging = false;
            dragStart = null;
            dragOrigin = null;
            document.querySelectorAll('[data-zj-drag="1"]').forEach(el => el.remove());
        }

        function handleKey(ev) {
            if (!opts.closeOnEsc) return;
            if (ev.key === "Escape" && opened) close();
        }

        function handleOutsideClick(ev) {
            if (!opts.closeOnOutsideClick || !opened) return;
            if (!root.contains(ev.target)) close();
        }

        function mount() {
            if (isMounted) return;

            root = document.createElement("div");
            root.setAttribute("data-zj-bubble", "");
            css(root, {
                position: "fixed",
                zIndex: String(opts.zIndex),
                inset: "auto",
                // Truco: el contenedor no intercepta clicks; solo sus hijos
                pointerEvents: "none"
            });

            applyPosition();

            // Iframe container
            iframeWrap = document.createElement("div");
            iframeWrap.className = "zj-bubble-iframe-wrap";
            css(iframeWrap, {
                width: `${opts.width}px`,
                height: `${opts.height}px`,
                pointerEvents: "auto",
                display: "none", // ⬅️ inicia cerrado
                background: "#fff",
                borderRadius: "16px",
            });

            iframeEl = document.createElement("iframe");
            iframeEl.className = "zj-bubble-iframe";
            iframeEl.src = opts.iframeUrl;
            iframeEl.setAttribute("title", opts.title || "Chat");
            iframeEl.setAttribute("allow", opts.permissions || DEFAULTS.permissions);
            iframeEl.setAttribute("sandbox", opts.sandbox || DEFAULTS.sandbox);
            iframeEl.addEventListener("load", () => {
                post({ type: "host:hello", theme: opts.theme, language: "es" });
            });

            iframeWrap.appendChild(iframeEl);

            // Botón launcher
            btn = document.createElement("button");
            btn.type = "button";
            btn.setAttribute("aria-expanded", "false");
            btn.setAttribute("aria-label", opts.title || "Abrir chat");
            btn.className = "zj-bubble-button";
            css(btn, { pointerEvents: "auto" });

            const avatarWrap = document.createElement("span");
            avatarWrap.className = "zj-avatar-wrap";
            const avatarImg = document.createElement("img");
            avatarImg.className = "zj-avatar";
            avatarImg.alt = "bot avatar";
            avatarImg.src = opts.avatar || DEFAULTS.avatar;
            avatarWrap.appendChild(avatarImg);

            const titleEl = document.createElement("span");
            titleEl.className = "zj-bubble-title";
            titleEl.textContent = String(opts.title || "Chat");

            const subEl = document.createElement("span");
            subEl.className = "zj-bubble-sub";
            subEl.textContent = String(opts.subtitle || "");

            if (opts.showLabel === false) {
                btn.classList.add("zj-compact");
            } else {
                btn.appendChild(titleEl);
                btn.appendChild(subEl);
            }
            btn.prepend(avatarWrap);
            btn.addEventListener("click", toggle);

            // Draggable: permite arrastrar con mouse o touch
            if (opts.draggable) {
                const dragTarget = btn; // arrastrar desde el botón
                dragTarget.addEventListener("mousedown", (e) => {
                    // Evitamos conflicto con click-toggle si mantienes arrastrando
                    if (e.buttons === 1) startDrag(e);
                });
                dragTarget.addEventListener("touchstart", (e) => startDrag(e), { passive: true });
                window.addEventListener("mousemove", (e) => moveDrag(e));
                window.addEventListener("touchmove", (e) => moveDrag(e), { passive: false });
                window.addEventListener("mouseup", endDrag);
                window.addEventListener("touchend", endDrag);
            }

            // Ensamblado
            root.appendChild(iframeWrap);
            root.appendChild(btn);
            document.body.appendChild(root);

            // Eventos globales
            window.addEventListener("message", handleMessage);
            if (opts.closeOnEsc) window.addEventListener("keydown", handleKey);
            if (opts.closeOnOutsideClick) window.addEventListener("mousedown", handleOutsideClick);

            isMounted = true;

            // Preferencias iniciales
            if (opts.theme && opts.theme !== "auto") setTheme(opts.theme);

            // Estado inicial abierto/cerrado
            if (opts.startOpen) open(); else close();

            // Mostrar con fade-in
            document.querySelectorAll("[data-zj-bubble]").forEach(el => (el.style.opacity = "1"));
        }

        function unmount() {
            if (!isMounted) return;
            try {
                window.removeEventListener("message", handleMessage);
                window.removeEventListener("keydown", handleKey);
                window.removeEventListener("mousedown", handleOutsideClick);
                root?.remove();
            } catch { }
            isMounted = false;
            opened = false;
        }

        return {
            mount, unmount, open, close, toggle, isOpen,
            onEvent, setTheme, setLanguage, sendAuthToken
        };
    }

    window.ZajunaBubble = { create };

    // Auto-fade para los que se monten después
    window.addEventListener("load", () => {
        document.querySelectorAll("[data-zj-bubble]").forEach(el => el.style.opacity = "1");
    });
})();
