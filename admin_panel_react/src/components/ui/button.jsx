import React, { forwardRef } from "react";
import { Loader2 } from "lucide-react";

// util simple para concatenar clases
function cn(...classes) {
    return classes.filter(Boolean).join(" ");
}

// Variantes modernas (shadcn-style) + mapeo retro-compat
const VARIANTS = {
    default: "bg-indigo-600 text-white hover:bg-indigo-700",
    outline: "border border-gray-300 text-gray-800 hover:bg-gray-50",
    ghost: "bg-transparent text-gray-700 hover:bg-gray-100",
    secondary: "bg-gray-800 text-white hover:bg-gray-900",
    destructive: "bg-red-600 text-white hover:bg-red-700",
    link: "bg-transparent text-indigo-600 underline-offset-4 hover:underline px-0 h-auto",
};

// Tamaños
const SIZES = {
    sm: "h-8 px-3 text-sm",
    md: "h-10 px-4 text-sm",
    lg: "h-11 px-5",
    icon: "h-10 w-10 p-0",
};

// Base común
const BASE =
    "inline-flex items-center justify-center rounded-md transition-colors " +
    "focus:outline-none focus:ring-2 focus:ring-indigo-300 " +
    "disabled:opacity-50 disabled:pointer-events-none";

// Mapeo de variantes legacy → modernas
function mapLegacyVariant(variant) {
    if (variant === "primary") return "default";
    // "secondary", "destructive", "ghost" ya existen en la nueva lista
    return variant;
}

/**
 * Button
 * - Soporta `as` para renderizar como otro componente/elemento (div, a, Link, etc.)
 * - loading: muestra spinner y deshabilita
 * - variant/size: estilos predefinidos
 * - Retro-compat: variant="primary" → "default"
 */
const Button = forwardRef(
    (
        {
            as: Comp = "button", // compat con tu versión anterior
            variant = "default",
            size = "md",
            loading = false,
            className = "",
            children,
            type, // opcional: si es <button>, default será "button"
            ...props
        },
        ref
    ) => {
        const resolvedVariant = mapLegacyVariant(variant);
        const classes = cn(
            BASE,
            VARIANTS[resolvedVariant] || VARIANTS.default,
            SIZES[size] || SIZES.md,
            className
        );

        const isButtonElement = Comp === "button";

        return (
            <Comp
                ref={ref}
                className={classes}
                data-variant={resolvedVariant}
                data-size={size}
                aria-busy={loading || undefined}
                disabled={(props.disabled || loading) && isButtonElement ? true : undefined}
                type={isButtonElement ? (type || "button") : undefined}
                {...props}
            >
                {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
                {children ?? (loading ? "Cargando…" : "Botón")}
            </Comp>
        );
    }
);

Button.displayName = "Button";

// Export default + named (compat con `import Button from` y `import { Button } from`)
export { Button };
export default Button;