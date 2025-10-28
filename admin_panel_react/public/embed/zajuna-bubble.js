;; (() => {
    const DEFAULTS = {
        iframeUrl: `${window.location.origin}/?embed=1`,
        allowedOrigin: window.location.origin,
        title: 'Tutor Virtual',
        subtitle: 'Sustentación',
        position: 'bottom-right',
        startOpen: false,
        theme: 'auto',
        zIndex: 999999,
        showLabel: false,  // para que no tape inputs
        padding: 20,
        avatar: null       // 👈 NUEVO
    };

    function css(el, styles) { Object.assign(el.style, styles); }

    function create(options = {}) {
        const opts = { ...DEFAULTS, ...options };
        let root, btn, iframeWrap, iframeEl, isMounted = false, opened = false;
        const listeners = new Set();

        function emit(evt) { for (const cb of listeners) try { cb(evt) } catch { } }
        function post(msg) { try { iframeEl?.contentWindow?.postMessage(msg, opts.allowedOrigin); } catch { } }

        function open() { if (!isMounted) return; iframeWrap.hidden = false; opened = true; btn.setAttribute('aria-expanded', 'true'); post({ type: 'host:open' }); emit({ type: 'telemetry', event: 'open' }); }
        function close() { if (!isMounted) return; iframeWrap.hidden = true; opened = false; btn.setAttribute('aria-expanded', 'false'); post({ type: 'host:close' }); emit({ type: 'telemetry', event: 'close' }); }
        const toggle = () => (opened ? close() : open());
        const isOpen = () => opened;
        const onEvent = (cb) => (typeof cb === 'function' && listeners.add(cb), () => listeners.delete(cb));
        const setTheme = (theme) => (post({ type: 'host:setTheme', theme }), emit({ type: 'prefs:update', source: 'host', prefs: { theme } }));
        const setLanguage = (language) => (post({ type: 'host:setLanguage', language }), emit({ type: 'prefs:update', source: 'host', prefs: { language } }));
        const sendAuthToken = (token) => (post({ type: 'host:auth', token }), emit({ type: 'telemetry', event: 'auth_sent' }));

        function mount() {
            if (isMounted) return;
            root = document.createElement('div');
            css(root, { position: 'fixed', zIndex: String(opts.zIndex), inset: 'auto', pointerEvents: 'none' });

            const pad = (opts.padding ?? 16) + 'px';
            const positions = {
                'bottom-right': { right: pad, bottom: pad },
                'bottom-left': { left: pad, bottom: pad },
                'top-right': { right: pad, top: pad },
                'top-left': { left: pad, top: pad },
            };
            css(root, positions[opts.position] || positions['bottom-right']);

            // botón launcher
            btn = document.createElement('button');
            btn.type = 'button';
            btn.setAttribute('aria-expanded', 'false');
            btn.setAttribute('aria-label', opts.title || 'Abrir chat');
            btn.className = 'zj-bubble-button';
            css(btn, { pointerEvents: 'auto' });

            // avatar redondo si viene configurado
            if (opts.avatar) {
                btn.innerHTML = ''; // sin texto
                css(btn, {
                    width: '56px',
                    height: '56px',
                    borderRadius: '50%',
                    backgroundImage: `url("${opts.avatar}")`,
                    backgroundSize: 'cover',
                    backgroundPosition: 'center center',
                    backgroundRepeat: 'no-repeat',
                    border: '0',
                    boxShadow: '0 6px 18px rgba(0,0,0,.25)',
                });
            } else if (!opts.showLabel) {
                // ícono mínimo si no hay avatar ni label
                btn.innerHTML = '<span class="zj-bubble-dot"></span>';
            } else {
                // label clásico
                btn.innerHTML = `
          <span class="zj-bubble-title">${opts.title || 'Chat'}</span>
          <span class="zj-bubble-sub">${opts.subtitle || ''}</span>
        `;
            }
            btn.addEventListener('click', toggle);

            // contenedor del iframe
            iframeWrap = document.createElement('div');
            iframeWrap.className = 'zj-bubble-iframe-wrap';
            css(iframeWrap, { pointerEvents: 'auto' });

            iframeEl = document.createElement('iframe');
            iframeEl.className = 'zj-bubble-iframe';
            iframeEl.src = opts.iframeUrl;
            iframeEl.setAttribute('title', opts.title || 'Chat');
            iframeEl.setAttribute('allow', 'microphone; camera; clipboard-write; clipboard-read; autoplay');
            // si usas micrófono en embed, evita restricciones raras de sandbox:
            iframeEl.setAttribute('sandbox', 'allow-scripts allow-same-origin allow-forms allow-popups allow-modals allow-presentation');

            iframeEl.addEventListener('load', () => {
                post({ type: 'host:hello', theme: opts.theme, language: 'es' });
            });

            iframeWrap.appendChild(iframeEl);
            root.appendChild(iframeWrap);
            root.appendChild(btn);
            document.body.appendChild(root);

            isMounted = true;
            if (opts.theme && opts.theme !== 'auto') setTheme(opts.theme);
            if (opts.startOpen) open(); else close();
        }

        function unmount() { if (!isMounted) return; try { root?.remove(); } catch { } isMounted = false; opened = false; }

        return { mount, unmount, open, close, toggle, isOpen, onEvent, setTheme, setLanguage, sendAuthToken };
    }

    window.ZajunaBubble = { create };
})();
