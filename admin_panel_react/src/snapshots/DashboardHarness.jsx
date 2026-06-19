// src/snapshots/DashboardHarness.jsx
import React from "react";
import ProviderHarness from "./ProviderHarness";

// TODO: ajusta import a tu Dashboard real:
import DashboardPage from "@/pages/DashboardPage";

export default function DashboardHarness() {
    return (
        <ProviderHarness>
            <main data-testid="app-root" className="p-6">
                <DashboardPage />
            </main>
        </ProviderHarness>
    );
}
