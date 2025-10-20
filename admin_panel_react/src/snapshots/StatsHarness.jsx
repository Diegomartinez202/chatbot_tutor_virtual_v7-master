// src/snapshots/StatsHarness.jsx
import React from "react";
import ProviderHarness from "./ProviderHarness";

// TODO: ajusta import a tu StatsPage real:
import StatsPage from "@/pages/StatsPage";

export default function StatsHarness() {
    return (
        <ProviderHarness>
            <main data-testid="app-root" className="p-6">
                <StatsPage />
            </main>
        </ProviderHarness>
    );
}
