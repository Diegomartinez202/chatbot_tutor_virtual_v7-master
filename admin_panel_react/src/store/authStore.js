// src/store/authStore.js
import { create } from "zustand";
export const useAuthStore = create((set) => ({
    accessToken: null,
    setAccessToken: (t) => set({ accessToken: t }),
}));
export const useAuthStore = create((set, get) => ({
    accessToken: null,
    setAccessToken: (t) => set({ accessToken: t }),
    getAccessToken: () => get().accessToken,
}));