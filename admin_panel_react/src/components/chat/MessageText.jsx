import { extractLinks } from "@/utils/links";
import { trackLink } from "@/utils/telemetry"; // 👈 AQUI
import React from "react";

export default function MessageText({ text, embed }) {
    const links = extractLinks(text);
    if (!links.length) return <p className="whitespace-pre-wrap">{text}</p>;

    let html = text;
    links.forEach((m) => {
        const safe = m.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); // escapar para regex
        html = html.replace(
            new RegExp(safe, "g"),
            `<a href="${m}" target="_blank" rel="noopener noreferrer" data-track="${m}" class="text-indigo-600 underline">${m}</a>`
        );
    });

    // Interceptamos clicks para enviar telemetría sin romper la navegación
    const onClick = (e) => {
        const a = e.target.closest("a[data-track]");
        if (a) trackLink(a.getAttribute("data-track"), { where: "MessageText" });
    };

    return (
        <p
            className="whitespace-pre-wrap break-words"
            onClick={onClick}
            dangerouslySetInnerHTML={{ __html: html }}
        />
    );
}
