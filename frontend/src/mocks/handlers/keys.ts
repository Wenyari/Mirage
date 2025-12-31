import { http, HttpResponse } from 'msw';
import type {
  AddKeyRequest,
  BatchAddKeysRequest,
  UpdateKeyRequest,
  CooldownRequest,
  Platform,
} from '@/types/key';
import {
  mockKeys,
  addMockKey,
  batchAddMockKeys,
  updateMockKey,
  deleteMockKey,
  triggerCooldown,
  checkCoolingExpiry,
  simulateConcurrencyChange,
} from '../data/keys';
import { mockPlatforms } from '../data/platforms';
import { maskKey } from '@/types/key';

/**
 * 密钥池管理相关的 Mock 处理器
 */
export const keysHandlers = [
  /**
   * 获取平台配置列表
   * GET /api/admin/platforms
   */
  http.get('/api/admin/platforms', () => {
    return HttpResponse.json({
      code: 0,
      message: 'success',
      data: mockPlatforms,
    });
  }),

  /**
   * 获取密钥列表
   * GET /api/admin/keys
   */
  http.get('/api/admin/keys', ({ request }) => {
    const url = new URL(request.url);
    const platform = url.searchParams.get('platform') as Platform | null;

    // 模拟冷却过期检查
    checkCoolingExpiry();

    // 模拟并发变化（用于测试实时刷新）
    if (Math.random() > 0.7) {
      simulateConcurrencyChange();
    }

    // 过滤数据
    let filteredKeys = [...mockKeys];
    if (platform && platform !== 'all') {
      filteredKeys = filteredKeys.filter((key) => key.platform === platform);
    }

    // 返回时脱敏密钥
    const result = filteredKeys.map((key) => ({
      ...key,
      key_secret: maskKey(key.key_secret),
    }));

    return HttpResponse.json({
      code: 0,
      message: 'Success',
      data: result,
    });
  }),

  /**
   * 添加密钥
   * POST /api/admin/keys
   */
  http.post('/api/admin/keys', async ({ request }) => {
    try {
      const body = (await request.json()) as AddKeyRequest;
      const { platform, key_secret, max_concurrency = 3, weight = 10 } = body;

      // 参数验证
      if (!platform || !key_secret) {
        return HttpResponse.json(
          {
            code: 400,
            message: '平台和密钥不能为空',
            data: null,
          },
          { status: 400 }
        );
      }

      // 检查密钥是否已存在
      if (mockKeys.find((k) => k.key_secret === key_secret)) {
        return HttpResponse.json(
          {
            code: 400,
            message: '该密钥已存在',
            data: null,
          },
          { status: 400 }
        );
      }

      // 添加密钥
      const newKey = addMockKey(platform, key_secret, max_concurrency, weight);

      return HttpResponse.json({
        code: 0,
        message: 'Key added successfully',
        data: {
          ...newKey,
          key_secret: maskKey(newKey.key_secret),
        },
      });
    } catch (error) {
      return HttpResponse.json(
        {
          code: 500,
          message: '添加密钥失败',
          data: null,
        },
        { status: 500 }
      );
    }
  }),

  /**
   * 批量添加密钥
   * POST /api/admin/keys/batch
   */
  http.post('/api/admin/keys/batch', async ({ request }) => {
    try {
      const body = (await request.json()) as BatchAddKeysRequest;
      const { platform, keys, max_concurrency = 3, weight = 10 } = body;

      // 参数验证
      if (!platform || !keys || keys.length === 0) {
        return HttpResponse.json(
          {
            code: 400,
            message: '平台和密钥列表不能为空',
            data: null,
          },
          { status: 400 }
        );
      }

      if (keys.length > 100) {
        return HttpResponse.json(
          {
            code: 400,
            message: '单次最多导入 100 个密钥',
            data: null,
          },
          { status: 400 }
        );
      }

      // 批量添加
      const result = batchAddMockKeys(platform, keys, max_concurrency, weight);

      return HttpResponse.json({
        code: 0,
        message: 'Batch import completed',
        data: {
          success_count: result.success.length,
          failed_count: result.failed.length,
          failed_keys: result.failed.map(maskKey),
        },
      });
    } catch (error) {
      return HttpResponse.json(
        {
          code: 500,
          message: '批量添加失败',
          data: null,
        },
        { status: 500 }
      );
    }
  }),

  /**
   * 更新密钥配置
   * PATCH /api/admin/keys/{id}
   */
  http.patch('/api/admin/keys/:id', async ({ params, request }) => {
    try {
      const id = parseInt(params.id as string);
      const body = (await request.json()) as UpdateKeyRequest;

      // 查找密钥
      const key = mockKeys.find((k) => k.id === id);
      if (!key) {
        return HttpResponse.json(
          {
            code: 404,
            message: '密钥不存在',
            data: null,
          },
          { status: 404 }
        );
      }

      // 更新配置
      const success = updateMockKey(id, body);

      if (!success) {
        return HttpResponse.json(
          {
            code: 500,
            message: '更新失败',
            data: null,
          },
          { status: 500 }
        );
      }

      return HttpResponse.json({
        code: 0,
        message: 'Key updated successfully',
        data: null,
      });
    } catch (error) {
      return HttpResponse.json(
        {
          code: 500,
          message: '更新密钥失败',
          data: null,
        },
        { status: 500 }
      );
    }
  }),

  /**
   * 删除密钥
   * DELETE /api/admin/keys/{id}
   */
  http.delete('/api/admin/keys/:id', ({ params }) => {
    try {
      const id = parseInt(params.id as string);

      // 查找密钥
      const key = mockKeys.find((k) => k.id === id);
      if (!key) {
        return HttpResponse.json(
          {
            code: 404,
            message: '密钥不存在',
            data: null,
          },
          { status: 404 }
        );
      }

      // 检查是否有正在使用的并发
      if (key.current_usage > 0) {
        return HttpResponse.json(
          {
            code: 400,
            message: `该密钥正在被 ${key.current_usage} 个任务使用，请先等待任务完成或手动停用`,
            data: null,
          },
          { status: 400 }
        );
      }

      // 删除密钥
      const success = deleteMockKey(id);

      if (!success) {
        return HttpResponse.json(
          {
            code: 500,
            message: '删除失败',
            data: null,
          },
          { status: 500 }
        );
      }

      return HttpResponse.json({
        code: 0,
        message: 'Key deleted successfully',
        data: null,
      });
    } catch (error) {
      return HttpResponse.json(
        {
          code: 500,
          message: '删除密钥失败',
          data: null,
        },
        { status: 500 }
      );
    }
  }),

  /**
   * 手动触发/解除熔断
   * POST /api/admin/keys/{id}/cooldown
   */
  http.post('/api/admin/keys/:id/cooldown', async ({ params, request }) => {
    try {
      const id = parseInt(params.id as string);
      const body = (await request.json()) as CooldownRequest;
      const { action, duration = 300 } = body;

      // 查找密钥
      const key = mockKeys.find((k) => k.id === id);
      if (!key) {
        return HttpResponse.json(
          {
            code: 404,
            message: '密钥不存在',
            data: null,
          },
          { status: 404 }
        );
      }

      // 触发/解除熔断
      const success = triggerCooldown(id, action, duration);

      if (!success) {
        return HttpResponse.json(
          {
            code: 500,
            message: '操作失败',
            data: null,
          },
          { status: 500 }
        );
      }

      return HttpResponse.json({
        code: 0,
        message: action === 'trigger' ? 'Cooldown triggered successfully' : 'Cooldown released successfully',
        data: {
          cooling_until: key.cooling_until,
        },
      });
    } catch (error) {
      return HttpResponse.json(
        {
          code: 500,
          message: '熔断控制失败',
          data: null,
        },
        { status: 500 }
      );
    }
  }),

  /**
   * 触发健康检测
   * POST /api/admin/keys/health-check
   */
  http.post('/api/admin/keys/health-check', ({ request }) => {
    const url = new URL(request.url);
    const platform = url.searchParams.get('platform') as Platform | null;

    // 过滤要检测的密钥
    let keysToCheck = [...mockKeys];
    if (platform && platform !== 'all') {
      keysToCheck = keysToCheck.filter((key) => key.platform === platform);
    }

    // 模拟健康检测（随机结果）
    const details = keysToCheck.map((key) => {
      let check_result: 'ok' | 'error' | 'rate_limit' = 'ok';

      // 模拟检测结果
      if (key.is_cooling) {
        check_result = 'rate_limit';
      } else if (Math.random() > 0.9) {
        check_result = 'error';
      }

      return {
        id: key.id,
        platform: key.platform,
        status: key.status,
        is_cooling: key.is_cooling,
        check_result,
      };
    });

    // 统计
    const total = keysToCheck.length;
    const active = details.filter((d) => d.check_result === 'ok' && d.status === 1).length;
    const cooling = details.filter((d) => d.is_cooling).length;
    const disabled = details.filter((d) => d.status === 0).length;

    return HttpResponse.json({
      code: 0,
      message: 'Health check completed',
      data: {
        total,
        active,
        cooling,
        disabled,
        details,
      },
    });
  }),

  /**
   * 获取密钥统计信息
   * GET /api/admin/keys/stats
   */
  http.get('/api/admin/keys/stats', () => {
    // 按平台分组统计（使用动态平台配置）
    const enabledPlatforms = mockPlatforms.filter((p) => p.enabled).map((p) => p.key);
    const byPlatform = enabledPlatforms.map((platform) => {
      const platformKeys = mockKeys.filter((k) => k.platform === platform);
      const activeKeys = platformKeys.filter((k) => k.status === 1 && !k.is_cooling);
      const coolingKeys = platformKeys.filter((k) => k.is_cooling);

      return {
        platform,
        total_keys: platformKeys.length,
        active_keys: activeKeys.length,
        cooling_keys: coolingKeys.length,
        total_concurrency: platformKeys.reduce((sum, k) => sum + k.max_concurrency, 0),
        current_usage: platformKeys.reduce((sum, k) => sum + k.current_usage, 0),
      };
    });

    // 今日统计（模拟）
    const totalCallsToday = mockKeys.reduce((sum, k) => sum + Math.floor(k.total_calls * 0.05), 0);
    const totalErrorsToday = mockKeys.reduce((sum, k) => sum + Math.floor(k.total_errors * 0.05), 0);
    const errorRate = totalCallsToday > 0 ? (totalErrorsToday / totalCallsToday) * 100 : 0;

    return HttpResponse.json({
      code: 0,
      message: 'Success',
      data: {
        by_platform: byPlatform,
        total_calls_today: totalCallsToday,
        total_errors_today: totalErrorsToday,
        error_rate: parseFloat(errorRate.toFixed(2)),
      },
    });
  }),
];
