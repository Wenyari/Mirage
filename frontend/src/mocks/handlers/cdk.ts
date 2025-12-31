import { http, HttpResponse } from 'msw';
import type { CDKGenerateRequest, CDKVoidRequest } from '@/types/cdk';
import {
  mockCDKList,
  generateMockCDKs,
  addCDKsToList,
  voidCDKsByIds,
  voidCDKsByBatchNo,
} from '../data/cdk';

/**
 * CDK 管理相关的 Mock 处理器
 */
export const cdkHandlers = [
  /**
   * 生成 CDK
   * POST /api/admin/cdk/generate
   */
  http.post('/api/admin/cdk/generate', async ({ request }) => {
    try {
      const body = (await request.json()) as CDKGenerateRequest;
      const { points, type, count, batch_no, expire_at } = body;

      // 参数验证
      if (!points || points <= 0) {
        return HttpResponse.json(
          {
            success: false,
            message: '积分面额必须大于0',
          },
          { status: 400 }
        );
      }

      if (!count || count <= 0 || count > 1000) {
        return HttpResponse.json(
          {
            success: false,
            message: '生成数量必须在1-1000之间',
          },
          { status: 400 }
        );
      }

      // 生成批次号（如果未提供）
      const finalBatchNo = batch_no || `BATCH-${Date.now()}`;

      // 生成 CDK
      const newCDKs = generateMockCDKs(count, points, type, finalBatchNo, expire_at);

      // 添加到列表
      addCDKsToList(newCDKs);

      // 返回生成的兑换码列表
      return HttpResponse.json({
        success: true,
        data: {
          codes: newCDKs.map((cdk) => cdk.code),
          batch_no: finalBatchNo,
        },
      });
    } catch (error) {
      return HttpResponse.json(
        {
          success: false,
          message: '生成 CDK 失败',
        },
        { status: 500 }
      );
    }
  }),

  /**
   * 获取 CDK 列表
   * GET /api/admin/cdk
   */
  http.get('/api/admin/cdk', ({ request }) => {
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const pageSize = parseInt(url.searchParams.get('page_size') || '10');
    const type = url.searchParams.get('type') as 'once' | 'universal' | null;
    const status = url.searchParams.get('status');
    const batchNo = url.searchParams.get('batch_no');
    const search = url.searchParams.get('search');

    // 过滤数据
    let filteredList = [...mockCDKList];

    if (type) {
      filteredList = filteredList.filter((cdk) => cdk.type === type);
    }

    if (status !== null && status !== undefined && status !== '') {
      const statusNum = parseInt(status) as 0 | 1 | 2;
      filteredList = filteredList.filter((cdk) => cdk.status === statusNum);
    }

    if (batchNo) {
      filteredList = filteredList.filter((cdk) => cdk.batch_no === batchNo);
    }

    if (search) {
      filteredList = filteredList.filter(
        (cdk) =>
          cdk.code.toLowerCase().includes(search.toLowerCase()) ||
          cdk.batch_no?.toLowerCase().includes(search.toLowerCase())
      );
    }

    // 分页
    const total = filteredList.length;
    const start = (page - 1) * pageSize;
    const end = start + pageSize;
    const paginatedList = filteredList.slice(start, end);

    return HttpResponse.json({
      success: true,
      data: paginatedList,
      total,
      page,
      page_size: pageSize,
    });
  }),

  /**
   * 作废 CDK
   * POST /api/admin/cdk/void
   */
  http.post('/api/admin/cdk/void', async ({ request }) => {
    try {
      const body = (await request.json()) as CDKVoidRequest;
      const { ids, batch_no } = body;

      if (!ids && !batch_no) {
        return HttpResponse.json(
          {
            success: false,
            message: '必须提供要作废的 CDK ID 列表或批次号',
          },
          { status: 400 }
        );
      }

      // 按 ID 作废
      if (ids && ids.length > 0) {
        voidCDKsByIds(ids);
      }

      // 按批次号作废
      if (batch_no) {
        voidCDKsByBatchNo(batch_no);
      }

      return HttpResponse.json({
        success: true,
        message: '作废成功',
      });
    } catch (error) {
      return HttpResponse.json(
        {
          success: false,
          message: '作废 CDK 失败',
        },
        { status: 500 }
      );
    }
  }),

  /**
   * 获取批次列表（用于筛选）
   * GET /api/admin/cdk/batches
   */
  http.get('/api/admin/cdk/batches', () => {
    // 提取所有唯一的批次号
    const batches = [...new Set(mockCDKList.map((cdk) => cdk.batch_no).filter(Boolean))];

    return HttpResponse.json({
      success: true,
      data: batches,
    });
  }),
];
