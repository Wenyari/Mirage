/**
 * 密钥池管理类型定义
 * 基于 MySQL + Redis 双层架构
 */

/**
 * 密钥状态枚举
 */
export type KeyStatus = 0 | 1; // 0=停用, 1=启用

/**
 * 模型类型（改为 string 以支持动态扩展）
 */
export type ModelType = string;

/**
 * 模型信息
 */
export interface Model {
  key: string;                   // 模型标识符（如 'gpt-4'）
  name: string;                  // 显示名称（如 'GPT-4'）
  enabled: boolean;              // 是否启用
  description?: string;          // 模型描述
  color?: string;                // 颜色标识（用于 Badge）
  icon?: string;                 // 图标 URL（可选）
  icon_url?: string;             // 图标 URL（与icon同义，数据库字段）
  max_concurrency_limit?: number; // 该模型建议的最大并发限制
  created_at?: string;           // 创建时间
  updated_at?: string;           // 更新时间
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
}

/**
 * 密钥实体（完整信息）
 */
export interface Key {
  id: number;
  model: ModelType;
  api_base: string;                // API 基础地址
  key_secret: string;              // 密钥（前端会脱敏显示）
  max_concurrency: number;         // 最大并发限制（核心配置）
  weight: number;                  // 权重（1-100，用于负载均衡）
  status: KeyStatus;               // 状态：1=启用，0=停用

  // 统计字段（MySQL 存储，定时从 Redis 同步）
  total_calls: number;             // 总调用次数
  total_errors: number;            // 总失败次数

  // 实时状态（从 Redis 读取）
  current_usage: number;           // 当前并发数（0 ~ max_concurrency）
  is_cooling: boolean;             // 是否在冷却期（熔断中）
  cooling_until: string | null;    // 冷却结束时间（ISO 8601）

  last_used_at: string;            // 最后使用时间
  created_at: string;              // 创建时间
}

/**
 * 添加密钥请求参数
 */
export interface AddKeyRequest {
  model: ModelType;
  api_base?: string;
  key_secret: string;
  max_concurrency?: number;        // 默认 3
  weight?: number;                 // 默认 10
}

/**
 * 批量添加密钥请求参数
 */
export interface BatchAddKeysRequest {
  model: ModelType;
  api_base?: string;               // 默认为官方地址
  keys: string[];                  // 密钥数组
  max_concurrency?: number;        // 统一的最大并发
  weight?: number;                 // 统一的权重
}

/**
 * 批量添加密钥响应
 */
export interface BatchAddKeysResponse {
  success: boolean;
  data: {
    success_count: number;
    failed_count: number;
    failed_keys: string[];         // 失败的密钥列表（脱敏）
  };
}

/**
 * 更新密钥配置请求参数
 */
export interface UpdateKeyRequest {
  max_concurrency?: number;
  weight?: number;
  status?: KeyStatus;
}

/**
 * 熔断控制请求参数
 */
export interface CooldownRequest {
  action: 'trigger' | 'release';   // trigger=触发熔断，release=解除熔断
  duration?: number;               // 冷却时长（秒），仅 trigger 时需要
}

/**
 * 熔断控制响应
 */
export interface CooldownResponse {
  success: boolean;
  data: {
    cooling_until?: string;        // 冷却结束时间
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
    total_concurrency: number;      // 所有 Key 的并发数总和
    current_usage: number;          // 当前实际使用的并发数
  }>;
  total_calls_today: number;
  total_errors_today: number;
  error_rate: number;               // 错误率（%）
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
export function maskKey(key: string): string {
  if (key.length <= 12) return key;
  return `${key.substring(0, 8)}****${key.substring(key.length - 4)}`;
}

/**
 * 计算并发使用率
 */
export function getConcurrencyRate(current: number, max: number): number {
  if (max === 0) return 0;
  return (current / max) * 100;
}

/**
 * 获取并发使用率颜色类
 */
export function getConcurrencyColorClass(rate: number): string {
  if (rate < 70) return 'bg-green-500';
  if (rate < 90) return 'bg-yellow-500';
  return 'bg-red-500';
}
