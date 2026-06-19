import React, { useEffect } from "react";
import ChatUI from "@/components/chat/ChatUI";

/**
 * Harness.jsx (página QA)
 * Ruta recomendada: /chat
 * - Pensado para pruebas de Zajuna (cursos, administración académica, navegación, FAQs).
 * - Permite cambiar persona/lang por query (?persona=aprendiz|instructor|administrativo&lang=es|en).
 */

function useDocTitle(title) {
    useEffect(() => {
        const prev = document.title;
        document.title = title;
        return () => { document.title = prev; };
    }, [title]);
}

function getParam(name, fallback = "") {
    const qs = new URLSearchParams(window.location.search);
    return qs.get(name) || fallback;
}

export default function Harness() {
    useDocTitle("Chatbot Tutor Virtual — Harness");

    const persona = getParam("persona", "aprendiz"); // aprendiz | instructor | administrativo
    const lang = getParam("lang", "es");             // es | en

    return (
        <div className="min-h-screen bg-white flex flex-col">
            {/* Barra de control mínima */}
            <div className="border-b bg-gray-50">
                <div className="max-w-5xl mx-auto px-3 py-2 flex items-center gap-3">
                    <span className="text-sm font-semibold">Harness Zajuna</span>

                    <label className="text-xs text-gray-600">
                        Persona:&nbsp;
                        <select
                            defaultValue={persona}
                            onChange={(e) => {
                                const qs = new URLSearchParams(location.search);
                                qs.set("persona", e.target.value);
                                history.replaceState({}, "", `${location.pathname}?${qs}`);
                                location.reload(); // simple: recarga para refrescar props
                            }}
                            className="border rounded px-2 py-1 text-xs"
                            data-testid="harness-persona"
                        >
                            <option value="aprendiz">aprendiz</option>
                            <option value="instructor">instructor</option>
                            <option value="administrativo">administrativo</option>
                        </select>
                    </label>

                    <label className="text-xs text-gray-600">
                        Idioma:&nbsp;
                        <select
                            defaultValue={lang}
                            onChange={(e) => {
                                const qs = new URLSearchParams(location.search);
                                qs.set("lang", e.target.value);
                                history.replaceState({}, "", `${location.pathname}?${qs}`);
                                location.reload();
                            }}
                            className="border rounded px-2 py-1 text-xs"
                            data-testid="harness-lang"
                        >
                            <option value="es">es</option>
                            <option value="en">en</option>
                        </select>
                    </label>

                    <div className="ml-auto text-[11px] text-gray-500">
                        Zajuna: cursos, matrícula, notas, navegación, FAQs.
                    </div>
                </div>
            </div>

            {/* Contenedor del chat */}
            <div className="flex-1">
                <div className="max-w-5xl mx-auto h-[calc(100vh-46px)] p-3">
                    <div
                        className="h-full border rounded-xl overflow-hidden"
                        data-testid="chat-root"        /* ← test anchor para Playwright */
                    >
                        <ChatUI
                            embed={false}
                            placeholder={
                                persona === "instructor"
                                    ? "Escribe tu duda (plan de curso, rúbricas, calificaciones, etc.)…"
                                    : persona === "administrativo"
                                        ? "Escribe tu consulta (matrículas, certificados, pagos, etc.)…"
                                        : "Escribe tu pregunta (clases, tareas, navegación en Zajuna, etc.)…"
                            }
                        />
                    </div>
                </div>
            </div>
        </div>
    );
}