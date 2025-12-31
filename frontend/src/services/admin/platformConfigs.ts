import api from '@/lib/api';
import type {
  PlatformConfig,
  AvailablePlatform,
  CreatePlatformConfigRequest,
  UpdatePlatformConfigRequest,
  MembershipConfigs,
} from '@/types/platformConfig';

/**
 * 获取平台配置列表
 */
export async function getPlatformConfigs(): Promise<{ code: number; message: string; data: PlatformConfig[] }> {
  return api.get('/admin/platform-configs');
}

/**
 * 获取可配置的平台列表
 */
export async function getAvailablePlatforms(): Promise<{ code: number; message: string; data: AvailablePlatform[] }> {
  return api.get('/admin/platform-configs/available-platforms');
}

/**
 * 创建平台配置
 */
export async function createPlatformConfig(
  data: CreatePlatformConfigRequest
): Promise<{ code: number; message: string; data: PlatformConfig }> {
  return api.post('/admin/platform-configs', data);
}

/**
 * 更新平台配置
 */
export async function updatePlatformConfig(
  id: number,
  data: UpdatePlatformConfigRequest
): Promise<{ code: number; message: string; data: null }> {
  return api.patch(`/admin/platform-configs/${id}`, data);
}

/**
 * 删除平台配置
 */
export async function deletePlatformConfig(id: number): Promise<{ code: number; message: string; data: null }> {
  return api.delete(`/admin/platform-configs/${id}`);
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
