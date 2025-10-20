// src/pages/ForgotPasswordPage.jsx
import React, { useState } from "react";
import { Link } from "react-router-dom";
import Input from "@/components/Input";
import IconTooltip from "@/components/ui/IconTooltip";
import { Mail, LifeBuoy } from "lucide-react";
import { toast } from "react-hot-toast";

import { forgotPassword as apiForgot } from "@/services/authApi";

export default function ForgotPasswordPage() {
    const [email, setEmail] = useState("");
    const [loading, setLoading] = useState(false);
    const [info, setInfo] = useState("");
    const [err, setErr] = useState("");

    const handleSubmit = async (e) => {
        e.preventDefault();
        setErr("");
        setInfo("");

        if (!email.trim()) return setErr("Escribe tu correo.");

        setLoading(true);
        try {
            await apiForgot({ email });
            setInfo("Si el correo existe, te enviaremos instrucciones para recuperar tu contraseña.");
            toast.success("Revisa tu correo para continuar.");
        } catch (e2) {
            const msg =
                e2?.response?.data?.message ||
                e2?.response?.data?.error ||
                e2?.message ||
                "No se pudo procesar la solicitud.";
            setErr(msg);
            toast.error(msg);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-[70vh] grid place-items-center p-6">
            <div className="w-full max-w-md bg-white rounded-2xl shadow p-6">
                <div className="flex items-center gap-2 mb-4">
                    <IconTooltip label="Recuperar contraseña" side="top">
                        <LifeBuoy className="w-6 h-6 text-indigo-600" />
                    </IconTooltip>
                    <h1 className="text-xl font-semibold">Recuperar contraseña</h1>
                </div>

                <form onSubmit={handleSubmit} aria-describedby="forgot-error">
                    <Input
                        label="Email"
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="correo@ejemplo.com"
                        name="email"
                        required
                        leadingIcon={<Mail className="w-4 h-4 text-gray-500" />}
                    />

                    <button
                        type="submit"
                        disabled={loading}
                        aria-busy={loading}
                        className="mt-2 w-full inline-flex items-center justify-center rounded-lg bg-indigo-600 text-white px-5 py-2.5 text-sm font-medium hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-400 disabled:opacity-60"
                    >
                        {loading ? "Enviando…" : "Enviar instrucciones"}
                    </button>
                </form>

                {err && (
                    <p id="forgot-error" className="text-red-600 mt-2" role="alert">
                        {err}
                    </p>
                )}
                {info && (
                    <p className="text-green-700 mt-2" role="status">
                        {info}
                    </p>
                )}

                <div className="mt-4 text-sm text-gray-600 flex items-center justify-between">
                    <Link to="/" className="hover:underline">
                        ← Volver al inicio
                    </Link>
                    <Link to="/login" className="hover:underline">
                        Volver al login
                    </Link>
                </div>
            </div>
        </div>
    );
}