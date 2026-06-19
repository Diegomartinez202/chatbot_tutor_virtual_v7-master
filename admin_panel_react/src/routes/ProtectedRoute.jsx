import { Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

const ProtectedRoute = ({ children, allowedRoles = [] }) => {
    const { isAuthenticated, user, redirectToZajunaSSO } = useAuth();
    const zajunaSSO = import.meta.env.VITE_ZAJUNA_SSO_URL;

    if (!isAuthenticated) {
        // Si hay SSO, redirigir automáticamente
        if (zajunaSSO) {
            redirectToZajunaSSO();
            return null; // Evitar renderizar antes de redirigir
        }
        return <Navigate to="/login" />;
    }

    if (allowedRoles.length && !allowedRoles.includes(user?.rol)) {
        return <Navigate to="/unauthorized" />;
    }

    return children;
};

export default ProtectedRoute;