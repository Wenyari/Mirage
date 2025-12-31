import type { PlatformConfig } from '@/types/key';

/**
 * 平台配置 Mock 数据
 * 实际项目中应该从后端管理配置中获取
 */
export const mockPlatforms: PlatformConfig[] = [
  {
    key: 'openai',
    name: 'OpenAI',
    enabled: true,
    description: 'OpenAI GPT 系列模型',
    color: 'bg-green-500',
    max_concurrency_limit: 20,
  },
  {
    key: 'sora',
    name: 'Sora',
    enabled: true,
    description: 'OpenAI Sora 视频生成模型',
    color: 'bg-blue-500',
    max_concurrency_limit: 10,
  },
  {
    key: 'midjourney',
    name: 'Midjourney',
    enabled: true,
    description: 'Midjourney 图像生成',
    color: 'bg-purple-500',
    max_concurrency_limit: 15,
  },
  {
    key: 'anthropic',
    name: 'Anthropic',
    enabled: true,
    description: 'Anthropic Claude 系列模型',
    color: 'bg-orange-500',
    max_concurrency_limit: 20,
  },
  {
    key: 'google',
    name: 'Google',
    enabled: true,
    description: 'Google Gemini 系列模型',
    color: 'bg-red-500',
    max_concurrency_limit: 20,
  },
  {
    key: 'stability',
    name: 'Stability AI',
    enabled: false,
    description: 'Stable Diffusion 系列模型',
    color: 'bg-indigo-500',
    max_concurrency_limit: 10,
  },
];

/**
 * 获取所有启用的平台
 */
export function getEnabledPlatforms(): PlatformConfig[] {
  return mockPlatforms.filter((p) => p.enabled);
}

/**
 * 根据 key 获取平台配置
 */
export function getPlatformByKey(key: string): PlatformConfig | undefined {
  return mockPlatforms.find((p) => p.key === key);
}

/**
 * 获取平台显示名称
 */
export function getPlatformName(key: string): string {
  const platform = getPlatformByKey(key);
  return platform?.name || key;
}

/**
 * 获取平台颜色
 */
export function getPlatformColor(key: string): string {
  const platform = getPlatformByKey(key);
  return platform?.color || 'bg-gray-500';
}
