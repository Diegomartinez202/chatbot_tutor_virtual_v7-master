// src/pages/HomePage.jsx
import React from "react";
import { useNavigate, Link } from "react-router-dom";

export default function HomePage() {
    const navigate = useNavigate();

    const AVATAR =
        import.meta.env.VITE_BOT_AVATAR ||
        "/bot-avatar.png";

    const goGuest = () => {
        navigate("/chat");
    };

    const goZajuna = () => {
        const sso = import.meta.env.VITE_ZAJUNA_SSO_URL;
        if (sso) {
            window.location.href = sso;
        } else {
            navigate("/login");
        }
    };

    return (
        <main className="min-h-screen flex items-center justify-center bg-gray-50 p-6">
            <div className="max-w-3xl w-full bg-white rounded-2xl shadow-lg p-8 text-center">
                <img
                    src={AVATAR}
                    onError={(e) => { e.currentTarget.src = "/bot-avatar.png"; }}
                    alt="Avatar del Chatbot"
                    className="
                      mx-auto mb-6 rounded-full shadow-lg object-cover
                      w-20 h-20
                      sm:w-24 sm:h-24
                      md:w-28 md:h-28
                      lg:w-32 lg:h-32
                    "
                    loading="eager"
                />

                <h1 className="text-3xl font-bold text-gray-900 mb-4">
                    ¡Bienvenido al <span className="text-indigo-600">Chatbot Tutor Virtual</span>!
                </h1>

                <p className="text-gray-600 mb-8">Elige cómo deseas entrar:</p>

                <div className="flex flex-col sm:flex-row gap-4 justify-center">
                    <button
                        type="button"
                        onClick={goGuest}
                        className="inline-flex items-center justify-center rounded-lg bg-indigo-600 text-white px-5 py-3 text-sm font-medium hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-400"
                    >
                        Entrar sin login
                    </button>

                    <button
                        type="button"
                        onClick={goZajuna}
                        className="inline-flex items-center justify-center rounded-lg bg-white text-gray-900 px-5 py-3 text-sm font-medium border hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-400"
                    >
                        Entrar con autenticación
                    </button>
                </div>

                <div className="mt-6 text-xs text-gray-500">
                    <Link to="/dashboard" className="hover:underline">
                        Ir al panel (requiere login)
                    </Link>
                </div>

                <p className="text-[11px] text-gray-400 mt-3">
                    Consejo: si tienes SSO Zajuna, define <code>VITE_ZAJUNA_SSO_URL</code> en tu <code>.env</code>.
                </p>
            </div>
        </main>
    );
}
