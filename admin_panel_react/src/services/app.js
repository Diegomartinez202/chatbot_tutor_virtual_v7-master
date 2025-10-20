import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import LoginPage from "@/pages/LoginPage";
import Dashboard from "@/pages/Dashboard";
import LogsPage from "@/pages/LogsPage";
import IntentsPage from "@/pages/IntentsPage";

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<LoginPage />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/logs" element={<LogsPage />} />
                <Route path="/intents" element={<IntentsPage />} />
            </Routes>
        </Router>
    );
}

export default App;