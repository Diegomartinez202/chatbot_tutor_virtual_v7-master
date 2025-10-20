// src/components/IntentsForm.jsx
import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import IconTooltip from "@/components/ui/IconTooltip";
import toast from "react-hot-toast";
import { PlusCircle, HelpCircle } from "lucide-react";

const IntentsForm = () => {
    const [intent, setIntent] = useState("");
    const [example, setExample] = useState("");
    const [response, setResponse] = useState("");

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!intent.trim() || !example.trim() || !response.trim()) {
            toast.error("Todos los campos son obligatorios");
            return;
        }

        // Aquí puedes usar tu servicio real
        toast.success("Intent enviado correctamente (simulado)");
        setIntent("");
        setExample("");
        setResponse("");
    };

    return (
        <form
            onSubmit={handleSubmit}
            className="space-y-4 bg-gray-50 p-4 rounded shadow-md"
            noValidate
        >
            {/* Intent */}
            <div>
                <label className="block font-semibold mb-1">
                    Intent:
                    <IconTooltip label="Nombre interno del intent, ej: saludo, ver_certificados">
                        <HelpCircle className="inline-block w-4 h-4 ml-1 text-gray-500 align-middle" />
                    </IconTooltip>
                </label>
                <input
                    type="text"
                    required
                    className="w-full border px-3 py-2 rounded outline-none focus:ring-2 focus:ring-indigo-300"
                    value={intent}
                    onChange={(e) => setIntent(e.target.value)}
                    placeholder="ej: saludo"
                    autoComplete="off"
                    aria-required="true"
                />
            </div>

            {/* Ejemplo */}
            <div>
                <label className="block font-semibold mb-1">
                    Ejemplo:
                    <IconTooltip label="Frase de ejemplo del usuario que activa el intent">
                        <HelpCircle className="inline-block w-4 h-4 ml-1 text-gray-500 align-middle" />
                    </IconTooltip>
                </label>
                <input
                    type="text"
                    required
                    className="w-full border px-3 py-2 rounded outline-none focus:ring-2 focus:ring-indigo-300"
                    value={example}
                    onChange={(e) => setExample(e.target.value)}
                    placeholder="ej: Hola, ¿cómo estás?"
                    autoComplete="off"
                    aria-required="true"
                />
            </div>

            {/* Respuesta */}
            <div>
                <label className="block font-semibold mb-1">
                    Respuesta:
                    <IconTooltip label="Texto que responderá el bot; para rich messages usa 'custom' en Rasa">
                        <HelpCircle className="inline-block w-4 h-4 ml-1 text-gray-500 align-middle" />
                    </IconTooltip>
                </label>
                <input
                    type="text"
                    required
                    className="w-full border px-3 py-2 rounded outline-none focus:ring-2 focus:ring-indigo-300"
                    value={response}
                    onChange={(e) => setResponse(e.target.value)}
                    placeholder="ej: ¡Hola! Estoy aquí para ayudarte."
                    autoComplete="off"
                    aria-required="true"
                />
            </div>

            <IconTooltip label="Agregar un nuevo intent">
                <Button
                    type="submit"
                    className="bg-green-600 hover:bg-green-700 text-white inline-flex items-center gap-2"
                    aria-label="Agregar intent"
                >
                    <PlusCircle className="w-4 h-4" />
                    <span>Agregar Intent</span>
                </Button>
            </IconTooltip>
        </form>
    );
};

export default IntentsForm;