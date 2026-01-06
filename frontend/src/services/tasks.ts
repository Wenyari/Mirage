import api from '@/lib/api';
import type { ApiResponse } from '@/types/api';

// Request Types
export interface CreateTaskRequest {
  model: string;
  prompt: string;
  params?: Record<string, any>;
  input_file_url?: string;
}

// Response Types
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
  token_cost_config?: any; // optional token cost config (kept for backward compat)
  params?: any; // optional JSON config for model-specific params like durations, hd, etc.
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

export const taskService = {
  // 获取任务历史
  getTaskHistory: async (page = 1, size = 20) => {
    const response = await api.get<ApiResponse<TaskHistoryResponse>>('/tasks', {
      params: { page, size }
    });
    return response.data;
  },

  // 获取可用模型列表
  getAvailableModels: async () => {
    const response = await api.get<ApiResponse<ModelOption[]>>('/tasks/models');
    return response.data;
  },

  // 提交新任务
  createTask: async (data: CreateTaskRequest) => {
    const response = await api.post<ApiResponse<TaskResponse>>('/tasks', data);
    return response.data;
  },

  // 查询任务状态
  getTaskStatus: async (taskId: string) => {
    const response = await api.get<ApiResponse<TaskStatusResponse>>(`/tasks/${taskId}`);
    return response.data;
  },

  // 取消任务
  cancelTask: async (taskId: string) => {
    return api.post<ApiResponse<void>>(`/tasks/${taskId}/cancel`);
  },
};
