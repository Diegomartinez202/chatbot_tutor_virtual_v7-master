// src/pages/HomePage.jsx
import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";

export default function HomePage() {
    const navigate = useNavigate();

    const [phase, setPhase] = useState("idle"); 

    const AVATAR =
        import.meta.env.VITE_BOT_AVATAR ||
        "/bot-avatar.png";

    const goGuest = () => {
       
        setPhase("loading");

       
        setTimeout(() => {
            navigate("/chat"); 
        }, 1200);
    };


    const goZajuna = () => {
        const sso = import.meta.env.VITE_ZAJUNA_SSO_URL;
        if (sso) {
            window.location.href = sso;
        } else {
            navigate("/login");
        }
    };

    if (phase === "loading") {
        return (
            <main className="chat-loading-screen">
                <div className="chat-loading-card">
                    <div className="chat-loading-avatar">
                        
                        <img
                            src="/bot-loading.png"
                            onError={(e) => { e.currentTarget.src = AVATAR; }}
                            alt="Cargando tutor virtual"
                        />
                    </div>

                    <p className="chat-loading-text">
                        Preparando tu tutor virtual...
                    </p>

                    <div className="chat-loading-bar">
                        <div className="chat-loading-bar-inner" />
                    </div>

                    <p className="chat-loading-subtext">
                        Conectando a la sesión como invitado
                    </p>
                </div>
            </main>
        );
    }
    return (
        <main className="min-h-screen flex items-center justify-center bg-gray-50 p-6">
            <div className="max-w-3xl w-full bg-white rounded-2xl shadow-lg p-8 text-center">
                <img
                    src={AVATAR}
                    onError={(e) => { e.currentTarget.src = "/bot-avatar.png"; }}
                    alt="Avatar del Chatbot"
                    className="home-avatar mb-6 shadow-lg"
                    loading="eager"
                />

                <h1 className="
                      text-2xl sm:text-3xl md:text-4xl
                      font-bold
                      text-gray-100
                      mb-4
                      leading-tight
                      max-w-md mx-auto
                    "
                >
                    ¡Bienvenido al <span className="text-indigo-600">Chatbot Tutor Virtual</span>!
                </h1>

                <p className="text-gray-600 mb-8">Elige cómo deseas entrar:</p>

                <div className="mt-6 flex justify-center">
                  <div className="w-[210px] sm:w-[230px] md:w-[260px] space-y-3">
                    <button
                        type="button"
                        onClick={goGuest}
                        className="
                          w-full
                          inline-flex items-center justify-center
                          rounded-full
                          bg-indigo-600 text-white
                          px-6 py-3 text-sm font-medium
                          shadow-md
                          hover:bg-indigo-700 hover:shadow-lg
                          focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:ring-offset-2
                          transition
                        "
                    >
                        Ingresar como invitado
                    </button>

                    <button
                        type="button"
                        onClick={goZajuna}
                        className="
                          w-full
                          inline-flex items-center justify-center
                          rounded-full
                          bg-white text-gray-900
                          px-6 py-3 text-sm font-medium
                          border border-indigo-500
                          shadow-sm
                          hover:bg-indigo-50 hover:border-indigo-600
                          focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:ring-offset-2
                          transition
                        "
                    >
                         Entrar con autenticación
                        </button>
                   </div>
                </div>

                <div className="mt-6 text-xs text-gray-500">
                    <Link to="/dashboard" className="hover:underline">
                        Ir al panel (requiere login)
                    </Link>
                </div>

                <p className="text-[11px] text-gray-400 mt-3">
                </p>
            </div>
        </main>
    );
}
