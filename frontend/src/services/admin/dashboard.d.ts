import type { ChartDataPoint, DashboardOverview } from '@/types';
export declare function getDashboardOverview(): Promise<DashboardOverview>;
export declare function getChartData(days?: '7' | '30'): Promise<ChartDataPoint[]>;
