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
  enabled: boolean;           // 是否启用 Token 计费
  input_cost?: number;        // 输入 Token 费率（每千 token，积分）
  output_cost?: number;       // 输出 Token 费率（每千 token，积分）
}

/**
 * 模型配置实体
 */
export interface ModelConfig {
  id: number;
  model: string;                   // 模型标识（来自密钥池）
  model_name: string;              // 模型显示名称
  allowed_tiers: MembershipTier[]; // 允许使用的等级
  cost_per_call: number;           // 每次调用扣除积分（固定计费）
  token_cost_config: TokenCostConfig; // Token 计费配置
  is_active: boolean;              // 是否启用该模型
  description?: string;            // 模型描述
  created_at: string;
  updated_at: string;
}

/**
 * 可配置的模型信息
 */
export interface AvailableModel {
  model: string;              // 模型标识
  model_name: string;         // 模型显示名称
  has_config: boolean;        // 是否已有配置
  key_count: number;          // 该模型的密钥数量
}

/**
 * 创建模型配置请求
 */
export interface CreateModelConfigRequest {
  model: string;
  allowed_tiers: MembershipTier[];
  cost_per_call: number;
  token_cost_config: TokenCostConfig;
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
  is_active?: boolean;
  description?: string;
}

/**
 * 会员等级配置
 */
export interface MembershipConfig {
  level: number;
  name: MembershipTier;
  concurrent_limit: number;    // 并发数限制
  queue_weight: number;        // 队列权重
  price: number;               // 价格（元/月）
  description: string;
}

/**
 * 会员等级配置集合
 */
export type MembershipConfigs = Record<MembershipTier, MembershipConfig>;

/**
 * 会员等级显示名称
 */
export const MEMBERSHIP_TIER_LABELS: Record<MembershipTier, string> = {
  T1: 'T1 免费版',
  T2: 'T2 基础版',
  T3: 'T3 高级版',
  T4: 'T4 专业版',
  T5: 'T5 旗舰版',
};

/**
 * 所有会员等级列表
 */
export const ALL_MEMBERSHIP_TIERS: MembershipTier[] = ['T1', 'T2', 'T3', 'T4', 'T5'];

/**
 * 计算总扣除积分（辅助函数）
 */
export function calculateTotalCost(
  config: ModelConfig,
  inputTokens: number = 0,
  outputTokens: number = 0
): number {
  let total = config.cost_per_call;

  if (config.token_cost_config.enabled) {
    if (config.token_cost_config.input_cost) {
      total += (inputTokens / 1000) * config.token_cost_config.input_cost;
    }
    if (config.token_cost_config.output_cost) {
      total += (outputTokens / 1000) * config.token_cost_config.output_cost;
    }
  }

  return Math.round(total * 100) / 100; // 保留两位小数
}
