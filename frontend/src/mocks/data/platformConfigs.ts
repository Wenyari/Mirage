import type { PlatformConfig, MembershipConfigs, AvailablePlatform } from '@/types/platformConfig';
import { mockPlatforms } from './platforms';
import { mockKeys } from './keys';

/**
 * Mock 平台配置数据
 */
export const mockPlatformConfigs: PlatformConfig[] = [
  {
    id: 1,
    platform: 'openai',
    platform_name: 'OpenAI',
    allowed_tiers: ['T1', 'T2', 'T3', 'T4', 'T5'],
    cost_per_call: 10,
    token_cost_config: {
      enabled: true,
      input_cost: 0.03,
      output_cost: 0.06,
    },
    is_active: true,
    description: 'OpenAI GPT 系列模型',
    created_at: '2024-03-01T10:00:00Z',
    updated_at: '2024-03-20T15:30:00Z',
  },
  {
    id: 2,
    platform: 'sora',
    platform_name: 'Sora',
    allowed_tiers: ['T3', 'T4', 'T5'],
    cost_per_call: 100,
    token_cost_config: {
      enabled: false,
    },
    is_active: true,
    description: 'OpenAI Sora 视频生成模型',
    created_at: '2024-03-10T12:00:00Z',
    updated_at: '2024-03-20T16:00:00Z',
  },
  {
    id: 3,
    platform: 'midjourney',
    platform_name: 'Midjourney',
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
  {
    id: 4,
    platform: 'anthropic',
    platform_name: 'Anthropic',
    allowed_tiers: ['T1', 'T2', 'T3', 'T4', 'T5'],
    cost_per_call: 15,
    token_cost_config: {
      enabled: true,
      input_cost: 0.04,
      output_cost: 0.08,
    },
    is_active: true,
    description: 'Anthropic Claude 系列模型',
    created_at: '2024-03-15T11:00:00Z',
    updated_at: '2024-03-21T10:00:00Z',
  },
  {
    id: 5,
    platform: 'google',
    platform_name: 'Google',
    allowed_tiers: ['T1', 'T2', 'T3', 'T4', 'T5'],
    cost_per_call: 8,
    token_cost_config: {
      enabled: true,
      input_cost: 0.025,
      output_cost: 0.05,
    },
    is_active: true,
    description: 'Google Gemini 系列模型',
    created_at: '2024-03-12T09:30:00Z',
    updated_at: '2024-03-19T14:00:00Z',
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
 * 添加平台配置
 */
export function addPlatformConfig(config: Omit<PlatformConfig, 'id' | 'created_at' | 'updated_at'>): PlatformConfig {
  const newConfig: PlatformConfig = {
    ...config,
    id: Math.max(...mockPlatformConfigs.map((c) => c.id), 0) + 1,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  mockPlatformConfigs.push(newConfig);
  return newConfig;
}

/**
 * 更新平台配置
 */
export function updatePlatformConfig(id: number, updates: Partial<PlatformConfig>): boolean {
  const index = mockPlatformConfigs.findIndex((c) => c.id === id);
  if (index === -1) return false;

  mockPlatformConfigs[index] = {
    ...mockPlatformConfigs[index],
    ...updates,
    updated_at: new Date().toISOString(),
  };

  return true;
}

/**
 * 删除平台配置
 */
export function deletePlatformConfig(id: number): boolean {
  const index = mockPlatformConfigs.findIndex((c) => c.id === id);
  if (index === -1) return false;

  mockPlatformConfigs.splice(index, 1);
  return true;
}

/**
 * 获取可配置的平台列表（从实际的平台表和密钥池动态获取）
 */
export function getAvailablePlatforms(): AvailablePlatform[] {
  // 从 mockPlatforms 获取所有启用的平台
  const enabledPlatforms = mockPlatforms.filter((p) => p.enabled);

  // 统计每个平台的密钥数量
  return enabledPlatforms.map((platform) => {
    const keyCount = mockKeys.filter((k) => k.platform === platform.key).length;
    const hasConfig = mockPlatformConfigs.some((c) => c.platform === platform.key);

    return {
      platform: platform.key,
      platform_name: platform.name,
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
