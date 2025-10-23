// src/pages/UserManagement.jsx
import React, { useEffect, useState } from "react";
import { Users as UsersIcon, Trash2, AlertCircle } from "lucide-react";
import { toast } from "react-hot-toast";
import { useAuth } from "@/context/AuthContext";

import { getUsers, createUser, deleteUser } from "@/services/api";
import IconTooltip from "@/components/ui/IconTooltip";
import RefreshButton from "@/components/RefreshButton";
import UserModal from "@/components/UserModal";
import Badge from "@/components/Badge";

export default function UserManagement() {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(false);
    const { user: currentUser } = useAuth();

    const canCreate = currentUser?.rol === "admin" || currentUser?.rol === "soporte";

    const loadUsers = async () => {
        setLoading(true);
        try {
            const data = await getUsers();
            setUsers(Array.isArray(data) ? data : []);
        } catch (e) {
            console.error(e);
            toast.error("No se pudieron cargar los usuarios");
            setUsers([]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadUsers();
    }, []);

    const handleCreate = async (payload) => {
        try {
            await createUser(payload);
            toast.success("Usuario creado correctamente");
            await loadUsers();
        } catch (e) {
            console.error(e);
            const msg =
                e?.response?.data?.detail ||
                e?.response?.data?.message ||
                "No se pudo crear el usuario";
            toast.error(msg);
            throw e; // permite que el modal decida si cierra o no
        }
    };

    const handleDelete = async (user) => {
        const id = user?._id || user?.id;
        if (!id) return toast.error("No se encontró el ID del usuario");
        if (!confirm(`¿Eliminar al usuario "${user?.email || user?.nombre || id}"?`)) return;

        try {
            await deleteUser(id);
            toast.success("Usuario eliminado");
            setUsers((prev) => prev.filter((u) => (u._id || u.id) !== id));
        } catch (e) {
            console.error(e);
            toast.error("No se pudo eliminar el usuario");
        }
    };

    return (
        <div className="p-6 space-y-4">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <IconTooltip label="Gestión de usuarios del sistema" side="top">
                        <UsersIcon className="w-6 h-6 text-gray-700" aria-hidden="true" />
                    </IconTooltip>
                    <h1 className="text-2xl font-bold">Gestión de Usuarios</h1>
                </div>

                <div className="flex items-center gap-2">
                    <RefreshButton
                        onClick={loadUsers}
                        loading={loading}
                        label="Recargar"
                        tooltipLabel="Recargar lista de usuarios"
                        variant="outline"
                    />
                    {canCreate && <UserModal onSubmit={handleCreate} />}
                </div>
            </div>

            <div className="rounded-md border bg-white overflow-x-auto">
                <table className="min-w-full text-sm">
                    <thead className="bg-gray-100">
                        <tr>
                            <th className="px-4 py-2 text-left">Nombre</th>
                            <th className="px-4 py-2 text-left">Email</th>
                            <th className="px-4 py-2 text-left">Rol</th>
                            <th className="px-4 py-2 text-left w-28">Acciones</th>
                        </tr>
                    </thead>

                    <tbody className="divide-y">
                        {loading && (
                            <tr>
                                <td colSpan={4} className="px-4 py-6 text-gray-600">
                                    Cargando…
                                </td>
                            </tr>
                        )}

                        {!loading && users.length === 0 && (
                            <tr>
                                <td colSpan={4} className="px-4 py-6 text-gray-500">
                                    No hay usuarios registrados.
                                </td>
                            </tr>
                        )}

                        {!loading &&
                            users.map((u) => {
                                const key = u._id || u.id;
                                const nombre = u.nombre || u.name || "—";
                                const email = u.email || "—";
                                const rol = (u.rol || u.role || "usuario").toLowerCase();

                                return (
                                    <tr key={key} className="hover:bg-gray-50">
                                        <td className="px-4 py-2">{nombre}</td>
                                        <td className="px-4 py-2">{email}</td>
                                        <td className="px-4 py-2">
                                            <Badge type="role" value={rol} />
                                        </td>
                                        <td className="px-4 py-2">
                                            <div className="flex items-center gap-2">
                                                <IconTooltip label="Eliminar usuario" side="top">
                                                    <button
                                                        type="button"
                                                        onClick={() => handleDelete(u)}
                                                        className="p-1.5 rounded hover:bg-red-50 text-red-600 hover:text-red-800 focus:outline-none focus:ring-2 focus:ring-red-300"
                                                        aria-label={`Eliminar ${email}`}
                                                    >
                                                        <Trash2 className="w-5 h-5" />
                                                    </button>
                                                </IconTooltip>
                                            </div>
                                        </td>
                                    </tr>
                                );
                            })}
                    </tbody>
                </table>
            </div>

            <div className="flex items-center gap-2 text-xs text-gray-500">
                <AlertCircle className="w-4 h-4" />
                Consejo: Puedes añadir edición inline o por modal más adelante (actualización de rol/contraseña).
            </div>
        </div>
    );
}