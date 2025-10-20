// src/components/Badge.jsx
import React, { useEffect, useMemo, useState } from "react";
import IconTooltip from "@/components/ui/IconTooltip";
import { ROLE_STYLES, STATUS_STYLES, INTENT_STYLES } from "@/lib/constants";

/**
 * Util simple tipo clsx
 */
const cn = (...args) => args.filter(Boolean).join(" ");

/**
 * Normaliza un origin para comparación (sin slash final, sin espacios)
 */
const normalizeOrigin = (o = "") => (o || "").trim().replace(/\/+$/, "");

/**
 * Badge unificado:
 * - Modo "static": chip estilizado (role/status/intent/neutral) con tooltip opcional.
 * - Modo "chat": globo contador que escucha postMessage con validación de orígenes.
 *
 * Props principales:
 *  mode: "static" | "chat" (default: "static")
 *
 *  — STATIC —
 *  type: "role" | "status" | "intent" | "neutral"  (default: "neutral")
 *  value: string  (texto del chip)
 *  variant: string (compat; si llega, asume type="role" y value=variant)
 *  size: "xs" | "sm" | "md" (default: "sm")
 *  tooltip: string (si viene, envuelve con IconTooltip)
 *  leadingIcon / trailingIcon: componentes de ícono (lucide)
 *
 *  — CHAT —
 *  initialCount: number (default: 0)
 *  resetOnOpen: boolean (default: true) → al recibir {type:"chat:visibility", open:true} resetea a 0
 *  badgeClassName: estilos extra para el globo de chat
 *  allowedOrigins: sobreescribe VITE_ALLOWED_HOST_ORIGINS (CSV). Si no se pasa, usa ENV.
 *
 * Seguridad (chat):
 *  - Siempre acepta el mismo origin (window.location.origin)
 *  - Acepta orígenes listados en VITE_ALLOWED_HOST_ORIGINS (CSV)
 */

export default function Badge(props) {
    const {
        // Modo
        mode = "static",

        // STATIC
        type: _type = "neutral",
        value: _value = "",
        variant,
        className = "",
        children,
        size = "sm",
        tooltip,
        leadingIcon: LeadingIcon,
        trailingIcon: TrailingIcon,
        "aria-label": ariaLabel,

        // CHAT
        initialCount = 0,
        resetOnOpen = true,
        badgeClassName = "",
        allowedOrigins, // CSV opcional para sobreescribir ENV
    } = props;

    /**
     * ─────────────────────────────────────────────────────────────
     * MODO STATIC
     * ─────────────────────────────────────────────────────────────
     */
    if (mode === "static") {
        let type = _type;
        let value = _value;

        // Compat: si viene "variant" y no "value", asumimos role
        if (variant && !value) {
            value = variant;
            if (type === "neutral") type = "role";
        }

        const maps = {
            role: ROLE_STYLES || {},
            status: STATUS_STYLES || {},
            intent: INTENT_STYLES || {},
            neutral: {},
        };

        const sizing = {
            xs: "px-1.5 py-0.5 text-[10px]",
            sm: "px-2 py-0.5 text-xs",
            md: "px-2.5 py-1 text-sm",
        };

        const style =
            (maps[type] && maps[type][String(value).toLowerCase()]) ||
            "bg-gray-100 text-gray-800";

        const content = (
            <span
                className={cn(
                    "inline-flex items-center gap-1.5 rounded-full font-medium",
                    sizing[size] || sizing.sm,
                    style,
                    className
                )}
                title={!tooltip && typeof value === "string" ? value : undefined}
                aria-label={ariaLabel || (typeof value === "string" ? value : undefined)}
            >
                {LeadingIcon ? <LeadingIcon className="w-3.5 h-3.5" /> : null}
                {children ?? value ?? ""}
                {TrailingIcon ? <TrailingIcon className="w-3.5 h-3.5" /> : null}
            </span>
        );

        return tooltip ? (
            <IconTooltip label={tooltip} side="top">
                {content}
            </IconTooltip>
        ) : (
            content
        );
    }

    /**
     * ─────────────────────────────────────────────────────────────
     * MODO CHAT
     * ─────────────────────────────────────────────────────────────
     */
    const [count, setCount] = useState(Number(initialCount) || 0);

    // Lista de orígenes permitidos (ENV o prop)
    const allowed = useMemo(() => {
        const raw =
            typeof allowedOrigins === "string"
                ? allowedOrigins
                : import.meta.env.VITE_ALLOWED_HOST_ORIGINS || "";
        return raw
            .split(",")
            .map((s) => normalizeOrigin(s))
            .filter(Boolean);
    }, [allowedOrigins]);

    // Validación de orígenes: mismo origin siempre OK, o en la lista permitida
    const isAllowed = (origin) => {
        const o = normalizeOrigin(origin);
        return (
            o === normalizeOrigin(window.location.origin) ||
            (allowed.length > 0 && allowed.includes(o))
        );
    };

    useEffect(() => {
        const onMsg = (ev) => {
            if (!ev?.origin || !isAllowed(ev.origin)) return;
            const data = ev.data || {};
            if (data?.type === "chat:badge" && typeof data.count === "number") {
                setCount(data.count);
            }
            if (resetOnOpen && data?.type === "chat:visibility" && data.open === true) {
                setCount(0);
            }
        };
        window.addEventListener("message", onMsg);
        return () => window.removeEventListener("message", onMsg);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [allowed.join("|"), resetOnOpen]);

    // Si no hay contador, no mostramos nada
    if (!count) return null;

    return (
        <span
            className={cn(
                "ml-2 inline-flex items-center justify-center rounded-full bg-red-600 text-white text-xs px-2 py-0.5",
                badgeClassName
            )}
            aria-label={`${count} mensajes sin leer`}
            data-testid="chat-badge"
            role="status"
        >
            {count}
        </span>
    );
}