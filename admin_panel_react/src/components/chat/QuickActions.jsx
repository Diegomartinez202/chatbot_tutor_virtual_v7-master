// QuickActions.jsx

import React, { useEffect, useState } from "react";

export default function QuickActions() {
    const [text, setText] = useState("");
    const [visible, setVisible] = useState(true);
    const fullText = "📘 Este es un mecanismo de comunicación educativo. Bienvenido aprendiz 👋";

    // Generamos un pequeño "ding" con el Web Audio API
    const playDing = () => {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioCtx.createOscillator();
        const gainNode = audioCtx.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(audioCtx.destination);
        oscillator.type = "sine";
        oscillator.frequency.setValueAtTime(880, audioCtx.currentTime); // tono A5
        gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime); // volumen suave
        oscillator.start();
        oscillator.stop(audioCtx.currentTime + 0.25); // duración 250ms
    };

    useEffect(() => {
        let index = 0;
        let typingInterval;
        let fadeTimeout;
        let repeatInterval;

        const startTyping = () => {
            setText("");
            setVisible(true);
            index = 0;
            typingInterval = setInterval(() => {
                setText(fullText.slice(0, index));
                index++;
                if (index > fullText.length) {
                    clearInterval(typingInterval);
                    playDing(); // 🔔 sonido al terminar
                    // Mantiene visible 2s y luego desvanece
                    fadeTimeout = setTimeout(() => setVisible(false), 2000);
                }
            }, 50);
        };

        startTyping(); // Inicia animación
        repeatInterval = setInterval(() => {
            startTyping();
        }, 10000);

        return () => {
            clearInterval(typingInterval);
            clearInterval(repeatInterval);
            clearTimeout(fadeTimeout);
        };
    }, []);

    return (
        <div
            className={`transition-opacity duration-1000 ease-in-out ${visible ? "opacity-100" : "opacity-0"
                } p-4 text-center text-gray-700 bg-gray-100 rounded-xl shadow-sm max-w-xl mx-auto mt-6 border border-gray-200`}
        >
            <p className="font-medium text-lg whitespace-pre-wrap">
                {text}
                <span className="animate-pulse">|</span>
            </p>
        </div>
    );
}
