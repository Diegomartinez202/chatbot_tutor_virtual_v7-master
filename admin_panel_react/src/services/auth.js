// src/services/auth.js
import { http } from "@/lib/http";

export async function getMe() {
    const { data } = await http.get("/auth/me");
    return data;
}

export async function logout() {
    await http.post("/auth/logout");
}
