import type { Key, ModelType } from '@/types/key';
/**
 * Mock 密钥数据列表
 * 模拟不同模型、不同状态的密钥
 */
export declare const mockKeys: Key[];
/**
 * 添加单个密钥
 */
export declare function addMockKey(model: ModelType, keySecret: string, maxConcurrency?: number, weight?: number, apiBase?: string): Key;
/**
 * 批量添加密钥
 */
export declare function batchAddMockKeys(model: ModelType, keys: string[], maxConcurrency?: number, weight?: number, apiBase?: string): {
    success: Key[];
    failed: string[];
};
/**
 * 更新密钥配置
 */
export declare function updateMockKey(id: number, updates: {
    max_concurrency?: number;
    weight?: number;
    status?: 0 | 1;
}): boolean;
/**
 * 删除密钥
 */
export declare function deleteMockKey(id: number): boolean;
/**
 * 触发/解除熔断
 */
export declare function triggerCooldown(id: number, action: 'trigger' | 'release', duration?: number): boolean;
/**
 * 模拟并发使用变化（用于实时刷新测试）
 */
export declare function simulateConcurrencyChange(): void;
/**
 * 模拟冷却结束
 */
export declare function checkCoolingExpiry(): void;
