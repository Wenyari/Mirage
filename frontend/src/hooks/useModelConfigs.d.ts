import type { CreateModelConfigRequest, UpdateModelConfigRequest, MembershipConfigs } from '@/types/modelConfig';
/**
 * 获取模型配置列表
 */
export declare function useModelConfigs(): import("@tanstack/react-query").UseQueryResult<{
    code: number;
    message: string;
    data: import("@/types/modelConfig").ModelConfig[];
}, Error>;
/**
 * 获取可配置的模型列表
 */
export declare function useAvailableModels(): import("@tanstack/react-query").UseQueryResult<{
    code: number;
    message: string;
    data: import("@/types/modelConfig").AvailableModel[];
}, Error>;
/**
 * 创建模型配置
 */
export declare function useCreateModelConfig(): import("@tanstack/react-query").UseMutationResult<{
    code: number;
    message: string;
    data: import("@/types/modelConfig").ModelConfig;
}, Error, CreateModelConfigRequest, unknown>;
/**
 * 更新模型配置
 */
export declare function useUpdateModelConfig(): import("@tanstack/react-query").UseMutationResult<{
    code: number;
    message: string;
    data: null;
}, Error, {
    id: number;
    data: UpdateModelConfigRequest;
}, unknown>;
/**
 * 删除模型配置
 */
export declare function useDeleteModelConfig(): import("@tanstack/react-query").UseMutationResult<{
    code: number;
    message: string;
    data: null;
}, Error, number, unknown>;
/**
 * 获取会员等级配置
 */
export declare function useMembershipConfigs(): import("@tanstack/react-query").UseQueryResult<{
    code: number;
    message: string;
    data: MembershipConfigs;
}, Error>;
/**
 * 更新会员等级配置
 */
export declare function useUpdateMembershipConfigs(): import("@tanstack/react-query").UseMutationResult<{
    code: number;
    message: string;
    data: null;
}, Error, MembershipConfigs, unknown>;
