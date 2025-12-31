import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { CreatePlatformConfigRequest, UpdatePlatformConfigRequest, MembershipConfigs } from '@/types/platformConfig';
import {
  getPlatformConfigs,
  getAvailablePlatforms,
  createPlatformConfig,
  updatePlatformConfig,
  deletePlatformConfig,
  getMembershipConfigs,
  updateMembershipConfigs,
} from '@/services/admin/platformConfigs';

/**
 * 获取平台配置列表
 */
export function usePlatformConfigs() {
  return useQuery({
    queryKey: ['admin', 'platform-configs'],
    queryFn: getPlatformConfigs,
  });
}

/**
 * 获取可配置的平台列表
 */
export function useAvailablePlatforms() {
  return useQuery({
    queryKey: ['admin', 'available-platforms'],
    queryFn: getAvailablePlatforms,
  });
}

/**
 * 创建平台配置
 */
export function useCreatePlatformConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreatePlatformConfigRequest) => createPlatformConfig(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'platform-configs'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'available-platforms'] });
    },
  });
}

/**
 * 更新平台配置
 */
export function useUpdatePlatformConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdatePlatformConfigRequest }) =>
      updatePlatformConfig(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'platform-configs'] });
    },
  });
}

/**
 * 删除平台配置
 */
export function useDeletePlatformConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => deletePlatformConfig(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'platform-configs'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'available-platforms'] });
    },
  });
}

/**
 * 获取会员等级配置
 */
export function useMembershipConfigs() {
  return useQuery({
    queryKey: ['admin', 'membership-configs'],
    queryFn: getMembershipConfigs,
  });
}

/**
 * 更新会员等级配置
 */
export function useUpdateMembershipConfigs() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: MembershipConfigs) => updateMembershipConfigs(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'membership-configs'] });
    },
  });
}
