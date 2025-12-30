import api from '@/lib/api';
import type { 
  UpdateBalanceRequest, 
  UpdateProfileRequest, 
  User, 
  UserListParams, 
  UserListResponse} from '@/types/user';

/**
 * 获取用户列表
 */
export async function getUsers(params: UserListParams): Promise<UserListResponse> {
  const response = await api.get('/admin/users', { params });
  return response.data;
}

/**
 * 更新用户余额（人工充值/扣费）
 */
export async function updateUserBalance(
  userId: number, 
  amount: number, 
  reason: string
): Promise<{ new_balance: number }> {
  const data: UpdateBalanceRequest = { amount, reason };
  const response = await api.patch(`/admin/users/${userId}/balance`, data);
  return response.data;
}

/**
 * 修改用户资料（等级、状态等）
 */
export async function updateUserProfile(
  userId: number, 
  profile: UpdateProfileRequest
): Promise<void> {
  await api.patch(`/admin/users/${userId}/profile`, profile);
}

/**
 * 批量更新用户状态
 */
export async function batchUpdateUserStatus(
  userIds: number[], 
  status: 0 | 1
): Promise<void> {
  // 这里假设后端支持批量操作，如果不支持可以循环调用单个更新
  for (const userId of userIds) {
    await updateUserProfile(userId, { status });
  }
}

/**
 * 导出用户数据
 */
export async function exportUsers(params: UserListParams): Promise<Blob> {
  const response = await api.get('/admin/users/export', { 
    params,
    responseType: 'blob'
  });
  return response.data;
}