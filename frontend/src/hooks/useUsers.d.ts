import type { UpdateProfileRequest, UserListParams } from '@/types/user';
/**
 * 获取用户列表
 */
export declare function useUsers(params: UserListParams): import("@tanstack/react-query").UseQueryResult<import("@/types/user").UserListResponse, Error>;
/**
 * 更新用户余额
 */
export declare function useUpdateBalance(): import("@tanstack/react-query").UseMutationResult<{
    new_balance: number;
}, any, {
    userId: number;
    amount: number;
    reason: string;
}, unknown>;
/**
 * 更新用户资料
 */
export declare function useUpdateProfile(): import("@tanstack/react-query").UseMutationResult<void, any, {
    userId: number;
    profile: UpdateProfileRequest;
}, unknown>;
