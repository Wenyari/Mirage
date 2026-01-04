import { http, HttpResponse } from 'msw';

import type { CreateModelConfigRequest, UpdateModelConfigRequest } from '@/types/modelConfig';

import {
  addModelConfig,
  deleteModelConfig,
  getAvailableModels,
  mockMembershipConfigs,
  mockModelConfigs,
  updateMembershipConfigs,
  updateModelConfig,
} from '../data/modelConfigs';

/**
 * 模型配置管理相关的 Mock 处理器
 */
export const modelConfigHandlers = [
  /**
   * 获取模型配置列表
   * GET /api/admin/model-configs
   */
  http.get('/api/admin/model-configs', () => {
    return HttpResponse.json({
      code: 0,
      message: 'Success',
      data: mockModelConfigs,
    });
  }),

  /**
   * 获取可配置的模型列表
   * GET /api/admin/model-configs/available-models
   */
  http.get('/api/admin/model-configs/available-models', () => {
    return HttpResponse.json({
      code: 0,
      message: 'Success',
      data: getAvailableModels(),
    });
  }),

  /**
   * 创建模型配置
   * POST /api/admin/model-configs
   */
  http.post('/api/admin/model-configs', async ({ request }) => {
    const body = (await request.json()) as CreateModelConfigRequest;

    // 验证模型是否已配置
    const exists = mockModelConfigs.find((c) => c.model === body.model);
    if (exists) {
      return HttpResponse.json(
        {
          code: 400,
          message: `Model ${body.model} already configured`,
          data: null,
        },
        { status: 400 }
      );
    }

    const newConfig = addModelConfig({
      model: body.model,
      model_name: body.model, // 实际应从 models 表获取 name
      allowed_tiers: body.allowed_tiers,
      cost_per_call: body.cost_per_call,
      token_cost_config: body.token_cost_config,
      is_active: body.is_active,
      description: body.description,
    });

    return HttpResponse.json({
      code: 0,
      message: 'Model config created successfully',
      data: newConfig,
    });
  }),

  /**
   * 更新模型配置
   * PATCH /api/admin/model-configs/:id
   */
  http.patch('/api/admin/model-configs/:id', async ({ request, params }) => {
    const id = Number(params.id);
    const body = (await request.json()) as UpdateModelConfigRequest;

    const success = updateModelConfig(id, body);

    if (!success) {
      return HttpResponse.json(
        {
          code: 404,
          message: 'Model config not found',
          data: null,
        },
        { status: 404 }
      );
    }

    return HttpResponse.json({
      code: 0,
      message: 'Model config updated successfully',
      data: null,
    });
  }),

  /**
   * 删除模型配置
   * DELETE /api/admin/model-configs/:id
   */
  http.delete('/api/admin/model-configs/:id', ({ params }) => {
    const id = Number(params.id);
    const success = deleteModelConfig(id);

    if (!success) {
      return HttpResponse.json(
        {
          code: 404,
          message: 'Model config not found',
          data: null,
        },
        { status: 404 }
      );
    }

    return HttpResponse.json({
      code: 0,
      message: 'Model config deleted successfully',
      data: null,
    });
  }),

  /**
   * 获取会员等级配置
   * GET /api/admin/config/membership
   */
  http.get('/api/admin/config/membership', () => {
    return HttpResponse.json({
      code: 0,
      message: 'Success',
      data: mockMembershipConfigs,
    });
  }),

  /**
   * 更新会员等级配置
   * PUT /api/admin/config/membership
   */
  http.put('/api/admin/config/membership', async ({ request }) => {
    const body = await request.json();
    updateMembershipConfigs(body);

    return HttpResponse.json({
      code: 0,
      message: 'Membership config updated successfully',
      data: null,
    });
  }),
];
