import type { Key, ModelType } from '@/types/key';

/**
 * Mock 密钥数据列表
 * 模拟不同模型、不同状态的密钥
 */
export const mockKeys: Key[] = [];

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
): void {
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
