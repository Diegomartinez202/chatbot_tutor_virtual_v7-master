// src/components/BackButton.jsx
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import IconTooltip from "@/components/ui/IconTooltip";
import { ArrowLeft } from "lucide-react";

const BackButton = ({
    to = "/",
    label = "Volver",
    className = "",
    icon: Icon = ArrowLeft,
    tooltip,
    variant = "outline",
    size,             // opcional: pasa tal cual a <Button />
    disabled = false,
    replace = false,  // opcional: usa navigate(to, { replace })
    type = "button",
    onClick,          // opcional: si devuelve e.preventDefault(), no navega
}) => {
    const navigate = useNavigate();

    const handleClick = (e) => {
        if (onClick) onClick(e);
        if (e?.defaultPrevented) return;
        navigate(to, { replace });
    };

    return (
        <IconTooltip label={tooltip || label} side="top">
            <Button
                type={type}
                variant={variant}
                size={size}
                disabled={disabled}
                onClick={handleClick}
                className={`inline-flex items-center gap-2 ${className}`}
                aria-label={label}
            >
                <Icon className="w-4 h-4" aria-hidden="true" />
                {label}
            </Button>
        </IconTooltip>
    );
};

export default BackButton;