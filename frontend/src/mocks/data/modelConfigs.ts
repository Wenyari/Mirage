import type { AvailableModel,MembershipConfigs, ModelConfig } from '@/types/modelConfig';

import { mockKeys } from './keys';
import { mockModels } from './models';

/**
 * Mock 模型配置数据
 */
export const mockModelConfigs: ModelConfig[] = [
  {
    id: 1,
    model: 'gpt-4',
    model_name: 'GPT-4',
    allowed_tiers: ['T1', 'T2', 'T3', 'T4', 'T5'],
    cost_per_call: 10,
    token_cost_config: {
      enabled: true,
      input_cost: 0.03,
      output_cost: 0.06,
    },
    is_active: true,
    description: 'OpenAI GPT-4 模型',
    created_at: '2024-03-01T10:00:00Z',
    updated_at: '2024-03-20T15:30:00Z',
  },
  {
    id: 2,
    model: 'claude-3-opus',
    model_name: 'Claude 3 Opus',
    allowed_tiers: ['T3', 'T4', 'T5'],
    cost_per_call: 100,
    token_cost_config: {
      enabled: true,
      input_cost: 0.05,
      output_cost: 0.1,
    },
    is_active: true,
    description: 'Anthropic Claude 3 Opus 模型',
    created_at: '2024-03-10T12:00:00Z',
    updated_at: '2024-03-20T16:00:00Z',
  },
  {
    id: 3,
    model: 'midjourney',
    model_name: 'Midjourney',
    allowed_tiers: ['T2', 'T3', 'T4', 'T5'],
    cost_per_call: 50,
    token_cost_config: {
      enabled: false,
    },
    is_active: true,
    description: 'Midjourney 图像生成',
    created_at: '2024-03-05T09:00:00Z',
    updated_at: '2024-03-18T14:00:00Z',
  },
];

/**
 * Mock 会员等级配置
 */
export const mockMembershipConfigs: MembershipConfigs = {
  T1: {
    level: 1,
    name: 'T1',
    concurrent_limit: 1,
    queue_weight: 1,
    price: 0,
    description: '免费用户',
  },
  T2: {
    level: 2,
    name: 'T2',
    concurrent_limit: 3,
    queue_weight: 2,
    price: 29,
    description: '基础会员',
  },
  T3: {
    level: 3,
    name: 'T3',
    concurrent_limit: 5,
    queue_weight: 3,
    price: 99,
    description: '高级会员',
  },
  T4: {
    level: 4,
    name: 'T4',
    concurrent_limit: 10,
    queue_weight: 4,
    price: 299,
    description: '专业会员',
  },
  T5: {
    level: 5,
    name: 'T5',
    concurrent_limit: 20,
    queue_weight: 5,
    price: 999,
    description: '旗舰会员',
  },
};

/**
 * 添加模型配置
 */
export function addModelConfig(config: Omit<ModelConfig, 'id' | 'created_at' | 'updated_at'>): ModelConfig {
  const newConfig: ModelConfig = {
    ...config,
    id: Math.max(...mockModelConfigs.map((c) => c.id), 0) + 1,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  mockModelConfigs.push(newConfig);
  return newConfig;
}

/**
 * 更新模型配置
 */
export function updateModelConfig(id: number, updates: Partial<ModelConfig>): boolean {
  const index = mockModelConfigs.findIndex((c) => c.id === id);
  if (index === -1) return false;

  mockModelConfigs[index] = {
    ...mockModelConfigs[index],
    ...updates,
    updated_at: new Date().toISOString(),
  };

  return true;
}

/**
 * 删除模型配置
 */
export function deleteModelConfig(id: number): boolean {
  const index = mockModelConfigs.findIndex((c) => c.id === id);
  if (index === -1) return false;

  mockModelConfigs.splice(index, 1);
  return true;
}

/**
 * 获取可配置的模型列表（从实际的模型表和密钥池动态获取）
 */
export function getAvailableModels(): AvailableModel[] {
  // 从 mockModels 获取所有启用的模型
  const enabledModels = mockModels.filter((p) => p.enabled);

  // 统计每个模型的密钥数量
  return enabledModels.map((model) => {
    const keyCount = mockKeys.filter((k) => k.model === model.key).length;
    const hasConfig = mockModelConfigs.some((c) => c.model === model.key);

    return {
      model: model.key,
      model_name: model.name,
      key_count: keyCount,
      has_config: hasConfig,
    };
  });
}

/**
 * 更新会员等级配置
 */
export function updateMembershipConfigs(configs: MembershipConfigs): boolean {
  Object.assign(mockMembershipConfigs, configs);
  return true;
}
