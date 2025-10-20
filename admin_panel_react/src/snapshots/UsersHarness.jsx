import React from "react";
import ProviderHarness from "@/snapshots/ProviderHarness";
import useHarnessMocks from "@/snapshots/useHarnessMocks";
import UserManagementPage from "@/pages/UserManagementPage";

export default function UsersHarness() {
    useHarnessMocks(true);
    return (
        <ProviderHarness>
            <div className="p-4">
                <h1 className="text-xl font-semibold mb-4">Usuarios (Harness)</h1>
                <UserManagementPage />
            </div>
        </ProviderHarness>
    );
}