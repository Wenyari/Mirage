import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import { getUsers, updateUserBalance, updateUserProfile } from '@/services/admin/users';
import type { UpdateProfileRequest, UserListParams } from '@/types/user';

/**
 * 获取用户列表
 */
export function useUsers(params: UserListParams) {
  return useQuery({
    queryKey: ['admin', 'users', params],
    queryFn: () => getUsers(params),
    staleTime: 1000 * 30, // 30秒缓存
  });
}

/**
 * 更新用户余额
 */
export function useUpdateBalance() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, amount, reason, balance_type }: {
      userId: number;
      amount: number;
      reason: string;
      balance_type?: 'recharge' | 'activity';
    }) => updateUserBalance(userId, amount, reason, balance_type),

    onSuccess: (data, variables) => {
      // 刷新用户列表
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });

      const action = variables.amount > 0 ? '充值' : '扣费';
      toast.success(`用户${action}成功`, {
        description: `新余额: ${data.new_balance}`,
      });
    },

    onError: (error: any) => {
      toast.error('操作失败', {
        description: error.response?.data?.message || '请稍后重试',
      });
    },
  });
}

/**
 * 更新用户资料
 */
export function useUpdateProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, profile }: {
      userId: number;
      profile: UpdateProfileRequest;
    }) => updateUserProfile(userId, profile),

    onSuccess: () => {
      // 刷新用户列表
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      toast.success('用户资料更新成功');
    },

    onError: (error: any) => {
      toast.error('更新失败', {
        description: error.response?.data?.message || '请稍后重试',
      });
    },
  });
}