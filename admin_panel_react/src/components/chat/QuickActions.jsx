// src/components/chat/QuickActions.jsx
import React, { useMemo, useState } from "react";

/**
 * Panel de acciones rápidas del chatbot (equivalente al viejo widget.html),
 * convertido a React y conectado al pipeline del chat.
 *
 * Props:
 * - onAction: (payload: string, displayTitle?: string) => void
 * - show: boolean (muestra/oculta el panel)
 */
export default function QuickActions({ onAction, show = true }) {
    const [active, setActive] = useState("main"); // main | temas | zajuna | cursos | academico | soporte | info
    const [form, setForm] = useState({ nombre: "", email: "", mensaje: "" });

    const visible = !!show;

    const go = (menu) => setActive(menu);
    const back = () => setActive("main");

    const canSend = useMemo(() => {
        return form.nombre.trim() && form.email.trim() && form.mensaje.trim();
    }, [form]);

    const enviarSoporte = () => {
        if (!canSend) return;
        const payload = `/enviar_soporte{"nombre":"${escapeQuotes(
            form.nombre
        )}","email":"${escapeQuotes(form.email)}","mensaje":"${escapeQuotes(
            form.mensaje
        )}"}`;

        onAction?.(payload, "Enviar solicitud de soporte");
        setForm({ nombre: "", email: "", mensaje: "" });
        setActive("main");
    };

    if (!visible) return null;

    return (
        <div className="mb-3">
            {/* Carrusel fijo como en el HTML original */}
            <div className="bg-gray-50 border rounded-xl p-3 mb-3">
                <h4 className="text-sm font-semibold mb-2">Cursos recomendados 🎓</h4>
                <div className="flex gap-3 overflow-x-auto pb-2">
                    {[
                        { title: "Excel Básico", meta: "🕒 20h • Virtual" },
                        { title: "Soldadura MIG", meta: "🛠️ 40h • Presencial" },
                        { title: "Programación Web", meta: "💻 60h • Virtual" },
                    ].map((c) => (
                        <div
                            key={c.title}
                            className="min-w-[160px] bg-white border rounded-lg p-2 shadow-sm"
                        >
                            <div className="w-full h-24 bg-gray-100 rounded mb-2 grid place-items-center text-xs text-gray-500">
                                Imagen
                            </div>
                            <div className="text-sm font-semibold">{c.title}</div>
                            <div className="text-xs text-gray-500">{c.meta}</div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Menú principal / submenús */}
            {active === "main" && (
                <div className="flex flex-wrap justify-center gap-2">
                    <Btn onClick={() => go("temas")}>📚 Temas de aprendizaje</Btn>
                    <Btn onClick={() => go("zajuna")}>🔐 Ingreso Zajuna</Btn>
                    <Btn onClick={() => go("cursos")}>🎓 Mis cursos</Btn>
                    <Btn onClick={() => go("academico")}>🏫 Proceso académico</Btn>
                    <Btn onClick={() => go("soporte")}>🛠️ Soporte técnico</Btn>
                    <Btn onClick={() => go("info")}>🤖 ¿Qué es este chatbot?</Btn>
                </div>
            )}

            {active === "temas" && (
                <Submenu title="Temas de aprendizaje" onBack={back}>
                    <Btn onClick={() => onAction?.("Inteligencia Artificial", "🧠 Inteligencia Artificial")}>
                        🧠 Inteligencia Artificial
                    </Btn>
                    <Btn onClick={() => onAction?.("Programación Web", "💻 Programación Web")}>
                        💻 Programación Web
                    </Btn>
                </Submenu>
            )}

            {active === "zajuna" && (
                <Submenu title="Ingreso Zajuna" onBack={back}>
                    <Btn
                        onClick={() => onAction?.("/recuperar_password", "🔑 Recuperar contraseña")}
                    >
                        🔑 Recuperar contraseña
                    </Btn>
                    <Btn
                        onClick={() => onAction?.("/link_ingreso", "🔗 Enlace de ingreso")}
                    >
                        🔗 Enlace de ingreso
                    </Btn>
                </Submenu>
            )}

            {active === "cursos" && (
                <Submenu title="Mis cursos" onBack={back}>
                    <Btn onClick={() => onAction?.("/ver_cursos", "📋 Ver cursos activos")}>
                        📋 Ver cursos activos
                    </Btn>
                    <Btn onClick={() => onAction?.("/ver_progreso", "📈 Progreso")}>📈 Progreso</Btn>
                </Submenu>
            )}

            {active === "academico" && (
                <Submenu title="Proceso académico" onBack={back}>
                    <Btn onClick={() => onAction?.("/certificados", "📜 Certificados")}>
                        📜 Certificados
                    </Btn>
                    <Btn onClick={() => onAction?.("/inscripcion", "📝 Inscripción")}>
                        📝 Inscripción
                    </Btn>
                    <Btn onClick={() => onAction?.("/horarios", "⏰ Horarios")}>⏰ Horarios</Btn>
                    <Btn onClick={() => onAction?.("/tutor_asignado", "👨‍🏫 Tutor asignado")}>
                        👨‍🏫 Tutor asignado
                    </Btn>
                </Submenu>
            )}

            {active === "soporte" && (
                <Submenu title="Soporte técnico" onBack={back}>
                    <Btn onClick={() => onAction?.("/faq", "❓ Preguntas frecuentes")}>
                        ❓ Preguntas frecuentes
                    </Btn>

                    {/* Formulario rápido de soporte */}
                    <div className="bg-white border rounded-lg p-3 mt-2">
                        <h5 className="font-medium text-sm mb-2">📨 Formulario de soporte</h5>
                        <input
                            className="w-full border rounded px-2 py-1 text-sm mb-2"
                            placeholder="Tu nombre completo"
                            value={form.nombre}
                            onChange={(e) => setForm((f) => ({ ...f, nombre: e.target.value }))}
                        />
                        <input
                            className="w-full border rounded px-2 py-1 text-sm mb-2"
                            placeholder="Correo de contacto"
                            value={form.email}
                            onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                        />
                        <textarea
                            className="w-full border rounded px-2 py-1 text-sm mb-2"
                            placeholder="¿En qué necesitas ayuda?"
                            rows={3}
                            value={form.mensaje}
                            onChange={(e) => setForm((f) => ({ ...f, mensaje: e.target.value }))}
                        />
                        <button
                            type="button"
                            onClick={enviarSoporte}
                            disabled={!canSend}
                            className="inline-flex items-center justify-center rounded bg-green-600 text-white px-3 py-2 text-sm disabled:opacity-60"
                        >
                            Enviar
                        </button>
                    </div>
                </Submenu>
            )}

            {active === "info" && (
                <Submenu title="¿Qué es este chatbot?" onBack={back}>
                    <Btn onClick={() => onAction?.("/info_general", "ℹ️ Información general")}>
                        ℹ️ Información general
                    </Btn>
                    <Btn onClick={() => onAction?.("/como_usar", "💡 Cómo usar el chatbot")}>
                        💡 Cómo usar el chatbot
                    </Btn>
                </Submenu>
            )}
        </div>
    );
}

function Btn({ children, onClick }) {
    return (
        <button
            type="button"
            onClick={onClick}
            className="px-3 py-2 rounded bg-indigo-600 text-white text-sm hover:bg-indigo-700"
        >
            {children}
        </button>
    );
}

function Submenu({ title, onBack, children }) {
    return (
        <div className="flex flex-col items-center gap-2">
            <div className="text-sm font-semibold">{title}</div>
            <div className="flex flex-wrap justify-center gap-2">{children}</div>
            <button
                type="button"
                onClick={onBack}
                className="mt-1 px-3 py-1.5 rounded bg-gray-200 text-gray-900 text-xs hover:bg-gray-300"
            >
                ⬅️ Volver
            </button>
        </div>
    );
}

function escapeQuotes(s) {
    return String(s || "").replace(/"/g, '\\"');
}