import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type {
  Platform,
  AddKeyRequest,
  BatchAddKeysRequest,
  UpdateKeyRequest,
  CooldownRequest,
  CreatePlatformRequest,
  UpdatePlatformRequest,
} from '@/types/key';
import {
  getPlatforms,
  getKeys,
  addKey,
  batchAddKeys,
  updateKey,
  deleteKey,
  triggerCooldown,
  healthCheck,
  getKeyStats,
  createPlatform,
  updatePlatform,
  deletePlatform,
} from '@/services/admin/keys';

/**
 * 获取平台配置列表
 */
export function usePlatforms() {
  return useQuery({
    queryKey: ['admin', 'platforms'],
    queryFn: getPlatforms,
    staleTime: 1000 * 60 * 30, // 30分钟内不重新请求（平台配置变化不频繁）
  });
}

/**
 * 获取密钥列表
 * 支持自动刷新（5秒轮询）
 */
export function useKeys(platform?: Platform) {
  return useQuery({
    queryKey: ['admin', 'keys', platform],
    queryFn: () => getKeys(platform),
    refetchInterval: 5000,              // 5秒自动刷新
    refetchOnWindowFocus: true,         // 窗口聚焦时刷新
    refetchIntervalInBackground: false, // 后台不刷新
  });
}

/**
 * 添加密钥
 */
export function useAddKey() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: AddKeyRequest) => addKey(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'keys'] });
    },
  });
}

/**
 * 批量添加密钥
 */
export function useBatchAddKeys() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: BatchAddKeysRequest) => batchAddKeys(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'keys'] });
    },
  });
}

/**
 * 更新密钥配置
 */
export function useUpdateKey() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateKeyRequest }) => updateKey(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'keys'] });
    },
  });
}

/**
 * 删除密钥
 */
export function useDeleteKey() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => deleteKey(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'keys'] });
    },
  });
}

/**
 * 手动触发/解除熔断
 */
export function useTriggerCooldown() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: CooldownRequest }) => triggerCooldown(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'keys'] });
    },
  });
}

/**
 * 触发健康检测
 */
export function useHealthCheck() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (platform?: Platform) => healthCheck(platform),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'keys'] });
    },
  });
}

/**
 * 获取密钥统计信息
 */
export function useKeyStats() {
  return useQuery({
    queryKey: ['admin', 'keys', 'stats'],
    queryFn: getKeyStats,
    refetchInterval: 10000, // 10秒刷新一次统计数据
  });
}

/**
 * 创建平台
 */
export function useCreatePlatform() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreatePlatformRequest) => createPlatform(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'platforms'] });
      // 刷新可用平台列表，这样模型配置页面会看到新平台
      queryClient.invalidateQueries({ queryKey: ['admin', 'available-platforms'] });
    },
  });
}

/**
 * 更新平台
 */
export function useUpdatePlatform() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ key, data }: { key: string; data: UpdatePlatformRequest }) =>
      updatePlatform(key, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'platforms'] });
      // 刷新可用平台列表
      queryClient.invalidateQueries({ queryKey: ['admin', 'available-platforms'] });
    },
  });
}

/**
 * 删除平台
 */
export function useDeletePlatform() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (key: string) => deletePlatform(key),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'platforms'] });
      // 刷新可用平台列表
      queryClient.invalidateQueries({ queryKey: ['admin', 'available-platforms'] });
    },
  });
}
