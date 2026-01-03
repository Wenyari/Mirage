export interface DashboardOverview {
    today_new_users: number;
    today_points_consumed: number;
    today_cdk_recharge: number;
    active_tasks: number;
}
export interface ChartDataPoint {
    date: string;
    new_users: number;
    points_consumed: number;
    cdk_recharge: number;
}
export interface ChartQueryParams {
    days?: '7' | '30';
}
