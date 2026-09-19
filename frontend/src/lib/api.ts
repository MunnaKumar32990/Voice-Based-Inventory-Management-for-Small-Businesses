import axios from 'axios';
import { useAuthStore } from '../stores/authStore';

function resolveBaseURL(): string {
  const raw = (import.meta.env.VITE_API_URL as string | undefined) || 'http://localhost:8000';
  const trimmed = raw.replace(/\/+$/, '');
  // Allow VITE_API_URL to be either the host (http://localhost:8000)
  // or already include the version prefix (/api/v1).
  if (trimmed.endsWith('/api/v1')) return trimmed;
  if (trimmed.endsWith('/api')) return `${trimmed}/v1`;
  return `${trimmed}/api/v1`;
}

export const api = axios.create({
  baseURL: resolveBaseURL(),
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const url: string = error.config?.url || '';
    const isAuthRequest = url.includes('/auth/demo-login') || url.includes('/auth/token') || url.includes('/auth/login') || url.includes('/auth/signup');
    // Don't logout for the login request itself — that would mask login errors
    // and create a logout loop. Only logout on authenticated calls.
    if (status === 401 && !isAuthRequest) {
      useAuthStore.getState().logout();
      if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);
