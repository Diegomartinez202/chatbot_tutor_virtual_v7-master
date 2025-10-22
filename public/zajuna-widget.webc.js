// ===============================================================
// 🌐 Widget Profesional del Chatbot Tutor SENA con Drag & Drop
// ===============================================================

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
      :host {
        position: fixed;
        ${position}: 20px;
        bottom: 20px;
        z-index: 9999;
        cursor: grab;
      }

      .wrap {
        position: relative;
        user-select: none;
      }

      .launcher {
        position: absolute;
        ${position}: 0;
        bottom: 0;
        width: 56px;
        height: 56px;
        border-radius: 999px;
        border: 0;
        background: #2563eb;
        color: #fff;
        font-weight: 600;
        cursor: pointer;
        box-shadow: 0 10px 20px rgba(0, 0, 0, .25);
        transition: transform 0.2s ease;
      }

      .launcher:hover {
        transform: scale(1.05);
      }

      .frame {
        position: absolute;
        ${position}: 0;
        bottom: 70px;
        width: ${width};
        height: ${height};
        border: 0;
        border-radius: 16px;
        display: none;
        background: #fff;
        box-shadow: 0 20px 40px rgba(0, 0, 0, .25);
      }

      .frame.open {
        display: block;
      }

      @media (max-width: 480px) {
        .frame {
          width: 94vw;
          height: 70vh;
          ${position}: 0;
        }
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

    // 👉 Abrir/Cerrar chat
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const open = iframe.classList.toggle("open");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
      if (open) setTimeout(() => iframe.focus?.(), 0);
    });

    wrap.appendChild(btn);
    wrap.appendChild(iframe);
    root.appendChild(style);
    root.appendChild(wrap);

    // =====================================================
    // 🚀 Drag & Drop (Arrastrar libremente por la pantalla)
    // =====================================================
    let isDragging = false;
    let startX, startY, startLeft, startBottom;

    const onMouseDown = (e) => {
      if (iframe.classList.contains("open")) return; // no mover si está abierto
      isDragging = true;
      root.host.style.cursor = "grabbing";
      startX = e.clientX;
      startY = e.clientY;
      const rect = root.host.getBoundingClientRect();
      startLeft = rect.left;
      startBottom = window.innerHeight - rect.bottom;
      e.preventDefault();
    };

    const onMouseMove = (e) => {
      if (!isDragging) return;
      const dx = e.clientX - startX;
      const dy = e.clientY - startY;
      const newLeft = startLeft + dx;
      const newBottom = startBottom - dy;

      // Limitar movimiento dentro de la pantalla
      const maxLeft = window.innerWidth - 80;
      const maxBottom = window.innerHeight - 80;
      root.host.style.left = `${Math.min(Math.max(newLeft, 0), maxLeft)}px`;
      root.host.style.bottom = `${Math.min(Math.max(newBottom, 0), maxBottom)}px`;
      root.host.style.right = "auto"; // para evitar conflicto con position right
    };

    const onMouseUp = () => {
      isDragging = false;
      root.host.style.cursor = "grab";
    };

    wrap.addEventListener("mousedown", onMouseDown);
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
  }
}

customElements.define("chatbot-tutor-sena", ChatbotTutorSena);