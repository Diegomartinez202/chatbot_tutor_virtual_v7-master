// public/zajuna-widget.webc.js
class ChatbotTutorSena extends HTMLElement {
    constructor() {
        super();
        const root = this.attachShadow({ mode: "open" });

        const origin = (this.getAttribute("origin") || window.location.origin).replace(/\/$/, "");
        const pathEmbed = this.getAttribute("path-embed") || "/chat-embed.html";
        const chatSrc = this.getAttribute("chat-src") || "/chat?embed=1";
        const width = this.getAttribute("width") || "380px";
        const height = this.getAttribute("height") || "560px";
        const title = this.getAttribute("title") || "Chatbot Tutor Virtual";
        const allow = this.getAttribute("allow") || "clipboard-write";
        const sandbox = this.getAttribute("sandbox") || "allow-scripts allow-forms allow-same-origin allow-popups";
        const position = this.getAttribute("position") === "left" ? "left" : "right";

        const defaultAvatar = new URL("bot-avatar.png", document.baseURI).pathname;
        const url = `${origin}${pathEmbed}?src=${encodeURIComponent(chatSrc)}&w=${encodeURIComponent(width)}&h=${encodeURIComponent(height)}&title=${encodeURIComponent(title)}&avatar=${encodeURIComponent(this.getAttribute("avatar") || defaultAvatar)}`;

        const style = document.createElement("style");
        style.textContent = `
      :host { position:fixed; ${position}:20px; bottom:20px; z-index:9999; }
      .wrap { position:relative; }
      .launcher {
        position:absolute; ${position}:0; bottom:0; width:56px; height:56px;
        border-radius:999px; border:0; background:#2563eb; color:#fff; font-weight:600; cursor:pointer;
        box-shadow:0 10px 20px rgba(0,0,0,.25);
      }
      .frame {
        position:absolute; ${position}:0; bottom:70px; width:${width}; height:${height};
        border:0; border-radius:16px; display:none; background:#fff; box-shadow:0 20px 40px rgba(0,0,0,.25);
      }
      .frame.open { display:block; }
      @media (max-width: 480px){
        .frame { width:94vw; height:70vh; ${position}:0; }
      }
    `;

        const wrap = document.createElement("div");
        wrap.className = "wrap";

        const btn = document.createElement("button");
        btn.className = "launcher";
        btn.type = "button";
        btn.setAttribute("aria-label", title);
        btn.textContent = "Chat";

        const iframe = document.createElement("iframe");
        iframe.className = "frame";
        iframe.title = title;
        iframe.src = url;
        iframe.allow = allow;
        iframe.sandbox = sandbox;

        btn.addEventListener("click", () => {
            const open = iframe.classList.toggle("open");
            btn.setAttribute("aria-expanded", open ? "true" : "false");
            if (open) setTimeout(() => iframe.focus?.(), 0);
        });

        wrap.appendChild(btn);
        wrap.appendChild(iframe);
        root.appendChild(style);
        root.appendChild(wrap);
    }
}
customElements.define("chatbot-tutor-sena", ChatbotTutorSena);