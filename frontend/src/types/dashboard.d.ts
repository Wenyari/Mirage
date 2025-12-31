export interface DashboardOverview {
    today_new_users: number;
    today_token_usage: number;
    estimated_revenue: number;
    active_tasks: number;
}
export interface ChartDataPoint {
    date: string;
    new_users: number;
    token_usage: number;
    revenue: number;
}
export interface ChartQueryParams {
    days?: '7' | '30';
}
