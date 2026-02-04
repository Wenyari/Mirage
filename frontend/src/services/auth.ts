import api from '@/lib/api';
import { AuthUser } from '@/store/authStore';
import { ApiResponse } from '@/types/api';

// Request Types
export interface GeetestParams {
  lot_number: string;
  captcha_output: string;
  pass_token: string;
  gen_time: string;
}

export interface SendCodeRequest extends Partial<GeetestParams> {
  email: string;
  // cf_token: string; // Removed
}

export interface RegisterRequest {
  email: string;
  code: string;
  password: string;
}

export interface LoginRequest extends Partial<GeetestParams> {
  email: string;
  password: string;
  // cf_token: string; // Removed
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
    return api.post<ApiResponse<void>>('/auth/code', data);
  },

  // 2. 用户注册
  register: async (data: RegisterRequest) => {
    const response = await api.post<ApiResponse<RegisterResponse>>('/auth/register', data);
    return response.data;
  },

  // 3. 用户登录
  login: async (data: LoginRequest) => {
    const response = await api.post<ApiResponse<LoginResponse>>('/auth/login', data);
    return response.data;
  },

  // 4. 获取当前用户信息
  me: async () => {
    const response = await api.get<ApiResponse<MeResponse>>('/auth/me');
    // api interceptor may already return the whole server payload or the inner data;
    // normalize to return the actual user object.
    if (response && (response as any).data) {
      return (response as any).data;
    }
    return response;
  },

  // 5. 用户登出
  logout: async () => {
    return api.post<ApiResponse<void>>('/auth/logout');
  },

  // 6. 获取公开统计信息
  getPublicStats: async () => {
    const response = await api.get<ApiResponse<UserStats>>('/auth/stats/public');
    return response.data;
  },
};

export interface UserStats {
  online_count: number;
  level_distribution: Record<string, number>;
}
