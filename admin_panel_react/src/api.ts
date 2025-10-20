import axios, { AxiosInstance, AxiosResponse } from "axios";

// ----------------------
// Tipos de datos
// ----------------------
export interface Intent {
    id: number;
    name: string;
    description?: string;
    createdAt?: string;
    updatedAt?: string;
}

export interface PagedIntents {
    intents: Intent[];
    total: number;
}

export interface CreateIntentPayload {
    name: string;
    description?: string;
}

export interface UpdateIntentPayload {
    name?: string;
    description?: string;
}

// ----------------------
// Configuración de Axios
// ----------------------
const api: AxiosInstance = axios.create({
    baseURL: "http://localhost:5000/api", // <- Ajusta según tu backend
    headers: {
        "Content-Type": "application/json",
    },
});

// ----------------------
// Funciones API
// ----------------------

// Listado paginado
export const fetchIntentsPaged = async (
    page: number,
    limit: number
): Promise<PagedIntents> => {
    const response: AxiosResponse<PagedIntents> = await api.get(
        `/intents?page=${page}&limit=${limit}`
    );
    return response.data;
};

// Obtener por ID
export const fetchIntentById = async (id: number): Promise<Intent> => {
    const response: AxiosResponse<Intent> = await api.get(`/intents/${id}`);
    return response.data;
};

// Crear
export const createIntent = async (
    intentData: CreateIntentPayload
): Promise<Intent> => {
    const response: AxiosResponse<Intent> = await api.post(
        "/intents",
        intentData
    );
    return response.data;
};

// Actualizar
export const updateIntent = async (
    id: number,
    intentData: UpdateIntentPayload
): Promise<Intent> => {
    const response: AxiosResponse<Intent> = await api.put(
        `/intents/${id}`,
        intentData
    );
    return response.data;
};

// Eliminar
export const deleteIntent = async (id: number): Promise<{ message: string }> => {
    const response: AxiosResponse<{ message: string }> = await api.delete(
        `/intents/${id}`
    );
    return response.data;
};

// Export principal
export default api;