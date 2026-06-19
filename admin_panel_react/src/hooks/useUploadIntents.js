// src/hooks/useUploadIntents.js
import { useMutation } from '@tanstack/react-query';
import axiosClient from '@/services/axiosClient';

export const useUploadIntents = () => {
    return useMutation({
        mutationFn: async () => {
            const res = await axiosClient.post('/admin/upload');
            return res.data;
        },
        onError: (error) => {
            console.error('❌ Error al subir los intents:', error?.response?.data || error.message);
        },
    });
};