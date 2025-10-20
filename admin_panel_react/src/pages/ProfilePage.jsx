// src/pages/ProfilePage.jsx
import React, { useEffect, useState } from "react";
import axios from "@/services/api";
import { UserCircle } from "lucide-react";
import IconTooltip from "@/components/ui/IconTooltip";
import Badge from "@/components/Badge";

function ProfilePage() {
    const [profile, setProfile] = useState(null);

    useEffect(() => {
        axios.get("/auth/me").then((res) => setProfile(res.data));
    }, []);

    const roleValue = profile?.role || profile?.rol;

    return (
        <div className="p-6">
            <div className="flex items-center gap-2 mb-4">
                <IconTooltip label="Mi Perfil" side="top">
                    <UserCircle className="w-6 h-6 text-gray-700" />
                </IconTooltip>
                <h1 className="text-2xl font-bold">Mi Perfil</h1>
            </div>

            {!profile ? (
                <p>Cargando...</p>
            ) : (
                <div className="space-y-2">
                    <p>
                        <strong>Email:</strong> {profile.email}
                    </p>
                    <p>
                        <strong>ID de usuario:</strong> {profile.user_id}
                    </p>
                    <p className="flex items-center gap-2">
                        <strong>Rol:</strong> <Badge type="role" value={roleValue} />
                    </p>
                </div>
            )}
        </div>
    );
}

export default ProfilePage;
