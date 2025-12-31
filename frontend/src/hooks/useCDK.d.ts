import type { CDKGenerateRequest, CDKListParams, CDKVoidRequest } from '@/types/cdk';
/**
 * 获取 CDK 列表
 */
export declare function useCDKList(params: CDKListParams): import("@tanstack/react-query").UseQueryResult<import("@/types/cdk").CDKListResponse, Error>;
/**
 * 生成 CDK
 */
export declare function useGenerateCDK(): import("@tanstack/react-query").UseMutationResult<import("@/types/cdk").CDKGenerateResponse, Error, CDKGenerateRequest, unknown>;
/**
 * 作废 CDK
 */
export declare function useVoidCDK(): import("@tanstack/react-query").UseMutationResult<{
    success: boolean;
    message: string;
}, Error, CDKVoidRequest, unknown>;
/**
 * 获取批次列表
 */
export declare function useBatchList(): import("@tanstack/react-query").UseQueryResult<{
    success: boolean;
    data: string[];
}, Error>;
