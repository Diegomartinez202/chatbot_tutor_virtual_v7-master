// src/components/UserRow.jsx
import { Edit, Trash2 } from "lucide-react";
import IconTooltip from "@/components/ui/IconTooltip";
import Badge from "@/components/Badge";

const ROLE_CLASS = {
    admin: "bg-purple-100 text-purple-800",
    soporte: "bg-blue-100 text-blue-800",
    usuario: "bg-gray-100 text-gray-800",
};

const UserRow = ({ user, onEdit, onDelete, renderRol }) => {
    const uid = user._id || user.id;
    const roleKey = (user.rol || "usuario").toLowerCase();

    return (
        <tr>
            <td className="p-2 border">{user.nombre}</td>
            <td className="p-2 border">{user.email}</td>

            {/* Badge visual para el rol si NO se pasa renderRol */}
            <td className="p-2 border capitalize">
                {renderRol ? (
                    renderRol()
                ) : (
                    // Preferimos el Badge tipado; si falla el estilo, ROLE_CLASS queda como respaldo visual.
                    <span className="inline-flex items-center gap-2">
                        <Badge type="role" value={roleKey} />
                        <span
                            className={[
                                "hidden sm:inline px-2 py-0.5 rounded-full text-xs",
                                ROLE_CLASS[roleKey] || ROLE_CLASS.usuario,
                            ].join(" ")}
                        >
                            {user.rol || "usuario"}
                        </span>
                    </span>
                )}
            </td>

            <td className="p-2 border">
                <div className="flex space-x-2">
                    <IconTooltip label="Editar usuario" side="top">
                        <button
                            type="button"
                            onClick={() => onEdit(user)}
                            className="p-1 rounded hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-300"
                            aria-label={`Editar usuario ${user.email || ""}`}
                        >
                            <Edit className="w-5 h-5 text-blue-600 hover:text-blue-800" />
                        </button>
                    </IconTooltip>

                    <IconTooltip label="Eliminar usuario" side="top">
                        <button
                            type="button"
                            onClick={() => onDelete(uid)}
                            className="p-1 rounded hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-300"
                            aria-label={`Eliminar usuario ${user.email || ""}`}
                        >
                            <Trash2 className="w-5 h-5 text-red-600 hover:text-red-800" />
                        </button>
                    </IconTooltip>
                </div>
            </td>
        </tr>
    );
};

export default UserRow;