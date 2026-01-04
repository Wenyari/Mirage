import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  addKey,
  batchAddKeys,
  createModel,
  deleteKey,
  deleteModel,
  getKeys,
  getKeyStats,
  getModels,
  healthCheck,
  triggerCooldown,
  updateKey,
  updateModel,
} from '@/services/admin/keys';
import type {
  AddKeyRequest,
  BatchAddKeysRequest,
  CooldownRequest,
  CreateModelRequest,
  ModelType,
  UpdateKeyRequest,
  UpdateModelRequest,
} from '@/types/key';

/**
 * 获取模型列表
 */
export function useModels() {
  return useQuery({
    queryKey: ['admin', 'models'],
    queryFn: getModels,
    staleTime: 1000 * 60 * 30, // 30分钟内不重新请求
  });
}

/**
 * 获取密钥列表
 * 支持自动刷新（5秒轮询）
 */
export function useKeys(model?: ModelType) {
  return useQuery({
    queryKey: ['admin', 'keys', model],
    queryFn: () => getKeys(model),
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
    mutationFn: (model?: ModelType) => healthCheck(model),
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
 * 创建模型
 */
export function useCreateModel() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateModelRequest) => createModel(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'models'] });
      // 刷新可用模型列表，这样模型配置页面会看到新模型
      queryClient.invalidateQueries({ queryKey: ['admin', 'available-models'] });
    },
  });
}

/**
 * 更新模型
 */
export function useUpdateModel() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ key, data }: { key: string; data: UpdateModelRequest }) =>
      updateModel(key, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'models'] });
      // 刷新可用模型列表
      queryClient.invalidateQueries({ queryKey: ['admin', 'available-models'] });
    },
  });
}

/**
 * 删除模型
 */
export function useDeleteModel() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (key: string) => deleteModel(key),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'models'] });
      // 刷新可用模型列表
      queryClient.invalidateQueries({ queryKey: ['admin', 'available-models'] });
    },
  });
}
