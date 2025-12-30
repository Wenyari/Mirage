import { useQuery } from '@tanstack/react-query';
import { getDashboardOverview, getChartData } from '@/services/admin/dashboard';

// 获取仪表盘总览数据
export function useDashboardOverview() {
  return useQuery({
    queryKey: ['admin', 'dashboard', 'overview'],
    queryFn: getDashboardOverview,
  });
}

// 获取趋势图数据
export function useChartData(days: '7' | '30' = '7') {
  return useQuery({
    queryKey: ['admin', 'dashboard', 'chart', days],
    queryFn: () => getChartData(days),
  });
}
