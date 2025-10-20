import { useMutation } from '@tanstack/react-query'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL
const getAuthHeaders = () => ({
    Authorization: `Bearer ${localStorage.getItem('token')}`,
})

export const useAddIntent = () => {
    return useMutation({
        mutationFn: async (data) => {
            await axios.post(`${API_URL}/admin/intents`, data, {
                headers: getAuthHeaders(),
            })
        },
    })
}
