import React from "react";
import ProviderHarness from "@/snapshots/ProviderHarness";
import useHarnessMocks from "@/snapshots/useHarnessMocks";
import LogsPage from "@/pages/LogsPage";

export default function LogsHarness() {
    useHarnessMocks(true);
    return (
        <ProviderHarness>
            <div className="p-4">
                <h1 className="text-xl font-semibold mb-4">Logs (Harness)</h1>
                <LogsPage />
            </div>
        </ProviderHarness>
    );
}