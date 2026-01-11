/**
 * CDK 兑换码类型定义
 */
/**
 * CDK 类型枚举
 */
export type CDKType = 'once' | 'universal';
/**
 * CDK 状态枚举
 */
export type CDKStatus = 'unused' | 'used' | 'void';
/**
 * CDK 兑换码实体
 */
export interface CDK {
    id: number;
    code: string;
    value: number;
    points?: number;
    type: CDKType;
    batch_no: string;
    batch_name: string;
    status: CDKStatus;
    used_by: string | null;
    used_at: string | null;
    expire_at?: string | null;
    created_at: string;
}
/**
 * CDK 生成请求参数
 */
export interface CDKGenerateRequest {
    points: number;
    type: CDKType;
    count: number;
    batch_no?: string;
    expire_at?: string;
    grant_level?: number;
}
/**
 * CDK 生成响应
 */
export interface CDKGenerateResponse {
    code: number;
    message: string;
    data: {
        batch_no: string;
        cdks: CDK[];
    };
}
/**
 * CDK 列表查询参数
 */
export interface CDKListParams {
    page?: number;
    page_size?: number;
    type?: CDKType;
    status?: CDKStatus;
    batch_no?: string;
    search?: string;
}
/**
 * CDK 列表响应
 */
export interface CDKListResponse {
    code: number;
    message: string;
    data: {
        items: CDK[];
        total: number;
        page: number;
        limit: number;
    };
}
/**
 * 作废 CDK 请求参数
 */
export interface CDKVoidRequest {
    batch_no?: string;
    ids?: number[];
}
/**
 * CDK 状态显示文本映射
 */
export declare const CDK_STATUS_MAP: Record<CDKStatus, string>;
/**
 * CDK 类型显示文本映射
 */
export declare const CDK_TYPE_MAP: Record<CDKType, string>;
