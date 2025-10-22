// public/zajuna-widget.js
(() => {
    const s = document.currentScript?.dataset || {};
    const origin = (s.origin || window.location.origin).replace(/\/$/, "");
    const pathEmbed = s.pathEmbed || "/chat-embed.html";
    const chatSrc = s.chatSrc || "/chat?embed=1";
    const width = s.width || "380px";
    const height = s.height || "560px";
    const position = s.position === "left" ? "left" : "right";
    const title = s.title || "Chatbot Tutor Virtual";
    const allow = s.allow || "clipboard-write";
    const sandbox = s.sandbox || "allow-scripts allow-forms allow-same-origin allow-popups";
    const z = Number.isFinite(Number(s.zIndex)) ? Number(s.zIndex) : 9999;

    const defaultAvatar = new URL("bot-avatar.png", document.baseURI).pathname;
    const avatarSrc = s.avatar || defaultAvatar;

    const url = `${origin}${pathEmbed}?src=${encodeURIComponent(chatSrc)}&w=${encodeURIComponent(width)}&h=${encodeURIComponent(height)}&title=${encodeURIComponent(title)}&avatar=${encodeURIComponent(avatarSrc)}`;

    // 💅 Estilos del widget
    const style = document.createElement("style");
    style.textContent = `
    .zj-launcher {
      position: fixed; ${position}: 20px; bottom: 20px;
      width: 64px; height: 64px;
      border-radius: 50%; border: none;
      background: transparent; cursor: pointer;
      z-index: ${z + 1};
      transition: transform 0.25s ease, box-shadow 0.25s ease;
    }
    .zj-launcher img {
      width: 100%; height: 100%;
      border-radius: 50%;
      object-fit: cover;
      box-shadow: 0 8px 18px rgba(0,0,0,.25);
      transition: transform 0.25s ease;
    }
    .zj-launcher:hover img {
      transform: scale(1.08);
    }
    .zj-frame {
      position: fixed; ${position}: 20px; bottom: 90px;
      width: ${width}; height: ${height};
      border: none; border-radius: 16px;
      box-shadow: 0 20px 40px rgba(0,0,0,.25);
      display: none; opacity: 0;
      transition: opacity 0.25s ease, transform 0.25s ease;
      transform: translateY(20px);
      z-index: ${z};
      background: #fff;
    }
    .zj-frame.open {
      display: block; opacity: 1; transform: translateY(0);
    }
    @media (max-width: 480px) {
      .zj-frame { width: 94vw; height: 70vh; ${position}: 3vw; }
    }
  `;
    document.head.appendChild(style);

    // 🧠 Crear botón con avatar
    const btn = document.createElement("button");
    btn.className = "zj-launcher";
    btn.type = "button";
    btn.setAttribute("aria-label", title);

    const img = document.createElement("img");
    img.src = avatarSrc;
    img.alt = "Abrir Chatbot";
    btn.appendChild(img);

    // 💬 Crear iframe del chat
    const iframe = document.createElement("iframe");
    iframe.className = "zj-frame";
    iframe.title = title;
    iframe.src = url;
    iframe.allow = allow;
    iframe.sandbox = sandbox;

    // 🎯 Alternar apertura/cierre
    btn.addEventListener("click", () => {
        const open = iframe.classList.toggle("open");
        btn.setAttribute("aria-expanded", open ? "true" : "false");
        if (open) setTimeout(() => iframe.focus?.(), 150);
    });

    document.body.appendChild(btn);
    document.body.appendChild(iframe);

    // 🖱️ Arrastrar libremente (desktop y mobile)
    let isDragging = false;
    let offsetX, offsetY;

    const startDrag = (x, y) => {
        isDragging = true;
        const rect = iframe.getBoundingClientRect();
        offsetX = x - rect.left;
        offsetY = y - rect.top;
        iframe.style.transition = "none";
        document.body.style.userSelect = "none";
    };

    const moveDrag = (x, y) => {
        if (!isDragging) return;
        iframe.style.left = `${x - offsetX}px`;
        iframe.style.top = `${y - offsetY}px`;
        iframe.style.right = "auto";
        iframe.style.bottom = "auto";
    };

    const stopDrag = () => {
        if (!isDragging) return;
        isDragging = false;
        iframe.style.transition = "opacity 0.25s ease, transform 0.25s ease";
        document.body.style.userSelect = "";
    };

    iframe.addEventListener("mousedown", (e) => startDrag(e.clientX, e.clientY));
    window.addEventListener("mousemove", (e) => moveDrag(e.clientX, e.clientY));
    window.addEventListener("mouseup", stopDrag);

    iframe.addEventListener("touchstart", (e) => {
        const t = e.touches[0];
        startDrag(t.clientX, t.clientY);
    });
    window.addEventListener("touchmove", (e) => {
        const t = e.touches[0];
        moveDrag(t.clientX, t.clientY);
    });
    window.addEventListener("touchend", stopDrag);
})();