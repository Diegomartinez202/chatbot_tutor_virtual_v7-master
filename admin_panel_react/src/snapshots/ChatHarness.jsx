import { BrowserRouter, Routes, Route } from "react-router-dom";
import Harness from "@/pages/Harness";
import ChatHarness from "@/snapshots/ChatHarness";
// ...otros imports

export default function App() {
    return (
        <BrowserRouter>
            <Routes>
                {/* ...otras rutas */}
                <Route path="/chat" element={<Harness />} />
                <Route path="/snapshots/chat" element={<ChatHarness />} />
            </Routes>
        </BrowserRouter>
    );
}