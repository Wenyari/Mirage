import api from '@/lib/api';
import type { ApiResponse, ChartDataPoint,DashboardOverview } from '@/types';

// 获取仪表盘总览数据
export async function getDashboardOverview(): Promise<DashboardOverview> {
  const response = await api.get<ApiResponse<DashboardOverview>>('/admin/stats/overview');
  return response.data;
}

// 获取趋势图数据
export async function getChartData(days: '7' | '30' = '7'): Promise<ChartDataPoint[]> {
  const response = await api.get<ApiResponse<ChartDataPoint[]>>('/admin/stats/chart', {
    params: { days },
  });
  return response.data;
}
