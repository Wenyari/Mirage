import api from '@/lib/api';
import { AuthUser } from '@/store/authStore';

// Request Types
export interface SendCodeRequest {
  email: string;
}

export interface RegisterRequest {
  email: string;
  code: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

// Response Types
export interface RegisterResponse {
  user_id: number;
}

export interface LoginResponse {
  token: string;
  user: AuthUser;
}

export interface MeResponse extends AuthUser {
  vip_desc?: string;
}

export const authService = {
  // 1. 发送邮箱验证码
  sendCode: async (data: SendCodeRequest) => {
    return api.post<void>('/auth/code', data);
  },

  // 2. 用户注册
  register: async (data: RegisterRequest) => {
    return api.post<RegisterResponse>('/auth/register', data);
  },

  // 3. 用户登录
  login: async (data: LoginRequest) => {
    return api.post<LoginResponse>('/auth/login', data);
  },

  // 4. 获取当前用户信息
  me: async () => {
    return api.get<MeResponse>('/auth/me');
  },

  // 5. 用户登出
  logout: async () => {
    return api.post<void>('/auth/logout');
  },
};
