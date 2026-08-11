import axios from 'axios';

// Toutes les requetes passent par /api/auth/*, proxifie vers auth-service
// (via Nginx Proxy Manager en production, via le proxy Vite en developpement
// -- voir vite.config.ts).
const apiClient = axios.create({
  baseURL: '/api/auth',
  timeout: 10_000,
});

export interface CorporateLoginPayload {
  username: string;
  password: string;
  auth_provider: 'ldap' | 'azure_ad';
  mac_address?: string | null;
}

export interface RequestOtpPayload {
  phone_number: string;
  mac_address?: string | null;
}

export interface VerifyOtpPayload {
  phone_number: string;
  code: string;
  mac_address?: string | null;
}

export interface RoomLoginPayload {
  room_number: string;
  access_code: string;
  mac_address?: string | null;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  display_name?: string;
}

export async function loginCorporate(payload: CorporateLoginPayload): Promise<AuthResponse> {
  const { data } = await apiClient.post<AuthResponse>('/corporate', payload);
  return data;
}

export async function requestOtp(payload: RequestOtpPayload): Promise<void> {
  await apiClient.post('/visitor/request-otp', payload);
}

export async function verifyOtp(payload: VerifyOtpPayload): Promise<AuthResponse> {
  const { data } = await apiClient.post<AuthResponse>('/visitor/verify-otp', payload);
  return data;
}

export async function loginRoom(payload: RoomLoginPayload): Promise<AuthResponse> {
  const { data } = await apiClient.post<AuthResponse>('/visitor/room', payload);
  return data;
}

// Extrait un message d'erreur lisible depuis une reponse Axios, sans exposer
// de details techniques internes a l'utilisateur final.
export function extractErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') return detail;
  }
  return fallback;
}
