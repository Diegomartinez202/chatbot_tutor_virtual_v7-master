import React from "react";
import ProviderHarness from "@/snapshots/ProviderHarness";
import useHarnessMocks from "@/snapshots/useHarnessMocks";
import AssignRoles from "@/pages/AssignRoles";

export default function AssignRolesHarness() {
    useHarnessMocks(true);
    return (
        <ProviderHarness>
            <div className="p-4">
                <h1 className="text-xl font-semibold mb-4">Asignar roles (Harness)</h1>
                <AssignRoles />
            </div>
        </ProviderHarness>
    );
}