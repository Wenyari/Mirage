/**
 * 模型配置管理类型定义
 * 基于密钥池的 model 进行等级权限和计费配置
 */
/**
 * 会员等级类型
 */
export type MembershipTier = 'T1' | 'T2' | 'T3' | 'T4' | 'T5';
/**
 * Token 计费配置
 */
export interface TokenCostConfig {
    enabled: boolean;
    input_cost?: number;
    output_cost?: number;
}
/**
 * 模型配置实体
 */
export interface ModelConfig {
    id: number;
    model: string;
    model_name: string;
    allowed_tiers: MembershipTier[];
    cost_per_call: number;
    token_cost_config: TokenCostConfig;
    params?: Record<string, any>;
    is_active: boolean;
    description?: string;
    created_at: string;
    updated_at: string;
}
/**
 * 可配置的模型信息
 */
export interface AvailableModel {
    model: string;
    model_name: string;
    has_config: boolean;
    key_count: number;
}
/**
 * 创建模型配置请求
 */
export interface CreateModelConfigRequest {
    model: string;
    allowed_tiers: MembershipTier[];
    cost_per_call: number;
    token_cost_config: TokenCostConfig;
    params?: Record<string, any>;
    is_active: boolean;
    description?: string;
}
/**
 * 更新模型配置请求
 */
export interface UpdateModelConfigRequest {
    allowed_tiers?: MembershipTier[];
    cost_per_call?: number;
    token_cost_config?: TokenCostConfig;
    params?: Record<string, any>;
    is_active?: boolean;
    description?: string;
}
/**
 * 会员等级配置
 */
export interface MembershipConfig {
    level: number;
    name: MembershipTier;
    concurrent_limit: number;
    queue_weight: number;
    price: number;
    description: string;
}
/**
 * 会员等级配置集合
 */
export type MembershipConfigs = Record<MembershipTier, MembershipConfig>;
/**
 * 会员等级显示名称
 */
export declare const MEMBERSHIP_TIER_LABELS: Record<MembershipTier, string>;
/**
 * 所有会员等级列表
 */
export declare const ALL_MEMBERSHIP_TIERS: MembershipTier[];
/**
 * 计算总扣除积分（辅助函数）
 */
export declare function calculateTotalCost(config: ModelConfig, inputTokens?: number, outputTokens?: number): number;
