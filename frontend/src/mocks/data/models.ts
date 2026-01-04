import type { Model } from '@/types/key';

/**
 * 模型配置 Mock 数据
 * 实际项目中应该从后端管理配置中获取
 */
export const mockModels: Model[] = [
  {
    key: 'gpt-4',
    name: 'GPT-4',
    enabled: true,
    description: 'OpenAI GPT-4 模型',
    color: 'bg-green-500',
    max_concurrency_limit: 20,
  },
  {
    key: 'gpt-3.5-turbo',
    name: 'GPT-3.5 Turbo',
    enabled: true,
    description: 'OpenAI GPT-3.5 Turbo 模型',
    color: 'bg-green-400',
    max_concurrency_limit: 50,
  },
  {
    key: 'claude-3-opus',
    name: 'Claude 3 Opus',
    enabled: true,
    description: 'Anthropic Claude 3 Opus 模型',
    color: 'bg-orange-500',
    max_concurrency_limit: 10,
  },
  {
    key: 'claude-3-sonnet',
    name: 'Claude 3 Sonnet',
    enabled: true,
    description: 'Anthropic Claude 3 Sonnet 模型',
    color: 'bg-orange-400',
    max_concurrency_limit: 20,
  },
  {
    key: 'gemini-pro',
    name: 'Gemini Pro',
    enabled: true,
    description: 'Google Gemini Pro 模型',
    color: 'bg-red-500',
    max_concurrency_limit: 30,
  },
  {
    key: 'midjourney',
    name: 'Midjourney',
    enabled: true,
    description: 'Midjourney 图像生成',
    color: 'bg-purple-500',
    max_concurrency_limit: 15,
  },
];

/**
 * 获取所有启用的模型
 */
export function getEnabledModels(): Model[] {
  return mockModels.filter((m) => m.enabled);
}

/**
 * 根据 key 获取模型配置
 */
export function getModelByKey(key: string): Model | undefined {
  return mockModels.find((m) => m.key === key);
}

/**
 * 获取模型显示名称
 */
export function getModelName(key: string): string {
  const model = getModelByKey(key);
  return model?.name || key;
}

/**
 * 获取模型颜色
 */
export function getModelColor(key: string): string {
  const model = getModelByKey(key);
  return model?.color || 'bg-gray-500';
}

/**
 * 创建新模型
 */
export function createMockModel(data: {
  key: string;
  name: string;
  enabled: boolean;
  description?: string;
  color?: string;
  icon_url?: string;
  max_concurrency_limit?: number;
}): Model {
  // 检查模型key是否已存在
  if (mockModels.find((m) => m.key === data.key)) {
    throw new Error('Model key already exists');
  }

  const newModel: Model = {
    ...data,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  mockModels.push(newModel);
  return newModel;
}

/**
 * 更新模型配置
 */
export function updateMockModel(
  key: string,
  updates: {
    name?: string;
    enabled?: boolean;
    description?: string;
    color?: string;
    icon_url?: string;
    max_concurrency_limit?: number;
  }
): Model | null {
  const model = mockModels.find((m) => m.key === key);
  if (!model) return null;

  Object.assign(model, updates);
  model.updated_at = new Date().toISOString();

  return model;
}

/**
 * 删除模型
 */
export function deleteMockModel(key: string): boolean {
  const index = mockModels.findIndex((m) => m.key === key);
  if (index === -1) return false;

  mockModels.splice(index, 1);
  return true;
}
