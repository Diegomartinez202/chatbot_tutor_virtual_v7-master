/* public/embed/zajuna-bubble.js */
; (() => {
    const DEFAULTS = {
        iframeUrl: `${window.location.origin}/hybrid-host.html`,
        // ✅ Se resuelve automáticamente desde iframeUrl si no lo pasas
        allowedOrigin: null,
        title: "Tutor Virtual",
        subtitle: "Sustentación",
        position: "bottom-right", // bottom-right | bottom-left | top-right | top-left
        startOpen: false,
        theme: "auto",            // auto | light | dark
        zIndex: 2147483000,
        showLabel: false,         // false => FAB redondo
        padding: 20,
        avatar: "/bot-avatar.png",

        // ✅ SOLO permisos necesarios (sin autoplay/clipboard-write)
        permissions: "microphone; camera; fullscreen",

        // Opciones extra
        draggable: true,
        closeOnEsc: true,
        closeOnOutsideClick: false,
        width: 380,
        height: 560,

        // 🔐 Bridge de auth
        autoSendToken: true,
        tokenStorageKey: "app:accessToken", // ajústalo a tu app
        tokenCookieName: "access_token",    // "" si no usas cookie

        // 🆕 (opcional) avatar de “cargando/typing” para el FAB
        loadingAvatar: "/bot-loading.png",
    };

    function css(el, styles) { Object.assign(el.style, styles); }

    // Lee token del host (localStorage y/o cookie)
    function readHostToken(opts) {
        try {
            const ls = localStorage.getItem(opts.tokenStorageKey);
            if (ls) return ls;
        } catch { }
        if (opts.tokenCookieName) {
            const m = document.cookie.match(new RegExp(`(?:^|; )${opts.tokenCookieName}=([^;]*)`));
            if (m) return decodeURIComponent(m[1]);
        }
        return null;
    }

    function create(options = {}) {
        // ▶️ allowedOrigin = origin(iframeUrl) si no se pasa
        const tmp = { ...DEFAULTS, ...options };
        if (!tmp.allowedOrigin) {
            try { tmp.allowedOrigin = new URL(tmp.iframeUrl).origin; }
            catch { tmp.allowedOrigin = "*"; }
        }
        const opts = tmp;

        let root, btn, iframeWrap, iframeEl, headerEl;
        // 🆕 referencias adicionales sin romper tu flujo:
        let avatarImgRef = null;      // referencia al <img> del FAB
        let isMounted = false;
        let opened = false;
        // 🆕 estado minimizado
        let minimized = false;

        const listeners = new Set();

        function emit(evt) { for (const cb of listeners) { try { cb(evt); } catch { } } }
        function onEvent(cb) {
            if (typeof cb === "function") { listeners.add(cb); return () => listeners.delete(cb); }
            return () => { };
        }

        function post(msg) {
            try {
                iframeEl?.contentWindow?.postMessage(msg, opts.allowedOrigin || "*");
            } catch { }
        }

        function setOpenState(next) {
            opened = !!next;
            root.classList.toggle("zj-open", opened);
            iframeWrap.setAttribute("aria-hidden", opened ? "false" : "true");
            btn.setAttribute("aria-expanded", opened ? "true" : "false");
        }

        function open() {
            if (!isMounted) return;
            setOpenState(true);
            post({ type: "host:open" });
            emit({ type: "telemetry", event: "open" });
            // 🆕 evento para persistencia del host
            emit({ type: "widget:opened" });
        }
        function close() {
            if (!isMounted) return;
            setOpenState(false);
            post({ type: "host:close" });
            emit({ type: "telemetry", event: "close" });
            // 🆕 evento para persistencia del host
            emit({ type: "widget:closed" });
        }
        const toggle = () => (opened ? close() : open());
        const isOpen = () => opened;

        // 🆕 Minimizar / restaurar (cambia altura vía clase CSS o estilo)
        function minimize(toMin = true) {
            minimized = !!toMin;
            root.classList.toggle("zj-min", minimized);
            emit({ type: minimized ? "widget:min" : "widget:restore" });
        }
        const isMinimized = () => minimized;

        // 🆕 Cambiar avatar del FAB en caliente
        function setAvatar(src) {
            try {
                if (!src) return;
                if (avatarImgRef) avatarImgRef.src = src;
                else {
                    // fallback: busca el img por DOM si aún no tenemos ref
                    const img = btn?.querySelector?.(".zj-avatar") || document.querySelector?.('[data-zj-fab] img');
                    if (img) img.src = src;
                }
            } catch { }
        }

        // 🔐 Enviar token hacia el iframe
        function sendAuthToken(token) {
            if (!token) return;
            post({ type: "auth:token", token });
            emit({ type: "telemetry", event: "auth_sent" });
        }

        // Mensajes desde el iframe
        function handleMessage(e) {
            // ✅ comparar contra el origen REAL del iframe
            if (opts.allowedOrigin !== "*" && e.origin !== opts.allowedOrigin) return;
            const data = e?.data || {};

            if (data.type === "widget:open") { open(); return; }
            if (data.type === "widget:close") { close(); return; }
            if (data.type === "widget:toggle") { toggle(); return; }

            // 🆕 soporta minimizar desde el iframe (si lo emite)
            if (data.type === "widget:minimize") { minimize(true); return; }
            if (data.type === "widget:restore") { minimize(false); return; }
            if (data.type === "widget:minToggle") { minimize(!minimized); return; }

            if (data.type === "auth:request") {
                const token = readHostToken(opts);
                if (token) sendAuthToken(token);
                else emit({ type: "auth:missing" });
                return;
            }

            if (data.type === "auth:needed") {
                // Aquí podrías abrir tu modal de login del host
                // if (window.showLoginModal) window.showLoginModal();
                return;
            }

            // 🆕 si el iframe reenvía typing, emítelo y (opcional) cambia avatar
            if (data.type === "bot:typing") {
                emit({ type: "bot:typing", active: !!data.active });
                if (opts.loadingAvatar) {
                    setAvatar(data.active ? opts.loadingAvatar : opts.avatar || DEFAULTS.avatar);
                }
                return;
            }

            emit(data);
        }

        const setTheme = (theme) => { post({ type: "host:setTheme", theme }); emit({ type: "prefs:update", source: "host", prefs: { theme } }); };
        const setLanguage = (language) => { post({ type: "host:setLanguage", language }); emit({ type: "prefs:update", source: "host", prefs: { language } }); };

        /* ──────────────── Drag support ──────────────── */
        function makeDraggable(handle) {
            if (!opts.draggable) return;
            let startX, startY, startLeft, startTop, dragging = false;

            handle.style.cursor = "grab";
            handle.addEventListener("pointerdown", (ev) => {
                dragging = true;
                handle.setPointerCapture(ev.pointerId);
                handle.style.cursor = "grabbing";
                const rect = root.getBoundingClientRect();
                startX = ev.clientX;
                startY = ev.clientY;
                startLeft = rect.left;
                startTop = rect.top;
            });
            handle.addEventListener("pointermove", (ev) => {
                if (!dragging) return;
                const dx = ev.clientX - startX;
                const dy = ev.clientY - startY;
                css(root, { left: `${startLeft + dx}px`, top: `${startTop + dy}px`, right: "auto", bottom: "auto" });
            });
            handle.addEventListener("pointerup", (ev) => {
                dragging = false;
                handle.releasePointerCapture?.(ev.pointerId);
                handle.style.cursor = "grab";
            });
        }

        /* ──────────────── MONTAJE ──────────────── */
        function mount() {
            if (isMounted) return;

            // Contenedor raíz
            root = document.createElement("div");
            root.setAttribute("data-zj-bubble", "");
            root.className = "zj-bubble-root";
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
            // 🆕 marca para selectores opcionales desde host
            btn.setAttribute("data-zj-fab", "");
            css(btn, { pointerEvents: "auto" });
            btn.addEventListener("click", toggle);

            // Avatar + labels
            const avatarWrap = document.createElement("span");
            avatarWrap.className = "zj-avatar-wrap";
            const avatarImg = document.createElement("img");
            avatarImg.className = "zj-avatar";
            avatarImg.alt = "bot avatar";
            avatarImg.src = opts.avatar || DEFAULTS.avatar;
            avatarWrap.appendChild(avatarImg);
            // 🆕 guarda referencia sin romper tu const local
            avatarImgRef = avatarImg;

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

            // Wrapper del iframe
            iframeWrap = document.createElement("div");
            iframeWrap.className = "zj-bubble-iframe-wrap";
            css(iframeWrap, {
                pointerEvents: "auto",
                width: `${opts.width}px`,
                height: `${opts.height}px`,
            });
            // Accesibilidad/estado visible
            iframeWrap.setAttribute("aria-hidden", "true");

            // Barra de drag
            headerEl = document.createElement("div");
            headerEl.className = "zj-bubble-dragbar";
            headerEl.title = "Arrastrar";
            iframeWrap.appendChild(headerEl);
            // 🆕 doble click para minimizar/restaurar
            headerEl.addEventListener("dblclick", () => minimize(!minimized));

            // Iframe
            const iframeUrl = opts.iframeUrl;

            iframeEl = document.createElement("iframe");
            iframeEl.className = "zj-bubble-iframe";
            iframeEl.src = iframeUrl;
            iframeEl.setAttribute("title", opts.title || "Chat");

            // ✅ SOLO permisos necesarios (sin autoplay/clipboard-write)
            iframeEl.allow = "microphone; camera";

            // Sandbox: necesario para app embebida (nota: same-origin + scripts reduce confinamiento)
            iframeEl.setAttribute("sandbox", "allow-scripts allow-forms allow-popups");

            iframeEl.addEventListener("load", () => {
                post({ type: "host:hello", theme: opts.theme, language: "es" });

                // 🔐 Enviar token automáticamente si existe en el host
                if (opts.autoSendToken) {
                    const t = readHostToken(opts);
                    if (t) {
                        post({ type: "auth:token", token: t });
                        emit({ type: "telemetry", event: "auth_sent" });
                    }
                }
            });

            iframeWrap.appendChild(iframeEl);
            root.appendChild(iframeWrap);
            root.appendChild(btn);
            document.body.appendChild(root);

            // Eventos globales
            window.addEventListener("message", handleMessage);
            if (opts.closeOnEsc) {
                window.addEventListener("keydown", (ev) => { if (ev.key === "Escape" && opened) close(); });
            }
            if (opts.closeOnOutsideClick) {
                document.addEventListener("mousedown", (ev) => {
                    if (!opened) return;
                    const t = ev.target;
                    if (root && !root.contains(t)) close();
                }, true);
            }

            // Drag
            makeDraggable(headerEl);

            isMounted = true;

            // Tema inicial
            if (opts.theme && opts.theme !== "auto") setTheme(opts.theme);

            // 🚪 Estado inicial: por defecto CERRADO (evita “flash abierto”)
            setOpenState(false);
            if (opts.startOpen) open(); else close();
            // 🆕 si alguien precargó minimizado desde fuera, respétalo
            if (minimized) minimize(true);
        }

        function unmount() {
            if (!isMounted) return;
            try {
                window.removeEventListener("message", handleMessage);
                root?.remove();
            } catch { }
            isMounted = false;
            opened = false;
            minimized = false;
        }

        // Inyección mínima de estilos (fallback)
        (function ensureStyles() {
            if (document.getElementById("zj-bubble-styles")) return;
            const st = document.createElement("style");
            st.id = "zj-bubble-styles";
            st.textContent = `
        .zj-bubble-iframe-wrap { 
          position: relative;
          margin-bottom: 10px;
          border-radius: 12px; 
          overflow: hidden; 
          box-shadow: 0 12px 32px rgba(0,0,0,.2);
          opacity: 0; transform: translateY(6px); 
          transition: opacity .18s ease, transform .18s ease; 
          display: none;
          background: #0000;
        }
        .zj-bubble-root.zj-open .zj-bubble-iframe-wrap { 
          display: block; 
          opacity: 1; transform: translateY(0);
        }
        .zj-bubble-button { 
          pointer-events: auto; border: none; border-radius: 9999px; 
          background: #4f46e5; color: #fff; 
          padding: 10px; display: inline-flex; align-items: center; gap: 8px; 
          box-shadow: 0 8px 20px rgba(79,70,229,.35);
        }
        .zj-compact { width: 56px; height: 56px; padding: 0; justify-content: center; }
        .zj-avatar-wrap{ display:inline-grid; place-items:center; width:28px; height:28px; border-radius:9999px; overflow:hidden; background:#fff; }
        .zj-avatar{ width:100%; height:100%; object-fit:cover; }
        .zj-bubble-title{ font-weight:600; font-size:14px; color:#fff; line-height:1; }
        .zj-bubble-sub{ font-size:11px; color:#e0e7ff; line-height:1; }
        .zj-bubble-iframe{ width:100%; height:100%; border:0; background:#fff; }
        .zj-bubble-dragbar{ position:absolute; top:0; left:0; right:0; height:10px; cursor:grab; background:transparent; z-index:2; }
        /* 🆕 estado minimizado (si el host añade .zj-min) */
        .zj-bubble-root.zj-min .zj-bubble-iframe-wrap{ height:56px !important; }
      `;
            document.head.appendChild(st);
        })();

        // 🔁 API pública (se añaden métodos nuevos sin quitar los tuyos)
        return {
            mount,
            unmount,
            open,
            close,
            toggle,
            isOpen,
            onEvent,
            setTheme,
            setLanguage,
            sendAuthToken,
            // 🆕 nuevos métodos expuestos:
            minimize,
            isMinimized,
            setAvatar,
        };
    }

    window.ZajunaBubble = { create };
    window.addEventListener("load", () => {
        document.querySelectorAll("[data-zj-bubble]").forEach(el => el.style.opacity = "1");
    });
})();
