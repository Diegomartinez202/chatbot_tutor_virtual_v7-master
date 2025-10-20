import React from "react";
import ProviderHarness from "@/snapshots/ProviderHarness";
import useHarnessMocks from "@/snapshots/useHarnessMocks";
import StatsPageV2 from "@/pages/StatsPageV2";

export default function StatsV2Harness() {
    useHarnessMocks(true);
    return (
        <ProviderHarness>
            <div className="p-4">
                <h1 className="text-xl font-semibold mb-4">Stats v2 (Harness)</h1>
                <StatsPageV2 />
            </div>
        </ProviderHarness>
    );
}