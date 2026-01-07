import api from '@/lib/api';
import type {
  Key,
  AddKeyRequest,
  BatchAddKeysRequest,
  BatchAddKeysResponse,
  UpdateKeyRequest,
  CooldownRequest,
  CooldownResponse,
  HealthCheckResponse,
  KeyStats,
  ModelType,
  Model,
  GetModelsResponse,
  CreateModelRequest,
  UpdateModelRequest,
} from '@/types/key';

/**
 * 获取模型列表
 */
export async function getModels(): Promise<GetModelsResponse> {
  return api.get('/admin/models');
}

/**
 * 获取密钥列表
 */
export async function getKeys(models?: ModelType[] | string): Promise<{ code: number; message: string; data: Key[] }> {
  // 如果是数组，转为逗号分隔字符串
  let modelParam = models;
  if (Array.isArray(models)) {
    modelParam = models.join(',');
  }
  
  const params = modelParam && modelParam !== 'all' ? { models: modelParam } : {};
  return api.get('/admin/keys', { params });
}

/**
 * 添加密钥
 */
export async function addKey(data: AddKeyRequest): Promise<{ code: number; message: string; data: Key }> {
  return api.post('/admin/keys', data);
}

/**
 * 批量添加密钥
 */
export async function batchAddKeys(data: BatchAddKeysRequest): Promise<BatchAddKeysResponse> {
  return api.post('/admin/keys/batch', data);
}

/**
 * 更新密钥配置
 */
export async function updateKey(
  id: number,
  data: UpdateKeyRequest
): Promise<{ code: number; message: string; data: null }> {
  return api.patch(`/admin/keys/${id}`, data);
}

/**
 * 删除密钥
 */
export async function deleteKey(id: number): Promise<{ code: number; message: string; data: null }> {
  return api.delete(`/admin/keys/${id}`);
}

/**
 * 手动触发/解除熔断
 */
export async function triggerCooldown(id: number, data: CooldownRequest): Promise<CooldownResponse> {
  return api.post(`/admin/keys/${id}/cooldown`, data);
}

/**
 * 触发健康检测
 */
export async function healthCheck(models?: ModelType[] | string): Promise<HealthCheckResponse> {
  // 如果是数组，转为逗号分隔字符串
  let modelParam = models;
  if (Array.isArray(models)) {
    modelParam = models.join(',');
  }

  const params = modelParam && modelParam !== 'all' ? { models: modelParam } : {};
  return api.post('/admin/keys/health-check', {}, { params });
}

/**
 * 获取密钥统计信息
 */
export async function getKeyStats(): Promise<{ code: number; message: string; data: KeyStats }> {
  return api.get('/admin/keys/stats');
}

/**
 * 创建模型
 */
export async function createModel(
  data: CreateModelRequest
): Promise<{ code: number; message: string; data: Model }> {
  return api.post('/admin/models', data);
}

/**
 * 更新模型
 */
export async function updateModel(
  key: string,
  data: UpdateModelRequest
): Promise<{ code: number; message: string; data: Model }> {
  return api.patch(`/admin/models/${key}`, data);
}

/**
 * 删除模型
 */
export async function deleteModel(key: string): Promise<{ code: number; message: string; data: null }> {
  return api.delete(`/admin/models/${key}`);
}
