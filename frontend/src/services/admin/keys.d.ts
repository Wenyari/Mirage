import type { AddKeyRequest, BatchAddKeysRequest, BatchAddKeysResponse, CooldownRequest, CooldownResponse, CreateModelRequest, GetModelsResponse, HealthCheckResponse, Key, KeyStats, Model, ModelType, UpdateKeyRequest, UpdateModelRequest } from '@/types/key';
/**
 * 获取模型列表
 */
export declare function getModels(tags?: string[]): Promise<GetModelsResponse>;
/**
 * 获取密钥列表
 */
export declare function getKeys(models?: ModelType[] | string): Promise<{
    code: number;
    message: string;
    data: Key[];
}>;
/**
 * 添加密钥
 */
export declare function addKey(data: AddKeyRequest): Promise<{
    code: number;
    message: string;
    data: Key;
}>;
/**
 * 批量添加密钥
 */
export declare function batchAddKeys(data: BatchAddKeysRequest): Promise<BatchAddKeysResponse>;
/**
 * 更新密钥配置
 */
export declare function updateKey(id: number, data: UpdateKeyRequest): Promise<{
    code: number;
    message: string;
    data: null;
}>;
/**
 * 删除密钥
 */
export declare function deleteKey(id: number): Promise<{
    code: number;
    message: string;
    data: null;
}>;
/**
 * 手动触发/解除熔断
 */
export declare function triggerCooldown(id: number, data: CooldownRequest): Promise<CooldownResponse>;
/**
 * 触发健康检测
 */
export declare function healthCheck(models?: ModelType[] | string): Promise<HealthCheckResponse>;
/**
 * 获取密钥统计信息
 */
export declare function getKeyStats(): Promise<{
    code: number;
    message: string;
    data: KeyStats;
}>;
/**
 * 创建模型
 */
export declare function createModel(data: CreateModelRequest): Promise<{
    code: number;
    message: string;
    data: Model;
}>;
/**
 * 更新模型
 */
export declare function updateModel(key: string, data: UpdateModelRequest): Promise<{
    code: number;
    message: string;
    data: Model;
}>;
/**
 * 删除模型
 */
export declare function deleteModel(key: string): Promise<{
    code: number;
    message: string;
    data: null;
}>;
