import api from '@/lib/api';
import type {
  CDKGenerateRequest,
  CDKGenerateResponse,
  CDKListParams,
  CDKListResponse,
  CDKVoidRequest,
} from '@/types/cdk';

/**
 * 生成 CDK
 */
export async function generateCDK(data: CDKGenerateRequest): Promise<CDKGenerateResponse> {
  return api.post('/admin/cdk/generate', data);
}

/**
 * 获取 CDK 列表
 */
export async function getCDKList(params: CDKListParams = {}): Promise<CDKListResponse> {
  return api.get('/admin/cdk', { params });
}

/**
 * 作废 CDK
 */
export async function voidCDK(data: CDKVoidRequest): Promise<{ success: boolean; message: string }> {
  return api.post('/admin/cdk/void', data);
}

/**
 * 获取批次列表
 */
export async function getBatchList(): Promise<{ success: boolean; data: string[] }> {
  return api.get('/admin/cdk/batches');
}
