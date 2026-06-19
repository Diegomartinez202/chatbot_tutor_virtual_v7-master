import { useEffect } from "react";

export function useAvatarPreload(url) {
    useEffect(() => {
        if (!url) return;
        const img = new Image();
        img.src = url; // dispara la precarga 1 sola vez por cambio de URL
    }, [url]);
}