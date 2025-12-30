// Dashboard 相关类型定义

// 仪表盘总览数据
export interface DashboardOverview {
  today_new_users: number;
  today_token_usage: number;
  estimated_revenue: number;
  active_tasks: number;
}

// 趋势图数据点
export interface ChartDataPoint {
  date: string;
  new_users: number;
  token_usage: number;
  revenue: number;
}

// 趋势图查询参数
export interface ChartQueryParams {
  days?: '7' | '30';
}
