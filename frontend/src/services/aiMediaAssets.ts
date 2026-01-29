/**
 * AI媒体资产API服务
 */
import api from '@/lib/api';
import type {
    AiMediaAsset,
    ApiResponse,
    BatchDeleteRequest,
    BatchDeleteResponse,
    CreateAssetRequest,
    GetAssetsParams,
    GetAssetsResponse,
    UpdateAssetRequest,
} from '@/types/aiMediaAsset';

/**
 * 获取资产列表(公开访问)
 */
export async function getAssets(params?: GetAssetsParams): Promise<GetAssetsResponse> {
    return api.get('/admin/ai-media-assets', { params });
}

/**
 * 获取单个资产详情(管理员)
 */
export async function getAssetById(id: number): Promise<ApiResponse<AiMediaAsset>> {
    return api.get(`/admin/ai-media-assets/${id}`);
}

/**
 * 创建资产(管理员)
 */
export async function createAsset(data: CreateAssetRequest): Promise<ApiResponse<AiMediaAsset>> {
    return api.post('/admin/ai-media-assets', data);
}

/**
 * 更新资产(管理员)
 */
export async function updateAsset(
    id: number,
    data: UpdateAssetRequest
): Promise<ApiResponse<null>> {
    return api.patch(`/admin/ai-media-assets/${id}`, data);
}

/**
 * 删除资产(管理员)
 */
export async function deleteAsset(id: number): Promise<ApiResponse<null>> {
    return api.delete(`/admin/ai-media-assets/${id}`);
}

/**
 * 批量删除资产(管理员)
 */
export async function batchDeleteAssets(data: BatchDeleteRequest): Promise<BatchDeleteResponse> {
    return api.post('/admin/ai-media-assets/batch-delete', data);
}
