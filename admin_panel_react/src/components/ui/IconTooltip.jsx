import * as Tooltip from "@radix-ui/react-tooltip";

/** Úsalo alrededor de tu layout para un solo Provider global (opcional). */
export function TooltipProvider({ children }) {
    return (
        <Tooltip.Provider delayDuration={200} skipDelayDuration={150}>
            {children}
        </Tooltip.Provider>
    );
}

/**
 * Wrapper reutilizable.
 * - Si ya usas <TooltipProvider>, puedes usar IconTooltip sin problema (Radix tolera Providers anidados).
 * - Props: content|label, side, align, sideOffset.
 */
export default function IconTooltip({
    content,
    label,
    side = "top",
    align = "center",
    sideOffset = 6,
    children,
}) {
    const text = content || label;
    return (
        <Tooltip.Root>
            <Tooltip.Trigger asChild>{children}</Tooltip.Trigger>
            <Tooltip.Portal>
                <Tooltip.Content
                    side={side}
                    align={align}
                    sideOffset={sideOffset}
                    className="rounded-md bg-black/90 text-white px-2 py-1 text-xs shadow z-50"
                >
                    <span>{text}</span>
                    <Tooltip.Arrow className="fill-black/90" />
                </Tooltip.Content>
            </Tooltip.Portal>
        </Tooltip.Root>
    );
}