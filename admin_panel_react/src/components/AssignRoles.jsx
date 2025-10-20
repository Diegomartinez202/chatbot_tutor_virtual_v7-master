// src/components/AssignRoles.jsx
import { useEffect, useState } from "react";
import axiosClient from "@/services/axiosClient";
import IconTooltip from "@/components/ui/IconTooltip";
import { Shield, CheckCircle, XCircle, Loader2 } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import Badge from "@/components/Badge";

const rolesDisponibles = ["admin", "soporte", "usuario"];

function AssignRoles() {
    const [users, setUsers] = useState([]);
    const [cargando, setCargando] = useState(false);
    const [mensaje, setMensaje] = useState("");
    const [mensajeTipo, setMensajeTipo] = useState(null); // "ok" | "error" | null
    const { user: currentUser } = useAuth();

    useEffect(() => {
        fetchUsers();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const fetchUsers = async () => {
        try {
            const res = await axiosClient.get("/admin/users");
            setUsers(Array.isArray(res.data) ? res.data : []);
        } catch (err) {
            console.error("Error al obtener usuarios", err);
            setMensaje("Error al obtener usuarios");
            setMensajeTipo("error");
        }
    };

    const handleRoleChange = async (userId, newRole) => {
        try {
            setCargando(true);
            setMensaje("");
            setMensajeTipo(null);

            const user = users.find((u) => (u.id || u._id) === userId);
            if (!user) throw new Error("Usuario no encontrado");

            await axiosClient.put(`/admin/users/${userId}`, {
                email: user.email,
                nombre: user.nombre,
                rol: newRole,
            });

            setMensaje("Rol actualizado correctamente");
            setMensajeTipo("ok");
            await fetchUsers();
        } catch (err) {
            console.error("Error actualizando rol", err);
            setMensaje("Error al actualizar rol");
            setMensajeTipo("error");
        } finally {
            setCargando(false);
        }
    };

    return (
        <div className="p-4 bg-white rounded shadow">
            <div className="flex items-center gap-2 mb-4">
                <IconTooltip label="Asignar Roles" side="top">
                    <Shield className="w-6 h-6 text-gray-700" />
                </IconTooltip>
                <h2 className="text-xl font-semibold">Asignar Roles</h2>
            </div>

            {mensaje && (
                <p
                    className={[
                        "mb-3 text-sm inline-flex items-center gap-2 px-3 py-2 rounded border",
                        mensajeTipo === "ok"
                            ? "text-green-700 bg-green-100 border-green-300"
                            : "text-red-700 bg-red-100 border-red-300",
                    ].join(" ")}
                    role="status"
                    aria-live="polite"
                >
                    {mensajeTipo === "ok" ? (
                        <CheckCircle className="w-4 h-4" />
                    ) : (
                        <XCircle className="w-4 h-4" />
                    )}
                    <span>{mensaje}</span>
                </p>
            )}

            {cargando && (
                <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
                    <Loader2 className="w-4 h-4 animate-spin" /> Actualizando…
                </div>
            )}

            <table className="w-full table-auto border text-sm">
                <thead className="bg-gray-100">
                    <tr>
                        <th className="p-2 text-left">Nombre</th>
                        <th className="p-2 text-left">Correo</th>
                        <th className="p-2 text-left">Rol</th>
                        <th className="p-2">Cambiar Rol</th>
                    </tr>
                </thead>
                <tbody>
                    {users.map((user) => {
                        const uid = user.id || user._id;
                        const isSelf = uid === currentUser?._id;
                        const roleValue = (user.rol || "usuario");

                        return (
                            <tr key={uid} className="border-t">
                                <td className="p-2">{user.nombre}</td>
                                <td className="p-2">{user.email}</td>
                                <td className="p-2 capitalize">
                                    <Badge type="role" value={roleValue} />
                                </td>
                                <td className="p-2">
                                    <IconTooltip
                                        label={isSelf ? "No puedes cambiar tu propio rol" : "Cambiar rol del usuario"}
                                        side="top"
                                    >
                                        <select
                                            value={user.rol}
                                            onChange={(e) => handleRoleChange(uid, e.target.value)}
                                            disabled={cargando || isSelf}
                                            className="border p-1 rounded bg-white"
                                            aria-label={`Cambiar rol de ${user.email}`}
                                        >
                                            {rolesDisponibles.map((rol) => (
                                                <option key={rol} value={rol}>
                                                    {rol}
                                                </option>
                                            ))}
                                        </select>
                                    </IconTooltip>
                                    {isSelf && <span className="text-xs text-gray-500 ml-2">(tú)</span>}
                                </td>
                            </tr>
                        );
                    })}
                    {users.length === 0 && (
                        <tr>
                            <td colSpan={4} className="p-4 text-center text-gray-500">
                                No hay usuarios para mostrar.
                            </td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
    );
}

export default AssignRoles;