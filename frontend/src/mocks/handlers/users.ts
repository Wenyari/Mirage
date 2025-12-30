import { http, HttpResponse } from 'msw';

import type { User } from '@/types/user';

import { mockUsers } from '../data/users';

// 用于存储运行时的用户数据（支持修改）
const runtimeUsers = [...mockUsers];

export const usersHandlers = [
  // GET /api/admin/users - 获取用户列表（支持分页、搜索、筛选）
  http.get('/api/admin/users', ({ request }) => {
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const limit = parseInt(url.searchParams.get('limit') || '10');
    const email = url.searchParams.get('email') || '';
    const levelParam = url.searchParams.get('level');
    const statusParam = url.searchParams.get('status');

    // 筛选
    const filtered = runtimeUsers.filter((user) => {
      const matchEmail = email ? user.email.toLowerCase().includes(email.toLowerCase()) : true;
      const matchLevel = levelParam ? user.level === parseInt(levelParam) : true;
      const matchStatus = statusParam !== null ? user.status === parseInt(statusParam) : true;
      return matchEmail && matchLevel && matchStatus;
    });

    // 排序（最新注册的在前）
    filtered.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

    const total = filtered.length;
    const start = (page - 1) * limit;
    const items = filtered.slice(start, start + limit);

    // 模拟延迟
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve(
          HttpResponse.json({
            code: 0,
            message: 'Success',
            data: {
              items,
              total,
              page,
              limit,
            },
          })
        );
      }, 500);
    });
  }),

  // PATCH /api/admin/users/:id/balance - 人工充值/扣费
  http.patch('/api/admin/users/:id/balance', async ({ params, request }) => {
    const userId = parseInt(params.id as string);
    const body = (await request.json()) as { amount: number; reason: string };

    const userIndex = runtimeUsers.findIndex((u) => u.id === userId);
    if (userIndex === -1) {
      return HttpResponse.json(
        {
          code: 404,
          message: 'User not found',
          data: null,
        },
        { status: 404 }
      );
    }

    // 更新余额
    const oldBalance = runtimeUsers[userIndex].balance;
    const newBalance = oldBalance + body.amount;

    if (newBalance < 0) {
      return HttpResponse.json(
        {
          code: 400,
          message: 'Insufficient balance',
          data: null,
        },
        { status: 400 }
      );
    }

    runtimeUsers[userIndex].balance = newBalance;

    return new Promise((resolve) => {
      setTimeout(() => {
        resolve(
          HttpResponse.json({
            code: 0,
            message: 'Balance updated successfully',
            data: {
              new_balance: newBalance,
            },
          })
        );
      }, 500);
    });
  }),

  // PATCH /api/admin/users/:id/profile - 修改用户资料
  http.patch('/api/admin/users/:id/profile', async ({ params, request }) => {
    const userId = parseInt(params.id as string);
    const body = (await request.json()) as { level?: number; status?: number };

    const userIndex = runtimeUsers.findIndex((u) => u.id === userId);
    if (userIndex === -1) {
      return HttpResponse.json(
        {
          code: 404,
          message: 'User not found',
          data: null,
        },
        { status: 404 }
      );
    }

    // 更新用户资料
    if (body.level !== undefined) {
      runtimeUsers[userIndex].level = body.level as 1 | 2 | 3 | 4 | 5;
    }
    if (body.status !== undefined) {
      runtimeUsers[userIndex].status = body.status as 0 | 1;
    }

    return new Promise((resolve) => {
      setTimeout(() => {
        resolve(
          HttpResponse.json({
            code: 0,
            message: 'User profile updated successfully',
            data: null,
          })
        );
      }, 500);
    });
  }),
];
