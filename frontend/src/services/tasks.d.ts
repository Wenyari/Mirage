import type { ApiResponse } from '@/types/api';
export interface CreateTaskRequest {
    model: string;
    prompt: string;
    params?: Record<string, any>;
    input_file_url?: string | string[];
}
export interface TaskResponse {
    task_id: string;
    status: string;
}
export interface QueueInfo {
    user_queue: string;
    position: number;
    vip_queue: number;
    normal_queue: number;
}
export interface TaskStatusResponse {
    id: string;
    status: 'pending' | 'processing' | 'success' | 'failed' | 'cancelled';
    progress?: number;
    queue_info?: QueueInfo;
    result_url?: string;
    fail_reason?: string;
    model?: string;
    prompt?: string;
    params?: Record<string, any>;
    input_file_url?: string | string[];
    created_at?: string;
    cost_points?: number;
}
export interface ModelOption {
    key: string;
    name: string;
    description: string;
    cost_per_call: number;
    is_available: boolean;
    user_tier: string;
    min_tier: string;
    allowed_tiers: string[];
    color: string;
    icon_url: string;
    enabled: number;
    max_concurrency_limit: number;
    token_cost_config?: any;
    params?: any;
    tags?: string[];
}
export interface TaskHistoryItem {
    id: string;
    model: string;
    prompt: string;
    status: 'pending' | 'processing' | 'success' | 'failed' | 'cancelled';
    created_at: string;
    result_url?: string;
    thumbnail_url?: string;
}
export interface TaskHistoryResponse {
    list: TaskHistoryItem[];
    total: number;
    page: number;
    size: number;
}
export declare const taskService: {
    getTaskHistory: (page?: number, size?: number) => Promise<ApiResponse<TaskHistoryResponse>>;
    getAvailableModels: () => Promise<ApiResponse<ModelOption[]>>;
    createTask: (data: CreateTaskRequest) => Promise<ApiResponse<TaskResponse>>;
    getTaskStatus: (taskId: string) => Promise<ApiResponse<TaskStatusResponse>>;
    cancelTask: (taskId: string) => Promise<import("axios").AxiosResponse<ApiResponse<void>, any, {}>>;
};
