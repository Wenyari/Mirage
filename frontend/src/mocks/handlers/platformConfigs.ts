import { http, HttpResponse } from 'msw';
import type { CreatePlatformConfigRequest, UpdatePlatformConfigRequest } from '@/types/platformConfig';
import {
  mockPlatformConfigs,
  mockMembershipConfigs,
  addPlatformConfig,
  updatePlatformConfig,
  deletePlatformConfig,
  getAvailablePlatforms,
  updateMembershipConfigs,
} from '../data/platformConfigs';

/**
 * 平台配置管理相关的 Mock 处理器
 */
export const platformConfigHandlers = [
  /**
   * 获取平台配置列表
   * GET /api/admin/platform-configs
   */
  http.get('/api/admin/platform-configs', () => {
    return HttpResponse.json({
      code: 0,
      message: 'Success',
      data: mockPlatformConfigs,
    });
  }),

  /**
   * 获取可配置的平台列表
   * GET /api/admin/platform-configs/available-platforms
   */
  http.get('/api/admin/platform-configs/available-platforms', () => {
    return HttpResponse.json({
      code: 0,
      message: 'Success',
      data: getAvailablePlatforms(),
    });
  }),

  /**
   * 创建平台配置
   * POST /api/admin/platform-configs
   */
  http.post('/api/admin/platform-configs', async ({ request }) => {
    const body = (await request.json()) as CreatePlatformConfigRequest;

    // 验证平台是否已配置
    const exists = mockPlatformConfigs.find((c) => c.platform === body.platform);
    if (exists) {
      return HttpResponse.json(
        {
          code: 400,
          message: `Platform ${body.platform} already configured`,
          data: null,
        },
        { status: 400 }
      );
    }

    const newConfig = addPlatformConfig({
      platform: body.platform,
      platform_name: body.platform, // 实际应从 platforms 表获取 name
      allowed_tiers: body.allowed_tiers,
      cost_per_call: body.cost_per_call,
      token_cost_config: body.token_cost_config,
      is_active: body.is_active,
      description: body.description,
    });

    return HttpResponse.json({
      code: 0,
      message: 'Platform config created successfully',
      data: newConfig,
    });
  }),

  /**
   * 更新平台配置
   * PATCH /api/admin/platform-configs/:id
   */
  http.patch('/api/admin/platform-configs/:id', async ({ request, params }) => {
    const id = Number(params.id);
    const body = (await request.json()) as UpdatePlatformConfigRequest;

    const success = updatePlatformConfig(id, body);

    if (!success) {
      return HttpResponse.json(
        {
          code: 404,
          message: 'Platform config not found',
          data: null,
        },
        { status: 404 }
      );
    }

    return HttpResponse.json({
      code: 0,
      message: 'Platform config updated successfully',
      data: null,
    });
  }),

  /**
   * 删除平台配置
   * DELETE /api/admin/platform-configs/:id
   */
  http.delete('/api/admin/platform-configs/:id', ({ params }) => {
    const id = Number(params.id);
    const success = deletePlatformConfig(id);

    if (!success) {
      return HttpResponse.json(
        {
          code: 404,
          message: 'Platform config not found',
          data: null,
        },
        { status: 404 }
      );
    }

    return HttpResponse.json({
      code: 0,
      message: 'Platform config deleted successfully',
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
