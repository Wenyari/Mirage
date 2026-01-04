import api from '@/lib/api';
import type {
  ModelConfig,
  AvailableModel,
  CreateModelConfigRequest,
  UpdateModelConfigRequest,
  MembershipConfigs,
} from '@/types/modelConfig';

/**
 * 获取模型配置列表
 */
export async function getModelConfigs(): Promise<{ code: number; message: string; data: ModelConfig[] }> {
  return api.get('/admin/model-configs');
}

/**
 * 获取可配置的模型列表
 */
export async function getAvailableModels(): Promise<{ code: number; message: string; data: AvailableModel[] }> {
  return api.get('/admin/model-configs/available-models');
}

/**
 * 创建模型配置
 */
export async function createModelConfig(
  data: CreateModelConfigRequest
): Promise<{ code: number; message: string; data: ModelConfig }> {
  return api.post('/admin/model-configs', data);
}

/**
 * 更新模型配置
 */
export async function updateModelConfig(
  id: number,
  data: UpdateModelConfigRequest
): Promise<{ code: number; message: string; data: null }> {
  return api.patch(`/admin/model-configs/${id}`, data);
}

/**
 * 删除模型配置
 */
export async function deleteModelConfig(id: number): Promise<{ code: number; message: string; data: null }> {
  return api.delete(`/admin/model-configs/${id}`);
}

/**
 * 获取会员等级配置
 */
export async function getMembershipConfigs(): Promise<{ code: number; message: string; data: MembershipConfigs }> {
  return api.get('/admin/config/membership');
}

/**
 * 更新会员等级配置
 */
export async function updateMembershipConfigs(
  data: MembershipConfigs
): Promise<{ code: number; message: string; data: null }> {
  return api.put('/admin/config/membership', data);
}
