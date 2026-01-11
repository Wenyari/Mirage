import type { CDKGenerateRequest, CDKGenerateResponse, CDKListParams, CDKListResponse, CDKVoidRequest } from '@/types/cdk';
/**
 * 生成 CDK
 */
export declare function generateCDK(data: CDKGenerateRequest): Promise<CDKGenerateResponse>;
/**
 * 获取 CDK 列表
 */
export declare function getCDKList(params?: CDKListParams): Promise<CDKListResponse['data']>;
/**
 * 作废 CDK
 */
export declare function voidCDK(data: CDKVoidRequest): Promise<{
    success: boolean;
    message: string;
}>;
/**
 * 获取批次列表
 */
export declare function getBatchList(): Promise<{
    success: boolean;
    data: string[];
}>;
