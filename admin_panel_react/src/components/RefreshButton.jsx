import React from "react";
import { RefreshCw } from "lucide-react";
import IconTooltip from "@/components/ui/IconTooltip";
import { Button } from "@/components/ui/button";

export default function RefreshButton({
  onClick,
  loading = false,
  className = "",
  label = "Recargar",
  tooltipLabel = "Recargar",
  variant = "outline",
  size = "sm",
  ...rest
}) {
  return (
    <IconTooltip label={tooltipLabel} side="top">
      <Button
        type="button"
        onClick={onClick}
        disabled={loading}
        variant={variant}
        size={size}
        className={className}
        aria-label={label}
        {...rest}
      >
        <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} />
        {loading ? "Cargando…" : label}
      </Button>
    </IconTooltip>
  );
}