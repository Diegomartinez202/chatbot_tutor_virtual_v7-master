// components/chat/MessageText.jsx
import { extractLinks } from "@/utils/links";

export default function MessageText({ text, embed }) {
    const links = extractLinks(text);
    if (!links.length) return <p className="whitespace-pre-wrap">{text}</p>;

    // Reemplaza links por <a target="_blank">
    const parts = [];
    let lastIndex = 0;
    text.replace(urlRegex, (m, idx) => {
        if (idx > lastIndex) parts.push(text.slice(lastIndex, idx));
        parts.push(
            <a
                key={idx}
                href={m}
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => trackLink(m)}
                className="text-indigo-600 underline"
            >
                {m}
            </a>
        );
        lastIndex = idx + m.length;
        return m;
    });
    if (lastIndex < text.length) parts.push(text.slice(lastIndex));

    return <p className="whitespace-pre-wrap break-words">{parts}</p>;
}
