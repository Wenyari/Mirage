import api from '@/lib/api';
import type { ApiResponse } from '@/types';
import { User } from '@/types/user';

export interface LoginParams {
  email: string;
  password?: string;
  code?: string; // 验证码等
}

export interface LoginResponse {
  token: string;
  user: Omit<User, 'password_hash' | 'register_ip'>;
}

export async function login(params: LoginParams): Promise<LoginResponse> {
  const response = await api.post<ApiResponse<LoginResponse>>('/auth/login', params);
  return response.data as any;
}

export async function logout(): Promise<void> {
  await api.post<ApiResponse<null>>('/auth/logout');
}
