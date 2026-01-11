import api from '@/lib/api';
import type { ApiResponse } from '@/types/api';
import type { User } from '@/types/user';

export interface UpdateUserInfoRequest {
  name?: string;
  current_password?: string;
  new_password?: string;
}

export const userService = {
  // 获取用户信息
  getUserInfo: async () => {
    const response = await api.get<ApiResponse<User>>('/users/me');
    return response.data;
  },

  // 更新用户信息
  updateUserInfo: async (data: UpdateUserInfoRequest) => {
    const response = await api.patch<ApiResponse<User>>('/users/me', data);
    return response.data;
  },
};
