// apiClient “oficial”: reusa tu axiosClient y exporta las formas esperadas
import axiosClient from "./axiosClient";

export const apiClient = axiosClient;

export default axiosClient;

export const api = axiosClient;

export * from "./axiosClient";
