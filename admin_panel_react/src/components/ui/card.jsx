// src/components/ui/card.jsx
import React from "react";
import classNames from "classnames";
import IconTooltip from "@/components/ui/IconTooltip";
import { ROLE_STYLES, STATUS_STYLES, INTENT_STYLES } from "@/lib/constants";

/** util simple tipo clsx */
const cn = (...args) => args.filter(Boolean).join(" ");

/**
 * Card
 * - Mantiene la API previa.
 * - Nuevo: `tooltip` opcional para envolver el contenedor con IconTooltip.
 */
export function Card({ className, tooltip, children, ...props }) {
    const inner = (
        <div
            className={cn("rounded-xl border bg-white text-gray-900 shadow-sm", className)}
            data-testid="ui-card"
            {...props}
        >
            {children}
        </div>
    );
    return tooltip ? <IconTooltip label={tooltip}>{inner}</IconTooltip> : inner;
}

/**
 * CardHeader
 * - Nuevo: `tooltip` opcional para tooltip de todo el header.
 */
export function CardHeader({ className, tooltip, children, ...props }) {
    const inner = (
        <div className={classNames("p-4 border-b", className)} {...props}>
            {children}
        </div>
    );
    return tooltip ? <IconTooltip label={tooltip}>{inner}</IconTooltip> : inner;
}

/**
 * CardTitle
 * - Mantiene API.
 * - Nuevo: `tooltip`, `leadingIcon`, `trailingIcon`.
 */
export function CardTitle({
    className,
    tooltip,
    leadingIcon: LeadingIcon,
    trailingIcon: TrailingIcon,
    children,
    ...props
}) {
    const content = (
        <h3
            className={classNames("text-base font-semibold leading-none flex items-center gap-2", className)}
            {...props}
        >
            {LeadingIcon ? <LeadingIcon className="w-4 h-4" /> : null}
            <span>{children}</span>
            {TrailingIcon ? <TrailingIcon className="w-4 h-4" /> : null}
        </h3>
    );
    return tooltip ? <IconTooltip label={tooltip}>{content}</IconTooltip> : content;
}

/**
 * CardDescription
 * - Nuevo: `tooltip` opcional.
 */
export function CardDescription({ className, tooltip, children, ...props }) {
    const inner = (
        <p className={classNames("text-sm text-gray-500", className)} {...props}>
            {children}
        </p>
    );
    return tooltip ? <IconTooltip label={tooltip}>{inner}</IconTooltip> : inner;
}

export function CardContent({ className, ...props }) {
    return <div className={classNames("p-4", className)} {...props} />;
}

export function CardFooter({ className, ...props }) {
    return <div className={classNames("p-4 border-t", className)} {...props} />;
}

/**
 * CardBadge
 * - Chip pequeño (role/status/intent/neutral) para usar dentro de headers o títulos.
 * - Usa ROLE_STYLES / STATUS_STYLES / INTENT_STYLES de tu proyecto.
 * - Soporta `tooltip`, `size`, `leadingIcon`, `trailingIcon`.
 */
export function CardBadge({
    type = "neutral", // "role" | "status" | "intent" | "neutral"
    value = "",
    size = "sm", // "xs" | "sm" | "md"
    tooltip,
    className = "",
    leadingIcon: LeadingIcon,
    trailingIcon: TrailingIcon,
    ...rest
}) {
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

    const chip = (
        <span
            className={cn(
                "inline-flex items-center gap-1.5 rounded-full font-medium",
                sizing[size] || sizing.sm,
                style,
                className
            )}
            {...rest}
        >
            {LeadingIcon ? <LeadingIcon className="w-3.5 h-3.5" /> : null}
            {String(value)}
            {TrailingIcon ? <TrailingIcon className="w-3.5 h-3.5" /> : null}
        </span>
    );

    return tooltip ? <IconTooltip label={tooltip}>{chip}</IconTooltip> : chip;
}