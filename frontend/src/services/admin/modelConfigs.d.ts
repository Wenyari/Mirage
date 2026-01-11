import type { ModelConfig, AvailableModel, CreateModelConfigRequest, UpdateModelConfigRequest, MembershipConfigs } from '@/types/modelConfig';
/**
 * 获取模型配置列表
 */
export declare function getModelConfigs(): Promise<{
    code: number;
    message: string;
    data: ModelConfig[];
}>;
/**
 * 获取可配置的模型列表
 */
export declare function getAvailableModels(): Promise<{
    code: number;
    message: string;
    data: AvailableModel[];
}>;
/**
 * 创建模型配置
 */
export declare function createModelConfig(data: CreateModelConfigRequest): Promise<{
    code: number;
    message: string;
    data: ModelConfig;
}>;
/**
 * 更新模型配置
 */
export declare function updateModelConfig(id: number, data: UpdateModelConfigRequest): Promise<{
    code: number;
    message: string;
    data: null;
}>;
/**
 * 删除模型配置
 */
export declare function deleteModelConfig(id: number): Promise<{
    code: number;
    message: string;
    data: null;
}>;
/**
 * 获取会员等级配置
 */
export declare function getMembershipConfigs(): Promise<{
    code: number;
    message: string;
    data: MembershipConfigs;
}>;
/**
 * 更新会员等级配置
 */
export declare function updateMembershipConfigs(data: MembershipConfigs): Promise<{
    code: number;
    message: string;
    data: null;
}>;
