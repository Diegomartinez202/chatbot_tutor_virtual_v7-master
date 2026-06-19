// src/components/RequireRole.jsx
import { Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext"; // ✅ acceso al usuario y loading

const RequireRole = ({ allowedRoles = [], children }) => {
    const { user, loading } = useAuth();

    if (loading) return <p className="p-4">Cargando...</p>;

    if (!user || !allowedRoles.includes(user.rol)) {
        return <Navigate to="/unauthorized" replace />;
    }

    return children;
};

export default RequireRole;