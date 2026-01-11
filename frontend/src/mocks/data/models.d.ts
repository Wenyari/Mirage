import type { Model } from '@/types/key';
/**
 * 模型配置 Mock 数据
 * 实际项目中应该从后端管理配置中获取
 */
export declare const mockModels: Model[];
/**
 * 获取所有启用的模型
 */
export declare function getEnabledModels(): Model[];
/**
 * 根据 key 获取模型配置
 */
export declare function getModelByKey(key: string): Model | undefined;
/**
 * 获取模型显示名称
 */
export declare function getModelName(key: string): string;
/**
 * 获取模型颜色
 */
export declare function getModelColor(key: string): string;
/**
 * 创建新模型
 */
export declare function createMockModel(data: {
    key: string;
    name: string;
    enabled: boolean;
    description?: string;
    color?: string;
    icon_url?: string;
    max_concurrency_limit?: number;
}): Model;
/**
 * 更新模型配置
 */
export declare function updateMockModel(key: string, updates: {
    name?: string;
    enabled?: boolean;
    description?: string;
    color?: string;
    icon_url?: string;
    max_concurrency_limit?: number;
}): Model | null;
/**
 * 删除模型
 */
export declare function deleteMockModel(key: string): boolean;
