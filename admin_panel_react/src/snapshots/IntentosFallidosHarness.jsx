// src/snapshots/IntentosFallidosHarness.jsx
import React from "react";
import ProviderHarness from "./ProviderHarness";

// TODO: ajusta import a tu p�gina real:
import IntentosFallidosPage from "@/pages/IntentosFallidosPage";

export default function IntentosFallidosHarness() {
    return (
        <ProviderHarness>
            <main data-testid="app-root" className="p-6">
                <IntentosFallidosPage />
            </main>
        </ProviderHarness>
    );
}
