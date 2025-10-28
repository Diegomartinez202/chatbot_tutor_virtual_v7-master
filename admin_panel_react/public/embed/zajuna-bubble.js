; (() => {
    const DEFAULTS = {
        iframeUrl: `${window.location.origin}/?embed=1`,
        allowedOrigin: window.location.origin,
        title: 'Tutor Virtual',
        subtitle: 'Sustentación',
        position: 'bottom-right', // bottom-right | bottom-left | top-right | top-left
        startOpen: false,
        theme: 'auto',            // auto | light | dark
        zIndex: 999999
    };

    function css(el, styles) {
        Object.assign(el.style, styles);
    }

    function create(options = {}) {
        const opts = { ...DEFAULTS, ...options };
        let root, btn, iframeWrap, iframeEl, isMounted = false, opened = false;
        const listeners = new Set(); // onEvent listeners

        function emit(evt) {
            // evt: { type: string, ... }
            for (const cb of listeners) {
                try { cb(evt) } catch { }
            }
        }

        function post(msg) {
            try {
                iframeEl?.contentWindow?.postMessage(msg, opts.allowedOrigin);
            } catch (e) {
                console.warn('[zajuna-bubble] postMessage error', e);
            }
        }

        function handleMessage(e) {
            if (opts.allowedOrigin !== '*' && e.origin !== opts.allowedOrigin) return;
            const data = e.data || {};
            // Normaliza eventos desde el iframe si tu app los emite
            // p.ej. { type: 'telemetry', ... } | { type: 'prefs:update', prefs: {theme,language} } | { type: 'auth:needed' }
            emit(data);
        }

        function setTheme(theme) {
            // Notifica al iframe (si lo soporta)
            post({ type: 'host:setTheme', theme });
            emit({ type: 'prefs:update', source: 'host', prefs: { theme } });
        }

        function setLanguage(language) {
            post({ type: 'host:setLanguage', language });
            emit({ type: 'prefs:update', source: 'host', prefs: { language } });
        }

        function sendAuthToken(token) {
            post({ type: 'host:auth', token });
            emit({ type: 'telemetry', event: 'auth_sent', tokenPreview: String(token).slice(0, 8) + '…' });
        }

        function open() {
            if (!isMounted) return;
            iframeWrap.hidden = false;
            opened = true;
            btn.setAttribute('aria-expanded', 'true');
            post({ type: 'host:open' });
            emit({ type: 'telemetry', event: 'open' });
        }

        function close() {
            if (!isMounted) return;
            iframeWrap.hidden = true;
            opened = false;
            btn.setAttribute('aria-expanded', 'false');
            post({ type: 'host:close' });
            emit({ type: 'telemetry', event: 'close' });
        }

        function toggle() {
            opened ? close() : open();
        }

        function isOpen() { return opened; }

        function mount() {
            if (isMounted) return;

            // raíz
            root = document.createElement('div');
            css(root, {
                position: 'fixed',
                zIndex: String(opts.zIndex),
                inset: 'auto',
                pointerEvents: 'none' // sólo elementos internos reciben eventos
            });

            // posición
            const pos = opts.position || 'bottom-right';
            const pad = '16px';
            const positions = {
                'bottom-right': { right: pad, bottom: pad },
                'bottom-left': { left: pad, bottom: pad },
                'top-right': { right: pad, top: pad },
                'top-left': { left: pad, top: pad }
            };
            css(root, positions[pos] || positions['bottom-right']);

            // botón
            btn = document.createElement('button');
            btn.type = 'button';
            btn.setAttribute('aria-expanded', 'false');
            btn.setAttribute('aria-label', opts.title || 'Abrir chat');
            btn.className = 'zj-bubble-button'; // estilo en zajuna-bubble.css
            btn.innerHTML = `
        <span class="zj-bubble-title">${opts.title || 'Chat'}</span>
        <span class="zj-bubble-sub">${opts.subtitle || ''}</span>
      `;
            css(btn, { pointerEvents: 'auto' });
            btn.addEventListener('click', toggle);

            // wrapper del iframe
            iframeWrap = document.createElement('div');
            iframeWrap.className = 'zj-bubble-iframe-wrap';
            css(iframeWrap, { pointerEvents: 'auto' });

            // iframe
            iframeEl = document.createElement('iframe');
            iframeEl.className = 'zj-bubble-iframe';
            iframeEl.src = opts.iframeUrl;
            iframeEl.setAttribute('allow', 'clipboard-write; clipboard-read; microphone; camera; autoplay');
            iframeEl.setAttribute('title', opts.title || 'Chat');
            iframeEl.setAttribute('sandbox', 'allow-scripts allow-same-origin allow-forms allow-popups allow-modals');
            iframeEl.addEventListener('load', () => {
                // enviar “hello” al iframe
                post({ type: 'host:hello', theme: opts.theme, language: 'es' });
            });

            iframeWrap.appendChild(iframeEl);
            root.appendChild(iframeWrap);
            root.appendChild(btn);
            document.body.appendChild(root);

            window.addEventListener('message', handleMessage);
            isMounted = true;

            // estado inicial
            if (opts.theme && opts.theme !== 'auto') setTheme(opts.theme);
            if (opts.startOpen) open(); else close();
        }

        function unmount() {
            if (!isMounted) return;
            try {
                window.removeEventListener('message', handleMessage);
                root?.remove();
            } catch { }
            isMounted = false;
            opened = false;
        }

        function onEvent(cb) {
            if (typeof cb === 'function') listeners.add(cb);
            return () => listeners.delete(cb);
        }

        return {
            // ciclo de vida
            mount, unmount,
            // visibilidad
            open, close, toggle, isOpen,
            // interacciones
            sendAuthToken,
            setTheme, setLanguage,
            // eventos
            onEvent
        };
    }

    window.ZajunaBubble = { create };
})();
