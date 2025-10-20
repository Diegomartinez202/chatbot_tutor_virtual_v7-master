import React from "react";
import IconTooltip from "@/components/ui/IconTooltip";

const TooltipWrapper = ({
    children,
    label,
    content,            // alias alternativo por compat
    side = "top",
    align = "center",
    sideOffset = 6,
    delayDuration = 200,
    disabled = false,
    asChild = true,
    className,
}) => {
    const text = content ?? label;
    if (!text || disabled) return children;

    return (
        <IconTooltip
            label={text}
            side={side}
            align={align}
            sideOffset={sideOffset}
            delayDuration={delayDuration}
            disabled={disabled}
            asChild={asChild}
            className={className}
        >
            {children}
        </IconTooltip>
    );
};

export default TooltipWrapper;