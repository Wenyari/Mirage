import type { AvailableModel, MembershipConfigs, ModelConfig } from '@/types/modelConfig';
/**
 * Mock 模型配置数据
 */
export declare const mockModelConfigs: ModelConfig[];
/**
 * Mock 会员等级配置
 */
export declare const mockMembershipConfigs: MembershipConfigs;
/**
 * 添加模型配置
 */
export declare function addModelConfig(config: Omit<ModelConfig, 'id' | 'created_at' | 'updated_at'>): ModelConfig;
/**
 * 更新模型配置
 */
export declare function updateModelConfig(id: number, updates: Partial<ModelConfig>): boolean;
/**
 * 删除模型配置
 */
export declare function deleteModelConfig(id: number): boolean;
/**
 * 获取可配置的模型列表（从实际的模型表和密钥池动态获取）
 */
export declare function getAvailableModels(): AvailableModel[];
/**
 * 更新会员等级配置
 */
export declare function updateMembershipConfigs(configs: MembershipConfigs): boolean;
