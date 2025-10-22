// src/components/ui/IconTooltip.jsx
import * as Tooltip from "@radix-ui/react-tooltip";
import clsx from "clsx";
import React from "react";

/** Provider global opcional */
export function TooltipProvider({ children }) {
    return (
        <Tooltip.Provider delayDuration={200} skipDelayDuration={150}>
            {children}
        </Tooltip.Provider>
    );
}

/**
 * Tooltip reutilizable con animaciones integradas
 * Props:
 * - content|label: texto del tooltip
 * - side, align, sideOffset: posicionamiento
 * - animation: 'fadeIn' | 'fadeOut' | 'pulse' | 'bounce' (default: 'fadeIn')
 */
export default function IconTooltip({
    content,
    label,
    side = "top",
    align = "center",
    sideOffset = 6,
    animation = "fadeIn",
    children,
}) {
    const text = content || label;

    // Mapeo de animaciones
    const animationMap = {
        fadeIn: "opacity-0 animate-fadeIn",
        fadeOut: "opacity-100 animate-fadeOut",
        pulse: "animate-pulse",
        bounce: "animate-bounce",
    };

    const animationClasses = clsx(
        "transition-transform duration-200 ease-in-out",
        animationMap[animation] || animationMap.fadeIn
    );

    return (
        <Tooltip.Root>
            <Tooltip.Trigger asChild>{children}</Tooltip.Trigger>
            <Tooltip.Portal>
                <Tooltip.Content
                    side={side}
                    align={align}
                    sideOffset={sideOffset}
                    className={clsx(
                        "rounded-md bg-black/90 text-white px-2 py-1 text-xs shadow z-50 dark:bg-gray-800 dark:text-gray-100",
                        animationClasses
                    )}
                >
                    <span>{text}</span>
                    <Tooltip.Arrow className="fill-current text-black dark:text-gray-800" />
                </Tooltip.Content>
            </Tooltip.Portal>
        </Tooltip.Root>
    );
}