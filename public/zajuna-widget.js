(() => {
    const s = document.currentScript?.dataset || {};
    const origin = (s.origin || window.location.origin).replace(/\/$/, "");
    const pathEmbed = s.pathEmbed || "/chat-embed.html";
    const chatSrc = s.chatSrc || "/chat?embed=1";
    const width = s.width || "380px";
    const height = s.height || "560px";
    const title = s.title || "Chatbot Tutor Virtual";
    const allow = s.allow || "clipboard-write";
    const sandbox = s.sandbox || "allow-scripts allow-forms allow-same-origin allow-popups";
    const z = Number.isFinite(Number(s.zIndex)) ? Number(s.zIndex) : 9999;

    const defaultAvatar = new URL("bot-avatar.png", document.baseURI).pathname;
    const url = `${origin}${pathEmbed}?src=${encodeURIComponent(chatSrc)}&w=${encodeURIComponent(width)}&h=${encodeURIComponent(height)}&title=${encodeURIComponent(title)}&avatar=${encodeURIComponent(s.avatar || defaultAvatar)}`;

    const style = document.createElement("style");
    style.textContent = `
    .zj-launcher {
      position:fixed; right:20px; bottom:20px;
      width:56px; height:56px; border-radius:999px;
      border:0; cursor:pointer; background:#2563eb; color:#fff;
      box-shadow:0 10px 20px rgba(0,0,0,.25);
      font-size:24px; z-index:${z + 1};
      display:flex; align-items:center; justify-content:center;
      transition:all .3s ease; user-select:none;
    }
    .zj-frame {
      position:fixed; right:20px; bottom:90px;
      width:${width}; height:${height};
      border:0; border-radius:16px;
      box-shadow:0 20px 40px rgba(0,0,0,.25);
      display:none; z-index:${z};
      user-select:none;
    }
    .zj-frame.open { display:block; }
    .zj-launcher.minimized {
      width:42px; height:42px; font-size:18px;
      background:#1d4ed8; opacity:.9;
    }
    @media (max-width:480px){
      .zj-frame { width:94vw; height:70vh; right:3vw; }
    }
  `;
    document.head.appendChild(style);

    const btn = document.createElement("button");
    btn.className = "zj-launcher";
    btn.type = "button";
    btn.setAttribute("aria-label", title);
    btn.textContent = "💬";

    const iframe = document.createElement("iframe");
    iframe.className = "zj-frame";
    iframe.title = title;
    iframe.src = url;
    iframe.allow = allow;
    iframe.sandbox = sandbox;

    // Recuperar posición guardada
    const saved = localStorage.getItem("zajunaWidgetPos");
    if (saved) {
        const pos = JSON.parse(saved);
        btn.style.left = pos.left;
        btn.style.top = pos.top;
        btn.style.right = "auto";
        btn.style.bottom = "auto";

        iframe.style.left = pos.left;
        iframe.style.top = (parseFloat(pos.top) - (parseInt(height) || 560) - 20) + "px";
        iframe.style.right = "auto";
        iframe.style.bottom = "auto";
    }

    // Abrir/cerrar el chat
    btn.addEventListener("click", () => {
        if (btn.classList.contains("minimized")) {
            btn.classList.remove("minimized");
            return;
        }
        const open = iframe.classList.toggle("open");
        btn.setAttribute("aria-expanded", open ? "true" : "false");
        if (open) setTimeout(() => iframe.focus?.(), 0);
    });

    // Doble clic = minimizar
    btn.addEventListener("dblclick", () => {
        iframe.classList.remove("open");
        btn.classList.add("minimized");
    });

    document.body.appendChild(btn);
    document.body.appendChild(iframe);

    // ---- Drag & Drop persistente ----
    let offsetX, offsetY, dragging = false;

    const onMouseDown = (e) => {
        dragging = true;
        offsetX = e.clientX - btn.getBoundingClientRect().left;
        offsetY = e.clientY - btn.getBoundingClientRect().top;
        document.body.style.userSelect = "none";
    };

    const onMouseMove = (e) => {
        if (!dragging) return;
        const x = e.clientX - offsetX;
        const y = e.clientY - offsetY;
        btn.style.left = x + "px";
        btn.style.top = y + "px";
        btn.style.right = "auto";
        btn.style.bottom = "auto";
        iframe.style.left = x + "px";
        iframe.style.top = y - (parseInt(height) || 560) - 20 + "px";
        iframe.style.right = "auto";
        iframe.style.bottom = "auto";
    };

    const onMouseUp = () => {
        if (dragging) {
            localStorage.setItem("zajunaWidgetPos", JSON.stringify({
                left: btn.style.left,
                top: btn.style.top
            }));
        }
        dragging = false;
        document.body.style.userSelect = "";
    };

    btn.addEventListener("mousedown", onMouseDown);
    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
})();