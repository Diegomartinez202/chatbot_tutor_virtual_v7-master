/* public/embed/zajuna-bubble.js */
; (() => {
    const DEFAULTS = {
        iframeUrl: `${window.location.origin}/?embed=1`,
        allowedOrigin: window.location.origin,
        title: "Tutor Virtual",
        subtitle: "Sustentación",
        position: "bottom-right", // bottom-right | bottom-left | top-right | top-left
        startOpen: false,
        theme: "auto",            // auto | light | dark
        zIndex: 2147483000,
        showLabel: false,         // false => FAB redondo
        padding: 20,
        // 🖼️ avatar por defecto (puedes pasarlo desde React con options.avatar)
        avatar: "/bot-avatar.png",
        // Permisos modernos para el iframe
        permissions: "microphone; camera; autoplay; clipboard-write; fullscreen",
    };

    function css(el, styles) { Object.assign(el.style, styles); }

    function create(options = {}) {
        const opts = { ...DEFAULTS, ...options };

        let root, btn, iframeWrap, iframeEl;
        let isMounted = false;
        let opened = false;
        const listeners = new Set();

        function emit(evt) { for (const cb of listeners) { try { cb(evt); } catch { } } }
        function onEvent(cb) {
            if (typeof cb === "function") { listeners.add(cb); return () => listeners.delete(cb); }
            return () => { };
        }
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
            emit(e?.data || {});
        }

        function open() {
            if (!isMounted) return;
            iframeWrap.hidden = false;
            opened = true;
            btn.setAttribute("aria-expanded", "true");
            post({ type: "host:open" });
            emit({ type: "telemetry", event: "open" });
        }
        function close() {
            if (!isMounted) return;
            iframeWrap.hidden = true;
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

        function mount() {
            if (isMounted) return;

            root = document.createElement("div");
            root.setAttribute("data-zj-bubble", "");
            css(root, { position: "fixed", zIndex: String(opts.zIndex), inset: "auto", pointerEvents: "none" });

            const pad = (opts.padding ?? 16) + "px";
            const positions = {
                "bottom-right": { right: pad, bottom: pad },
                "bottom-left": { left: pad, bottom: pad },
                "top-right": { right: pad, top: pad },
                "top-left": { left: pad, top: pad },
            };
            css(root, positions[opts.position] || positions["bottom-right"]);

            // Botón launcher
            btn = document.createElement("button");
            btn.type = "button";
            btn.setAttribute("aria-expanded", "false");
            btn.setAttribute("aria-label", opts.title || "Abrir chat");
            btn.className = "zj-bubble-button";
            css(btn, { pointerEvents: "auto" });

            // avatar + (opcional label)
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

            // Iframe
            iframeWrap = document.createElement("div");
            iframeWrap.className = "zj-bubble-iframe-wrap";
            css(iframeWrap, { pointerEvents: "auto" });

            iframeEl = document.createElement("iframe");
            iframeEl.className = "zj-bubble-iframe";
            iframeEl.src = opts.iframeUrl;
            iframeEl.setAttribute("title", opts.title || "Chat");
            iframeEl.setAttribute("allow", opts.permissions || DEFAULTS.permissions);
            iframeEl.setAttribute("sandbox", "allow-same-origin allow-scripts allow-forms allow-popups");

            iframeEl.addEventListener("load", () => {
                post({ type: "host:hello", theme: opts.theme, language: "es" });
            });

            iframeWrap.appendChild(iframeEl);
            root.appendChild(iframeWrap);
            root.appendChild(btn);
            document.body.appendChild(root);

            window.addEventListener("message", handleMessage);
            isMounted = true;

            if (opts.theme && opts.theme !== "auto") setTheme(opts.theme);
            if (opts.startOpen) open(); else close();
        }

        function unmount() {
            if (!isMounted) return;
            try {
                window.removeEventListener("message", handleMessage);
                root?.remove();
            } catch { }
            isMounted = false;
            opened = false;
        }

        return { mount, unmount, open, close, toggle, isOpen, onEvent, setTheme, setLanguage, sendAuthToken };
    }

    window.ZajunaBubble = { create };
    window.addEventListener("load", () => {
        document.querySelectorAll("[data-zj-bubble]").forEach(el => el.style.opacity = "1");
    });
})();
