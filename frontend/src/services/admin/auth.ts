import api from '@/lib/api';
import type { ApiResponse } from '@/types';

export interface LoginParams {
  email: string;
  password?: string;
  code?: string; // 验证码等
}

export interface LoginResponse {
  token: string;
  user: {
    id: number;
    email: string;
    role: string;
    [key: string]: any;
  };
}

export async function login(params: LoginParams): Promise<LoginResponse> {
  const response = await api.post<ApiResponse<LoginResponse>>('/auth/login', params);
  return response.data;
}
