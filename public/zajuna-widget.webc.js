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
        const z = Number(this.getAttribute("z-index")) || 9999;

        const defaultAvatar = new URL("bot-avatar.png", document.baseURI).pathname;
        const url = `${origin}${pathEmbed}?src=${encodeURIComponent(chatSrc)}&w=${encodeURIComponent(width)}&h=${encodeURIComponent(height)}&title=${encodeURIComponent(title)}&avatar=${encodeURIComponent(this.getAttribute("avatar") || defaultAvatar)}`;

        const style = document.createElement("style");
        style.textContent = `
      :host {
        position:fixed; ${position}:20px; bottom:20px; z-index:${z};
        user-select:none;
      }
      .wrap { position:relative; }
      .launcher {
        position:absolute; ${position}:0; bottom:0;
        width:56px; height:56px; border-radius:50%;
        border:0; background:#2563eb; color:#fff; font-weight:600;
        display:flex; align-items:center; justify-content:center;
        cursor:pointer; font-size:22px;
        box-shadow:0 10px 20px rgba(0,0,0,.25);
        transition:all .3s ease;
      }
      .launcher.minimized {
        width:42px; height:42px; font-size:18px;
        background:#1d4ed8; opacity:.9;
      }
      .frame {
        position:absolute; ${position}:0; bottom:70px;
        width:${width}; height:${height};
        border:0; border-radius:16px;
        background:#fff; box-shadow:0 20px 40px rgba(0,0,0,.25);
        display:none; overflow:hidden;
      }
      .frame.open { display:block; }
      @media (max-width:480px){
        .frame { width:94vw; height:70vh; ${position}:0; }
      }
    `;

        const wrap = document.createElement("div");
        wrap.className = "wrap";

        const btn = document.createElement("button");
        btn.className = "launcher";
        btn.type = "button";
        btn.setAttribute("aria-label", title);
        btn.textContent = "💬";

        const iframe = document.createElement("iframe");
        iframe.className = "frame";
        iframe.title = title;
        iframe.src = url;
        iframe.allow = allow;
        iframe.sandbox = sandbox;

        // Restaurar posición previa
        const saved = localStorage.getItem("chatbotTutorSenaPos");
        if (saved) {
            const pos = JSON.parse(saved);
            this.style.left = pos.left;
            this.style.top = pos.top;
            this.style.right = "auto";
            this.style.bottom = "auto";
        }

        // Toggle abrir/cerrar
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

        wrap.appendChild(btn);
        wrap.appendChild(iframe);
        root.appendChild(style);
        root.appendChild(wrap);

        // Drag & drop persistente
        let offsetX, offsetY, dragging = false;

        const onMouseDown = (e) => {
            dragging = true;
            offsetX = e.clientX - this.getBoundingClientRect().left;
            offsetY = e.clientY - this.getBoundingClientRect().top;
            document.body.style.userSelect = "none";
        };

        const onMouseMove = (e) => {
            if (!dragging) return;
            const x = e.clientX - offsetX;
            const y = e.clientY - offsetY;
            this.style.left = x + "px";
            this.style.top = y + "px";
            this.style.right = "auto";
            this.style.bottom = "auto";
        };

        const onMouseUp = () => {
            if (dragging) {
                localStorage.setItem("chatbotTutorSenaPos", JSON.stringify({
                    left: this.style.left,
                    top: this.style.top
                }));
            }
            dragging = false;
            document.body.style.userSelect = "";
        };

        btn.addEventListener("mousedown", onMouseDown);
        document.addEventListener("mousemove", onMouseMove);
        document.addEventListener("mouseup", onMouseUp);
    }
}

customElements.define("chatbot-tutor-sena", ChatbotTutorSena);