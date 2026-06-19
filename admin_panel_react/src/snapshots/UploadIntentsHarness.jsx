import React from "react";
import ProviderHarness from "@/snapshots/ProviderHarness";
import useHarnessMocks from "@/snapshots/useHarnessMocks";
import UploadIntentsCSV from "@/components/UploadIntentsCSV";

export default function UploadIntentsHarness() {
    useHarnessMocks(true);
    return (
        <ProviderHarness>
            <div className="p-4">
                <h1 className="text-xl font-semibold mb-4">Upload Intents CSV (Harness)</h1>
                <UploadIntentsCSV />
            </div>
        </ProviderHarness>
    );
}