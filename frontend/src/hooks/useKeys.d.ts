import type { AddKeyRequest, BatchAddKeysRequest, CooldownRequest, CreateModelRequest, ModelType, UpdateKeyRequest, UpdateModelRequest } from '@/types/key';
/**
 * 获取模型列表
 */
export declare function useModels(): import("@tanstack/react-query").UseQueryResult<unknown, Error>;
/**
 * 获取密钥列表
 * 支持自动刷新（5秒轮询）
 */
export declare function useKeys(model?: ModelType): import("@tanstack/react-query").UseQueryResult<{
    code: number;
    message: string;
    data: import("@/types/key").Key[];
}, Error>;
/**
 * 添加密钥
 */
export declare function useAddKey(): import("@tanstack/react-query").UseMutationResult<{
    code: number;
    message: string;
    data: import("@/types/key").Key;
}, Error, AddKeyRequest, unknown>;
/**
 * 批量添加密钥
 */
export declare function useBatchAddKeys(): import("@tanstack/react-query").UseMutationResult<import("@/types/key").BatchAddKeysResponse, Error, BatchAddKeysRequest, unknown>;
/**
 * 更新密钥配置
 */
export declare function useUpdateKey(): import("@tanstack/react-query").UseMutationResult<{
    code: number;
    message: string;
    data: null;
}, Error, {
    id: number;
    data: UpdateKeyRequest;
}, unknown>;
/**
 * 删除密钥
 */
export declare function useDeleteKey(): import("@tanstack/react-query").UseMutationResult<{
    code: number;
    message: string;
    data: null;
}, Error, number, unknown>;
/**
 * 手动触发/解除熔断
 */
export declare function useTriggerCooldown(): import("@tanstack/react-query").UseMutationResult<import("@/types/key").CooldownResponse, Error, {
    id: number;
    data: CooldownRequest;
}, unknown>;
/**
 * 触发健康检测
 */
export declare function useHealthCheck(): import("@tanstack/react-query").UseMutationResult<import("@/types/key").HealthCheckResponse, Error, string | undefined, unknown>;
/**
 * 获取密钥统计信息
 */
export declare function useKeyStats(): import("@tanstack/react-query").UseQueryResult<{
    code: number;
    message: string;
    data: import("@/types/key").KeyStats;
}, Error>;
/**
 * 创建模型
 */
export declare function useCreateModel(): import("@tanstack/react-query").UseMutationResult<{
    code: number;
    message: string;
    data: import("@/types/key").Model;
}, Error, CreateModelRequest, unknown>;
/**
 * 更新模型
 */
export declare function useUpdateModel(): import("@tanstack/react-query").UseMutationResult<{
    code: number;
    message: string;
    data: import("@/types/key").Model;
}, Error, {
    key: string;
    data: UpdateModelRequest;
}, unknown>;
/**
 * 删除模型
 */
export declare function useDeleteModel(): import("@tanstack/react-query").UseMutationResult<{
    code: number;
    message: string;
    data: null;
}, Error, string, unknown>;
