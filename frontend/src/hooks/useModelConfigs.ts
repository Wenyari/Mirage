import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { CreateModelConfigRequest, UpdateModelConfigRequest, MembershipConfigs } from '@/types/modelConfig';
import {
  getModelConfigs,
  getAvailableModels,
  createModelConfig,
  updateModelConfig,
  deleteModelConfig,
  getMembershipConfigs,
  updateMembershipConfigs,
} from '@/services/admin/modelConfigs';

/**
 * 获取模型配置列表
 */
export function useModelConfigs() {
  return useQuery({
    queryKey: ['admin', 'model-configs'],
    queryFn: getModelConfigs,
  });
}

/**
 * 获取可配置的模型列表
 */
export function useAvailableModels() {
  return useQuery({
    queryKey: ['admin', 'available-models'],
    queryFn: getAvailableModels,
  });
}

/**
 * 创建模型配置
 */
export function useCreateModelConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateModelConfigRequest) => createModelConfig(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'model-configs'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'available-models'] });
    },
  });
}

/**
 * 更新模型配置
 */
export function useUpdateModelConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateModelConfigRequest }) =>
      updateModelConfig(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'model-configs'] });
    },
  });
}

/**
 * 删除模型配置
 */
export function useDeleteModelConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => deleteModelConfig(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'model-configs'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'available-models'] });
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
