import type { UpdateProfileRequest, UserListParams, UserListResponse } from '@/types/user';
/**
 * 获取用户列表
 */
export declare function getUsers(params: UserListParams): Promise<UserListResponse>;
/**
 * 更新用户余额（人工充值/扣费）
 */
export declare function updateUserBalance(userId: number, amount: number, reason: string): Promise<{
    new_balance: number;
}>;
/**
 * 修改用户资料（等级、状态等）
 */
export declare function updateUserProfile(userId: number, profile: UpdateProfileRequest): Promise<void>;
/**
 * 批量更新用户状态
 */
export declare function batchUpdateUserStatus(userIds: number[], status: 0 | 1): Promise<void>;
/**
 * 导出用户数据
 */
export declare function exportUsers(params: UserListParams): Promise<Blob>;
