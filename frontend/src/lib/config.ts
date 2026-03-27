export const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000/api/v1";
export const FRONTEND_ENV = import.meta.env.MODE;

const rawBaseUrl = import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL;

export const API_BASE_URL = rawBaseUrl.replace(/\/+$/, "");
