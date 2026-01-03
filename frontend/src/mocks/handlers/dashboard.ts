import { http, HttpResponse, passthrough } from 'msw';

import { mockChart7Days, mockChart30Days,mockDashboardOverview } from '../data/stats';

export const dashboardHandlers = [
  // GET /api/admin/stats/overview - 获取核心指标
  http.get('/api/admin/stats/overview', () => {
    return passthrough();
    // return HttpResponse.json({
    //   code: 0,
    //   message: 'Success',
    //   data: mockDashboardOverview,
    // });
  }),

  // GET /api/admin/stats/chart - 获取趋势数据
  http.get('/api/admin/stats/chart', ({ request }) => {
    return passthrough();
    // const url = new URL(request.url);
    // const days = url.searchParams.get('days') || '7';

    // const chartData = days === '30' ? mockChart30Days : mockChart7Days;

    // return HttpResponse.json({
    //   code: 0,
    //   message: 'Success',
    //   data: chartData,
    // });
  }),
];
