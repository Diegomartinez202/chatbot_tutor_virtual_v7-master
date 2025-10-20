import React from "react";
import ProviderHarness from "@/snapshots/ProviderHarness";
import useHarnessMocks from "@/snapshots/useHarnessMocks";
import ChatPage from "@/pages/ChatPage";

/**
 * Chat de página completa usando tu ChatPage real.
 * Reutiliza los mocks del hook para /api/chat/*, /api/users/me, etc.
 */
export default function ChatFullHarness() {
    useHarnessMocks(true); // activa mocks globales del harness
    return (
        <ProviderHarness>
            <div className="p-4">
                <h1 className="text-xl font-semibold mb-4">Chat — Página completa (Harness)</h1>
                <ChatPage />
            </div>
        </ProviderHarness>
    );
}