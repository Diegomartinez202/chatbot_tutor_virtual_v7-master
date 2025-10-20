// src/pages/UsersPage.jsx
import { useEffect, useState } from "react";
import { getUsers, createUser, updateUser, deleteUser } from "@/services/api";
import UsersTable from "@/components/UsersTable";
import ExportUsersButton from "@/components/ExportUsersButton";
import AssignRoles from "@/components/AssignRoles";
import { toast } from "react-hot-toast";
import { Users as UsersIcon, Plus, Save } from "lucide-react";
import IconTooltip from "@/components/ui/IconTooltip";
import Badge from "@/components/Badge";

const UsersPage = () => {
    const [users, setUsers] = useState([]);
    const [editingUserId, setEditingUserId] = useState(null);
    const [formData, setFormData] = useState({ nombre: "", email: "", rol: "usuario" });
    const [newUser, setNewUser] = useState({ nombre: "", email: "", rol: "usuario", password: "" });

    const fetchUsers = async () => {
        try {
            const data = await getUsers();
            setUsers(Array.isArray(data) ? data : []);
        } catch (err) {
            toast.error("Error al cargar usuarios");
            setUsers([]);
        }
    };

    useEffect(() => {
        fetchUsers();
    }, []);

    const handleEdit = (user) => {
        setEditingUserId(user._id);
        setFormData({ nombre: user.nombre, email: user.email, rol: user.rol });
    };

    const handleCancel = () => {
        setEditingUserId(null);
        setFormData({ nombre: "", email: "", rol: "usuario" });
    };

    const handleUpdate = async () => {
        try {
            await updateUser(editingUserId, formData);
            toast.success("Usuario actualizado");
            handleCancel();
            fetchUsers();
        } catch (err) {
            toast.error("Error al actualizar usuario");
        }
    };

    const handleDelete = async (userId) => {
        if (!confirm("¿Estás seguro de eliminar este usuario?")) return;
        try {
            await deleteUser(userId);
            toast.success("Usuario eliminado");
            fetchUsers();
        } catch (err) {
            toast.error("Error al eliminar usuario");
        }
    };

    const handleCreate = async () => {
        if (!newUser.email || !newUser.password) {
            toast.error("Email y contraseña son obligatorios");
            return;
        }
        try {
            await createUser(newUser);
            toast.success("Usuario creado");
            setNewUser({ nombre: "", email: "", rol: "usuario", password: "" });
            fetchUsers();
        } catch (err) {
            toast.error("Error al crear usuario");
        }
    };

    return (
        <div className="p-6 max-w-6xl mx-auto">
            {/* Encabezado sin emojis, con lucide + tooltip */}
            <div className="flex items-center gap-2 mb-6">
                <IconTooltip label="Gestión de Usuarios" side="top">
                    <UsersIcon className="w-6 h-6 text-gray-700" aria-hidden="true" />
                </IconTooltip>
                <h1 className="text-2xl font-bold">Gestión de Usuarios</h1>
            </div>

            {/* Crear nuevo usuario (reemplazo de emojis por iconos) */}
            <div className="mb-6 p-4 border rounded bg-green-50">
                <div className="flex items-center gap-2 mb-2">
                    <IconTooltip label="Crear nuevo usuario" side="top">
                        <Plus className="w-4 h-4 text-green-700" />
                    </IconTooltip>
                    <h3 className="font-semibold">Crear Nuevo Usuario</h3>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                    <input
                        className="border px-2 py-1 rounded"
                        placeholder="Nombre"
                        value={newUser.nombre}
                        onChange={(e) => setNewUser({ ...newUser, nombre: e.target.value })}
                    />
                    <input
                        className="border px-2 py-1 rounded"
                        placeholder="Email"
                        type="email"
                        value={newUser.email}
                        onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                    />
                    <input
                        className="border px-2 py-1 rounded"
                        placeholder="Contraseña"
                        type="password"
                        value={newUser.password}
                        onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                    />
                    <select
                        className="border px-2 py-1 rounded"
                        value={newUser.rol}
                        onChange={(e) => setNewUser({ ...newUser, rol: e.target.value })}
                    >
                        <option value="admin">Admin</option>
                        <option value="soporte">Soporte</option>
                        <option value="usuario">Usuario</option>
                    </select>

                    <IconTooltip label="Crear usuario" side="top">
                        <button
                            onClick={handleCreate}
                            className="bg-green-600 text-white px-3 py-1 rounded inline-flex items-center gap-2"
                            type="button"
                        >
                            <Save className="w-4 h-4" />
                            Crear
                        </button>
                    </IconTooltip>
                </div>
            </div>

            {/* Exportar CSV */}
            <ExportUsersButton users={users} />

            {/* Tabla con paginación y edición inline */}
            <UsersTable
                users={users}
                editingUserId={editingUserId}
                formData={formData}
                setFormData={setFormData}
                onEdit={handleEdit}
                onCancel={handleCancel}
                onUpdate={handleUpdate}
                onDelete={handleDelete}
                Badge={Badge}
            />

            {/* Gestión de roles adicional */}
            <div className="mt-10">
                <AssignRoles />
            </div>
        </div>
    );
};

export default UsersPage;