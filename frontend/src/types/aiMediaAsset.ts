/**
 * AI媒体资产类型定义
 */

// AI媒体资产
export interface AiMediaAsset {
    id: number;
    source_id: string;
    title: string;
    media_type: 'image' | 'video';
    prompt_en: string | null;
    prompt_zh: string | null;
    width: number;
    height: number;
    aspect_ratio: number;
    r2_key: string[] | null;
    r2_url: string[] | null;
    cover_r2_key: string | null;
    cover_r2_url: string | null;
    created_at: string;
    updated_at: string;
}

// 列表查询参数
export interface GetAssetsParams {
    page?: number;
    page_size?: number;
    media_type?: 'image' | 'video';
    keyword?: string;
}

// 列表查询响应
export interface GetAssetsResponse {
    code: number;
    message: string;
    data: {
        items: AiMediaAsset[];
        total: number;
        page: number;
        page_size: number;
        total_pages: number;
    };
}

// 创建资产请求
export interface CreateAssetRequest {
    title: string;
    media_type?: 'image' | 'video';
    prompt_en?: string;
    prompt_zh?: string;
    width?: number;
    height?: number;
    r2_key?: string[];
    r2_url?: string[];
    cover_r2_key?: string;
    cover_r2_url?: string;
}

// 更新资产请求
export interface UpdateAssetRequest extends Partial<CreateAssetRequest> { }

// 批量删除请求
export interface BatchDeleteRequest {
    ids: number[];
}

// 批量删除响应
export interface BatchDeleteResponse {
    code: number;
    message: string;
    data: {
        success_count: number;
        failed_count: number;
        deleted_files: {
            total: number;
            deleted: number;
            failed: number;
        };
    };
}

// 通用API响应
export interface ApiResponse<T> {
    code: number;
    message: string;
    data: T;
}
