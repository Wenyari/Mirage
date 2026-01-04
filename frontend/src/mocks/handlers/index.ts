import { http, HttpResponse } from 'msw';

import { cdkHandlers } from './cdk';
import { dashboardHandlers } from './dashboard';
import { keysHandlers } from './keys';
import { modelConfigHandlers } from './modelConfigs';
import { usersHandlers } from './users';

// 这是初始的 handlers，后续会根据需要添加更多的 handlers
export const handlers = [
  // 健康检查接口
  http.get('/api/health', () => {
    return HttpResponse.json({
      code: 0,
      message: 'OK',
      data: {
        status: 'healthy',
        timestamp: new Date().toISOString(),
      },
    });
  }),

  // Dashboard handlers
  ...dashboardHandlers,

  // Users handlers
  ...usersHandlers,

  // CDK handlers
  ...cdkHandlers,

  // Keys handlers
  ...keysHandlers,

  // Model Config handlers
  ...modelConfigHandlers,
];
