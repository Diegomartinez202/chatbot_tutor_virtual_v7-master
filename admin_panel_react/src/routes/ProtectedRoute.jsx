import { Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

const ProtectedRoute = ({ children, allowedRoles = [] }) => {
    const { isAuthenticated, user } = useAuth();

    if (!isAuthenticated) return <Navigate to="/login" />;
    if (allowedRoles.length && !allowedRoles.includes(user?.rol)) {
        return <Navigate to="/unauthorized" />;
    }

    return children;
};

export default ProtectedRoute;