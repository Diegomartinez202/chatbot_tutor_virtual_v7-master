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
    const url = `${origin}${pathEmbed}?src=${encodeURIComponent(chatSrc)}&w=${encodeURIComponent(width)}&h=${encodeURIComponent(height)}&title=${encodeURIComponent(title)}&avatar=${encodeURIComponent(s.avatar || defaultAvatar)}`;

    const style = document.createElement("style");
    style.textContent = `
    .zj-launcher {
      position:fixed; ${position}:20px; bottom:20px; width:56px; height:56px;
      border-radius:999px; border:0; cursor:pointer; background:#2563eb; color:#fff;
      box-shadow:0 10px 20px rgba(0,0,0,.25); font-weight:600; z-index:${z + 1};
    }
    .zj-frame {
      position:fixed; ${position}:20px; bottom:90px; width:${width}; height:${height};
      border:0; border-radius:16px; box-shadow:0 20px 40px rgba(0,0,0,.25);
      display:none; z-index:${z};
    }
    .zj-frame.open { display:block; }
    @media (max-width: 480px){
      .zj-frame { width:94vw; height:70vh; ${position}:3vw; }
    }
  `;
    document.head.appendChild(style);

    const btn = document.createElement("button");
    btn.className = "zj-launcher";
    btn.type = "button";
    btn.setAttribute("aria-label", title);
    btn.textContent = "Chat";

    const iframe = document.createElement("iframe");
    iframe.className = "zj-frame";
    iframe.title = title;
    iframe.src = url;
    iframe.allow = allow;
    iframe.sandbox = sandbox;

    btn.addEventListener("click", () => {
        const open = iframe.classList.toggle("open");
        btn.setAttribute("aria-expanded", open ? "true" : "false");
        if (open) setTimeout(() => iframe.focus?.(), 0);
    });

    document.body.appendChild(btn);
    document.body.appendChild(iframe);
})();