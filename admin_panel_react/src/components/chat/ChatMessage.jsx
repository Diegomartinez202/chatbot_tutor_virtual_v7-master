// components/chat/ChatMessage.jsx (parte de render del mensaje del bot)
import LinkCard from "./LinkCard";
import MessageText from "./MessageText";

export default function ChatMessage({ msg }) {
    const text = msg.text || "";
    const cards = msg.cards || msg.custom?.cards || [];

    return (
        <div className="space-y-2">
            {text && <MessageText text={text} embed={true} />}
            {Array.isArray(cards) && cards.length > 0 && (
                <div className="grid grid-cols-1 gap-2">
                    {cards.map((c, i) => <LinkCard key={i} url={c.url} />)}
                </div>
            )}
        </div>
    );
}
