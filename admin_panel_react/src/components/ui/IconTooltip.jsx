// src/components/ui/IconTooltip.jsx
import React from "react";

/**
 * Shim de Tooltip minimalista y accesible.
 * - Mantiene compatibilidad con importaciones existentes:
 *   { TooltipProvider } y el componente por defecto IconTooltip
 * - Exporta adicionalmente Tooltip, TooltipTrigger, TooltipContent
 *   para componentes que los importan (p. ej., LanguageSelector.jsx)
 */

export function TooltipProvider({ children }) {
  return <>{children}</>;
}

export function Tooltip({ children, ...props }) {
  return (
    <span className="relative inline-flex group" {...props}>
      {children}
    </span>
  );
}

export function TooltipTrigger({ children, ...props }) {
  // Se apoya en title (fallback) si no hay TooltipContent declarado
  return (
    <span
      role="button"
      tabIndex={0}
      className="inline-flex items-center"
      {...props}
    >
      {children}
    </span>
  );
}

export function TooltipContent({ children }) {
  // Se muestra al pasar el mouse si el contenedor usa :hover (group-hover)
  return (
    <span
      className="pointer-events-none absolute z-[1000] -top-8 left-1/2 -translate-x-1/2 whitespace-nowrap
                 rounded-md border border-zinc-200 bg-white px-2 py-1 text-xs text-zinc-800 shadow
                 opacity-0 group-hover:opacity-100 transition-opacity"
      role="tooltip"
    >
      {children}
    </span>
  );
}

/**
 * IconTooltip - uso sencillo:
 * <IconTooltip label="Texto"><button>...</button></IconTooltip>
 */
export default function IconTooltip({ label, side = "top", children }) {
  // 'side' está para compatibilidad, este shim usa posición superior por defecto
  return (
    <span className="relative inline-flex group align-middle">
      <span aria-label={label} title={label}>
        {children}
      </span>
      <span
        className="pointer-events-none absolute z-[1000] -top-8 left-1/2 -translate-x-1/2 whitespace-nowrap
                   rounded-md border border-zinc-200 bg-white px-2 py-1 text-xs text-zinc-800 shadow
                   opacity-0 group-hover:opacity-100 transition-opacity"
        role="tooltip"
      >
        {label}
      </span>
    </span>
  );
}