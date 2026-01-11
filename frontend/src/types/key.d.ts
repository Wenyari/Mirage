/**
 * 密钥池管理类型定义
 * 基于 MySQL + Redis 双层架构
 */
/**
 * 密钥状态枚举
 */
export type KeyStatus = 0 | 1;
/**
 * 模型类型（改为 string 以支持动态扩展）
 */
export type ModelType = string;
/**
 * 模型信息
 */
export interface Model {
    key: string;
    name: string;
    enabled: boolean;
    description?: string;
    color?: string;
    icon?: string;
    icon_url?: string;
    max_concurrency_limit?: number;
    tags?: string[];
    created_at?: string;
    updated_at?: string;
}
/**
 * 创建模型请求参数
 */
export interface CreateModelRequest {
    key: string;
    name: string;
    enabled: boolean;
    description?: string;
    color?: string;
    icon_url?: string;
    max_concurrency_limit?: number;
    tags?: string[];
}
/**
 * 更新模型请求参数
 */
export interface UpdateModelRequest {
    name?: string;
    enabled?: boolean;
    description?: string;
    color?: string;
    icon_url?: string;
    max_concurrency_limit?: number;
    tags?: string[];
}
/**
 * 模型配置（包含模型标识和对应的 API Base）
 */
export interface ModelConfig {
    model: ModelType;
    api_base?: string;
}
/**
 * 密钥实体（完整信息）
 */
export interface Key {
    id: number;
    models: ModelType[];
    model_configs?: ModelConfig[];
    api_base: string;
    key_secret: string;
    max_concurrency: number;
    weight: number;
    status: KeyStatus;
    total_calls: number;
    total_errors: number;
    current_usage: number;
    is_cooling: boolean;
    cooling_until: string | null;
    last_used_at: string;
    created_at: string;
}
/**
 * 添加密钥请求参数
 */
export interface AddKeyRequest {
    models: ModelType[] | ModelConfig[];
    api_base?: string;
    key_secret: string;
    max_concurrency?: number;
    weight?: number;
}
/**
 * 批量添加密钥请求参数
 */
export interface BatchAddKeysRequest {
    models: ModelType[] | ModelConfig[];
    api_base?: string;
    keys: string[];
    max_concurrency?: number;
    weight?: number;
}
/**
 * 批量添加密钥响应
 */
export interface BatchAddKeysResponse {
    success: boolean;
    data: {
        success_count: number;
        failed_count: number;
        failed_keys: string[];
    };
}
/**
 * 更新密钥配置请求参数
 */
export interface UpdateKeyRequest {
    models?: ModelType[] | ModelConfig[];
    max_concurrency?: number;
    weight?: number;
    status?: KeyStatus;
}
/**
 * 熔断控制请求参数
 */
export interface CooldownRequest {
    action: 'trigger' | 'release';
    duration?: number;
}
/**
 * 熔断控制响应
 */
export interface CooldownResponse {
    success: boolean;
    data: {
        cooling_until?: string;
    };
}
/**
 * 健康检测响应（同步方式）
 */
export interface HealthCheckResponse {
    success: boolean;
    data: {
        total: number;
        active: number;
        cooling: number;
        disabled: number;
        details: Array<{
            id: number;
            model: ModelType;
            status: KeyStatus;
            is_cooling: boolean;
            check_result: 'ok' | 'error' | 'rate_limit';
        }>;
    };
}
/**
 * 密钥统计信息
 */
export interface KeyStats {
    by_model: Array<{
        model: ModelType;
        total_keys: number;
        active_keys: number;
        cooling_keys: number;
        total_concurrency: number;
        current_usage: number;
    }>;
    total_calls_today: number;
    total_errors_today: number;
    error_rate: number;
}
/**
 * 获取模型列表响应
 */
export interface GetModelsResponse {
    code: number;
    message: string;
    data: Model[];
}
/**
 * 脱敏密钥显示
 */
export declare function maskKey(key: string): string;
/**
 * 计算并发使用率
 */
export declare function getConcurrencyRate(current: number, max: number): number;
/**
 * 获取并发使用率颜色类
 */
export declare function getConcurrencyColorClass(rate: number): string;
