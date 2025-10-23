// src/components/UserModal.jsx
import React, { useState, useCallback, useEffect, useRef } from "react";
import { UserPlus, X, Info, ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import IconTooltip from "@/components/ui/IconTooltip";
import UserForm from "./UserForm";
import { useAuth } from "@/context/AuthContext"; // ✅ para validar rol de usuario
import { toast } from "react-hot-toast";

const UserModal = ({ onSubmit }) => {
    const [open, setOpen] = useState(false);
    const dialogRef = useRef(null);
    const { user } = useAuth(); // ✅ usuario actual

    // 🔒 Validación de permisos
    const canCreateUser = user?.rol === "admin" || user?.rol === "soporte";

    const handleSubmit = (data) => {
        // 🔒 Validación interna adicional por si alguien forza desde la consola
        if (!canCreateUser) {
            toast.error("No tienes permisos para crear usuarios.");
            return;
        }

        onSubmit?.(data);
        setOpen(false);
    };

    const onClose = () => setOpen(false);

    const onBackdrop = (e) => {
        if (e.target === e.currentTarget) onClose();
    };

    const onEsc = useCallback((e) => {
        if (e.key === "Escape") onClose();
    }, []);

    useEffect(() => {
        if (!open) return;
        const node = dialogRef.current;
        if (!node) return;

        const tryFocusFirst = () => {
            const focusables = node.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            if (focusables.length) focusables[0]?.focus?.();
            else node.focus();
        };
        setTimeout(tryFocusFirst, 0);

        const handleKeyDown = (ev) => {
            if (ev.key !== "Tab") return;
            const focusables = Array.from(
                node.querySelectorAll(
                    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
                )
            ).filter((el) => !el.hasAttribute("disabled") && !el.getAttribute("aria-hidden"));
            if (!focusables.length) return;

            const first = focusables[0];
            const last = focusables[focusables.length - 1];
            if (!ev.shiftKey && document.activeElement === last) {
                ev.preventDefault();
                first.focus();
            } else if (ev.shiftKey && document.activeElement === first) {
                ev.preventDefault();
                last.focus();
            }
        };

        document.addEventListener("keydown", onEsc);
        node.addEventListener("keydown", handleKeyDown);

        return () => {
            document.removeEventListener("keydown", onEsc);
            node.removeEventListener("keydown", handleKeyDown);
        };
    }, [open, onEsc]);

    // 🚫 No mostrar botón ni modal si no hay permisos
    if (!canCreateUser) {
        return (
            <div className="text-center text-gray-500 mt-4 flex items-center justify-center gap-2">
                <ShieldAlert className="w-4 h-4 text-red-500" />
                <span>No tienes permisos para crear usuarios.</span>
            </div>
        );
    }

    return (
        <div>
            <IconTooltip label="Crear un nuevo usuario" side="top">
                <span>
                    <Button
                        onClick={() => setOpen(true)}
                        className="flex items-center gap-2"
                        type="button"
                        aria-haspopup="dialog"
                        aria-expanded={open}
                        aria-controls="user-modal"
                    >
                        <UserPlus className="w-4 h-4" />
                        Crear Usuario
                    </Button>
                </span>
            </IconTooltip>

            {open && (
                <div
                    className="fixed inset-0 flex items-center justify-center bg-black/50 z-50"
                    onMouseDown={onBackdrop}
                    role="presentation"
                >
                    <div
                        id="user-modal"
                        ref={dialogRef}
                        className="bg-white p-6 rounded shadow-md w-full max-w-md relative outline-none"
                        role="dialog"
                        aria-modal="true"
                        aria-labelledby="new-user-title"
                        tabIndex={-1}
                        onMouseDown={(e) => e.stopPropagation()}
                    >
                        <IconTooltip label="Cerrar" side="left">
                            <button
                                onClick={onClose}
                                className="absolute top-2 right-2 text-red-500 p-1 rounded hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-300"
                                aria-label="Cerrar modal"
                                type="button"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </IconTooltip>

                        <div className="flex items-center gap-2 mb-4">
                            <h2 id="new-user-title" className="text-xl font-bold">
                                Nuevo Usuario
                            </h2>
                            <IconTooltip label="Completa los campos y asigna un rol. Email y contraseña son obligatorios.">
                                <Info className="w-4 h-4 text-gray-500" aria-hidden="true" />
                            </IconTooltip>
                        </div>

                        <UserForm onSubmit={handleSubmit} />
                    </div>
                </div>
            )}
        </div>
    );
};

export default UserModal;