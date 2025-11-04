// src/components/chat/QuickActions.jsx
import React, { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

export default function QuickActions({ onAction, show = true }) {
    const { t } = useTranslation("chat", { useSuspense: false });
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

        onAction?.(payload, t("support.send_request", "Enviar solicitud de soporte"));
        setForm({ nombre: "", email: "", mensaje: "" });
        setActive("main");
    };

    if (!visible) return null;

    return (
        <div className="mb-3" aria-label={t("quick_actions.title", "Acciones rápidas")}>
                <div className="flex flex-wrap justify-center gap-2">
                    <Btn onClick={() => go("temas")}>📚 {t("inicio.options.explorar", "Temas de aprendizaje")}</Btn>
                    <Btn onClick={() => go("zajuna")}>🔐 {t("inicio.options.ingreso", "Ingreso Zajuna")}</Btn>
                    <Btn onClick={() => go("cursos")}>🎓 {t("inicio.options.cursos", "Mis cursos")}</Btn>
                    <Btn onClick={() => go("academico")}>🏫 {t("inicio.options.academico", "Proceso académico")}</Btn>
                    <Btn onClick={() => go("soporte")}>🛠️ {t("inicio.options.soporte", "Soporte técnico")}</Btn>
                    <Btn onClick={() => go("info")}>🤖 {t("quick_actions.what_is_chatbot", "¿Qué es este chatbot?")}</Btn>
                </div>
            )

            {active === "temas" && (
                <Submenu title={t("sections.topicsFeatured", "Temas de aprendizaje")} onBack={back}>
                    {/* Nota: usamos payloads de tu router local para UX instantánea */}
                    <Btn onClick={() => onAction?.("/tema_ia_educativa", "🧠 " + t("topics.aiEducation", "Inteligencia Artificial"))}>
                        🧠 {t("topics.aiEducation", "Inteligencia Artificial")}
                    </Btn>
                    <Btn onClick={() => onAction?.("/tema_programacion_web", "💻 " + t("topics.webProgramming", "Programación Web"))}>
                        💻 {t("topics.webProgramming", "Programación Web")}
                    </Btn>
                    <Btn onClick={() => onAction?.("/tema_excel_basico", "📊 " + t("topics.excelBasic", "Excel Básico"))}>
                        📊 {t("topics.excelBasic", "Excel Básico")}
                    </Btn>
                    <Btn onClick={() => onAction?.("/explorar_temas", "🗂️ " + t("sections.topicsFeatured", "Temas destacados"))}>
                        🗂️ {t("sections.topicsFeatured", "Temas destacados")}
                    </Btn>
                </Submenu>
            )}

            {active === "zajuna" && (
                <Submenu title={t("inicio.options.ingreso", "Ingreso Zajuna")} onBack={back}>
                    <Btn onClick={() => onAction?.("/recuperar_password", "🔑 " + t("links.changePassword", "Recuperar contraseña"))}>
                        🔑 {t("links.changePassword", "Recuperar contraseña")}
                    </Btn>
                    <Btn onClick={() => onAction?.("/faq_ingreso", "🔗 " + t("links.zajunaLogin", "Enlace de ingreso"))}>
                        🔗 {t("links.zajunaLogin", "Enlace de ingreso")}
                    </Btn>
                </Submenu>
            )}

            {active === "cursos" && (
                <Submenu title={t("sections.yourActiveCourses", "Mis cursos")} onBack={back}>
                    <Btn onClick={() => onAction?.("/mis_cursos", "📋 " + t("quick_actions.view_active_courses", "Ver cursos activos"))}>
                        📋 {t("quick_actions.view_active_courses", "Ver cursos activos")}
                    </Btn>
                    <Btn onClick={() => onAction?.("/ver_progreso", "📈 " + t("quick_actions.progress", "Progreso"))}>
                        📈 {t("quick_actions.progress", "Progreso")}
                    </Btn>
                </Submenu>
            )}

            {active === "academico" && (
                <Submenu title={t("sections.whichPart", "Proceso académico")} onBack={back}>
                    <Btn onClick={() => onAction?.("/faq_certificados", "📜 " + t("faq.certificados", "Certificados"))}>
                        📜 {t("faq.certificados", "Certificados")}
                    </Btn>
                    <Btn onClick={() => onAction?.("/faq_matricula", "📝 " + t("faq.matricula", "Inscripción"))}>
                        📝 {t("faq.matricula", "Inscripción")}
                    </Btn>
                    <Btn onClick={() => onAction?.("/horarios", "⏰ " + t("quick_actions.schedules", "Horarios"))}>
                        ⏰ {t("quick_actions.schedules", "Horarios")}
                    </Btn>
                    <Btn onClick={() => onAction?.("/tutor_asignado", "👨‍🏫 " + t("quick_actions.assigned_tutor", "Tutor asignado"))}>
                        👨‍🏫 {t("quick_actions.assigned_tutor", "Tutor asignado")}
                    </Btn>
                </Submenu>
            )}

            {active === "soporte" && (
                <Submenu title={t("sections.supportOptions", "Soporte técnico")} onBack={back}>
                    <Btn onClick={() => onAction?.("/faq", "❓ " + t("quick_actions.faq", "Preguntas frecuentes"))}>
                        ❓ {t("quick_actions.faq", "Preguntas frecuentes")}
                    </Btn>

                    {/* Formulario rápido de soporte */}
                    <div className="bg-white border rounded-lg p-3 mt-2 w-full max-w-[560px]">
                        <h5 className="font-medium text-sm mb-2">📨 {t("support.form_title", "Formulario de soporte")}</h5>
                        <input
                            className="w-full border rounded px-2 py-1 text-sm mb-2"
                            placeholder={t("support.name_placeholder", "Tu nombre completo")}
                            value={form.nombre}
                            onChange={(e) => setForm((f) => ({ ...f, nombre: e.target.value }))}
                        />
                        <input
                            className="w-full border rounded px-2 py-1 text-sm mb-2"
                            placeholder={t("support.email_placeholder", "Correo de contacto")}
                            value={form.email}
                            onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                        />
                        <textarea
                            className="w-full border rounded px-2 py-1 text-sm mb-2"
                            placeholder={t("support.message_placeholder", "¿En qué necesitas ayuda?")}
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
                            {t("support.send", "Enviar")}
                        </button>
                    </div>
                </Submenu>
            )}

            {active === "info" && (
                <Submenu title={t("quick_actions.about", "¿Qué es este chatbot?")} onBack={back}>
                    <Btn onClick={() => onAction?.("/info_general", "ℹ️ " + t("quick_actions.general_info", "Información general"))}>
                        ℹ️ {t("quick_actions.general_info", "Información general")}
                    </Btn>
                    <Btn onClick={() => onAction?.("/como_usar", "💡 " + t("quick_actions.how_to_use", "Cómo usar el chatbot"))}>
                        💡 {t("quick_actions.how_to_use", "Cómo usar el chatbot")}
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
            className="px-3 py-2 rounded bg-indigo-600 text-white text-sm hover:bg-indigo-700 focus:outline-none focus:ring focus:ring-indigo-300"
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
                className="mt-1 px-3 py-1.5 rounded bg-gray-200 text-gray-900 text-xs hover:bg-gray-300 focus:outline-none focus:ring"
            >
                ⬅️ {/**/}Volver
            </button>
        </div>
    );
}

function escapeQuotes(s) {
    return String(s || "").replace(/"/g, '\\"');
}
