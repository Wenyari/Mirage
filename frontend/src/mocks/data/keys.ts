import type { Key, ModelType } from '@/types/key';

/**
 * Mock 密钥数据列表
 * 模拟不同模型、不同状态的密钥
 */
export const mockKeys: Key[] = [
  // GPT-4 密钥（正常使用中）
  {
    id: 1,
    model: 'gpt-4',
    api_base: 'https://api.openai.com/v1',
    key_secret: 'sk-proj-abc12345defg6789hijk0123lmno4567pqrs8901tuvw',
    max_concurrency: 5,
    weight: 20,
    status: 1,
    total_calls: 25680,
    total_errors: 34,
    current_usage: 3,
    is_cooling: false,
    cooling_until: null,
    last_used_at: '2024-12-31T10:30:00Z',
    created_at: '2024-01-15T08:00:00Z',
  },
  {
    id: 2,
    model: 'gpt-3.5-turbo',
    api_base: '',
    key_secret: 'sk-proj-wxyz9876abcd5432efgh1234ijkl8765mnop4321qrst',
    max_concurrency: 3,
    weight: 10,
    status: 1,
    total_calls: 12450,
    total_errors: 18,
    current_usage: 2,
    is_cooling: false,
    cooling_until: null,
    last_used_at: '2024-12-31T10:25:00Z',
    created_at: '2024-02-20T14:30:00Z',
  },
  {
    id: 3,
    model: 'gpt-4',
    api_base: 'https://openai.proxy.com/v1',
    key_secret: 'sk-proj-test1111test2222test3333test4444test5555test',
    max_concurrency: 2,
    weight: 5,
    status: 1,
    total_calls: 5620,
    total_errors: 245,
    current_usage: 0,
    is_cooling: true,
    cooling_until: new Date(Date.now() + 180000).toISOString(), // 3分钟后
    last_used_at: '2024-12-31T10:27:00Z',
    created_at: '2024-03-10T09:15:00Z',
  },

  // Midjourney 密钥
  {
    id: 6,
    model: 'midjourney',
    api_base: '',
    key_secret: 'mj-key-abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx',
    max_concurrency: 4,
    weight: 12,
    status: 1,
    total_calls: 8920,
    total_errors: 56,
    current_usage: 4, // 满载
    is_cooling: false,
    cooling_until: null,
    last_used_at: '2024-12-31T10:29:00Z',
    created_at: '2024-02-28T16:45:00Z',
  },
  {
    id: 7,
    model: 'midjourney',
    api_base: 'https://mj.proxy.com',
    key_secret: 'mj-key-yzab5678cdef1234ghij5678klmn9012opqr3456stuv',
    max_concurrency: 3,
    weight: 8,
    status: 0, // 已停用
    total_calls: 3450,
    total_errors: 120,
    current_usage: 0,
    is_cooling: false,
    cooling_until: null,
    last_used_at: '2024-12-30T18:00:00Z',
    created_at: '2024-03-15T10:00:00Z',
  },

  // Claude 3 Opus 密钥
  {
    id: 8,
    model: 'claude-3-opus',
    api_base: 'https://api.anthropic.com',
    key_secret: 'sk-ant-api03-abc123def456ghi789jkl012mno345pqr678stu901',
    max_concurrency: 5,
    weight: 18,
    status: 1,
    total_calls: 15230,
    total_errors: 28,
    current_usage: 1,
    is_cooling: false,
    cooling_until: null,
    last_used_at: '2024-12-31T10:26:00Z',
    created_at: '2024-01-25T09:30:00Z',
  },

  // Gemini Pro 密钥
  {
    id: 9,
    model: 'gemini-pro',
    api_base: '',
    key_secret: 'AIzaSyAbc123Def456Ghi789Jkl012Mno345Pqr678',
    max_concurrency: 10,
    weight: 25,
    status: 1,
    total_calls: 42350,
    total_errors: 65,
    current_usage: 7,
    is_cooling: false,
    cooling_until: null,
    last_used_at: '2024-12-31T10:29:30Z',
    created_at: '2024-01-10T07:00:00Z',
  },
  {
    id: 10,
    model: 'gemini-pro',
    key_secret: 'AIzaSyDef456Ghi789Jkl012Mno345Pqr678Stu901',
    max_concurrency: 5,
    weight: 15,
    status: 1,
    total_calls: 18670,
    total_errors: 42,
    current_usage: 2,
    is_cooling: false,
    cooling_until: null,
    last_used_at: '2024-12-31T10:28:45Z',
    created_at: '2024-02-15T13:20:00Z',
  },
];

/**
 * 下一个可用的密钥 ID
 */
let nextKeyId = mockKeys.length + 1;

/**
 * 添加单个密钥
 */
export function addMockKey(
  model: ModelType,
  keySecret: string,
  maxConcurrency: number = 3,
  weight: number = 10,
  apiBase: string = ''
): Key {
  const newKey: Key = {
    id: nextKeyId++,
    model,
    api_base: apiBase,
    key_secret: keySecret,
    max_concurrency: maxConcurrency,
    weight,
    status: 1,
    total_calls: 0,
    total_errors: 0,
    current_usage: 0,
    is_cooling: false,
    cooling_until: null,
    last_used_at: new Date().toISOString(),
    created_at: new Date().toISOString(),
  };

  mockKeys.unshift(newKey);
  return newKey;
}

/**
 * 批量添加密钥
 */
export function batchAddMockKeys(
  model: ModelType,
  keys: string[],
  maxConcurrency: number = 3,
  weight: number = 10,
  apiBase: string = ''
): { success: Key[]; failed: string[] } {
  const success: Key[] = [];
  const failed: string[] = [];

  keys.forEach((keySecret) => {
    try {
      // 简单验证（检查是否已存在）
      if (mockKeys.find((k) => k.key_secret === keySecret)) {
        failed.push(keySecret);
      } else {
        const newKey = addMockKey(model, keySecret, maxConcurrency, weight, apiBase);
        success.push(newKey);
      }
    } catch {
      failed.push(keySecret);
    }
  });

  return { success, failed };
}

/**
 * 更新密钥配置
 */
export function updateMockKey(
  id: number,
  updates: { max_concurrency?: number; weight?: number; status?: 0 | 1 }
): boolean {
  const key = mockKeys.find((k) => k.id === id);
  if (!key) return false;

  if (updates.max_concurrency !== undefined) {
    key.max_concurrency = updates.max_concurrency;
  }
  if (updates.weight !== undefined) {
    key.weight = updates.weight;
  }
  if (updates.status !== undefined) {
    key.status = updates.status;
  }

  return true;
}

/**
 * 删除密钥
 */
export function deleteMockKey(id: number): boolean {
  const index = mockKeys.findIndex((k) => k.id === id);
  if (index === -1) return false;

  mockKeys.splice(index, 1);
  return true;
}

/**
 * 触发/解除熔断
 */
export function triggerCooldown(id: number, action: 'trigger' | 'release', duration: number = 300): boolean {
  const key = mockKeys.find((k) => k.id === id);
  if (!key) return false;

  if (action === 'trigger') {
    key.is_cooling = true;
    key.cooling_until = new Date(Date.now() + duration * 1000).toISOString();
  } else {
    key.is_cooling = false;
    key.cooling_until = null;
  }

  return true;
}

/**
 * 模拟并发使用变化（用于实时刷新测试）
 */
export function simulateConcurrencyChange(): void {
  mockKeys.forEach((key) => {
    if (key.status === 1 && !key.is_cooling) {
      // 随机增减并发数
      const change = Math.random() > 0.5 ? 1 : -1;
      key.current_usage = Math.max(0, Math.min(key.max_concurrency, key.current_usage + change));
    }
  });
}

/**
 * 模拟冷却结束
 */
export function checkCoolingExpiry(): void {
  const now = Date.now();
  mockKeys.forEach((key) => {
    if (key.is_cooling && key.cooling_until) {
      if (new Date(key.cooling_until).getTime() <= now) {
        key.is_cooling = false;
        key.cooling_until = null;
      }
    }
  });
}
