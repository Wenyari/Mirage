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
  const payload = {
    amount: data.points, // 后端字段名为 amount
    count: data.count,
    type: data.type,
    batch_name: data.batch_no || undefined, // 后端字段名为 batch_name
    grant_level: data.grant_level,
    expire_at: data.expire_at || undefined, // 新增过期时间
  };
  return api.post('/admin/cdk/generate', payload);
}

/**
 * 获取 CDK 列表
 */
export async function getCDKList(params: CDKListParams = {}): Promise<CDKListResponse['data']> {
  const queryParams: any = {
    ...params,
    limit: params.page_size, // 映射 page_size 到 limit
  };
  delete queryParams.page_size;

  const res: any = await api.get('/admin/cdk', { params: queryParams });
  return res.data;
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
