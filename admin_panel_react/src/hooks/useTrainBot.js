// src/hooks/useTrainBot.js
import { useMutation } from '@tanstack/react-query';
import axiosClient from '@/services/axiosClient';

export const useTrainBot = () => {
    return useMutation({
        mutationFn: async () => {
            const res = await axiosClient.post('/admin/train');
            return res.data;
        },
        onError: (error) => {
            console.error('❌ Error al entrenar el bot:', error?.response?.data || error.message);
        },
    });
};