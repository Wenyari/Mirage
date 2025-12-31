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
  Platform,
  PlatformConfig,
  GetPlatformsResponse,
  CreatePlatformRequest,
  UpdatePlatformRequest,
} from '@/types/key';

/**
 * 获取平台配置列表
 */
export async function getPlatforms(): Promise<GetPlatformsResponse> {
  return api.get('/admin/platforms');
}

/**
 * 获取密钥列表
 */
export async function getKeys(platform?: Platform): Promise<{ code: number; message: string; data: Key[] }> {
  const params = platform && platform !== 'all' ? { platform } : {};
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
export async function healthCheck(platform?: Platform): Promise<HealthCheckResponse> {
  const params = platform && platform !== 'all' ? { platform } : {};
  return api.post('/admin/keys/health-check', {}, { params });
}

/**
 * 获取密钥统计信息
 */
export async function getKeyStats(): Promise<{ code: number; message: string; data: KeyStats }> {
  return api.get('/admin/keys/stats');
}

/**
 * 创建平台
 */
export async function createPlatform(
  data: CreatePlatformRequest
): Promise<{ code: number; message: string; data: PlatformConfig }> {
  return api.post('/admin/platforms', data);
}

/**
 * 更新平台
 */
export async function updatePlatform(
  key: string,
  data: UpdatePlatformRequest
): Promise<{ code: number; message: string; data: PlatformConfig }> {
  return api.patch(`/admin/platforms/${key}`, data);
}

/**
 * 删除平台
 */
export async function deletePlatform(key: string): Promise<{ code: number; message: string; data: null }> {
  return api.delete(`/admin/platforms/${key}`);
}
