import VoiceList from "@/components/voice/VoiceList";

export default function VoicePage() {
    return (
        <div className="p-4">
            <h1 className="text-lg font-semibold mb-3">Audios (Voice)</h1>
            <p className="text-sm text-slate-600 mb-4">
                Listado de audios guardados (GridFS). Haz clic en reproducir o descarga.
            </p>
            <VoiceList defaultSender="web-demo" />
        </div>
    );
}
