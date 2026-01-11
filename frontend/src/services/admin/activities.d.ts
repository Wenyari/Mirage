export interface Activity {
    id: number;
    code: string;
    name: string;
    description: string;
    points: number;
    expire_days: number | null;
    max_claims_per_user: number;
    required_level: number;
    start_at: string | null;
    end_at: string | null;
    status: 'active' | 'paused' | 'ended';
    created_at: string;
}
export interface ActivityStats {
    activity_id: number;
    total_claims: number;
    unique_users: number;
    total_points_granted: number;
    active_claims: number;
    expired_claims: number;
    used_claims: number;
}
export interface CheckinConfig {
    id: number;
    day: number;
    points: number;
    is_active: boolean;
}
export declare const getActivities: (params: {
    page: number;
    size: number;
    status?: string;
}) => Promise<import("axios").AxiosResponse<any, any, {}>>;
export declare const createActivity: (data: Partial<Activity>) => Promise<import("axios").AxiosResponse<any, any, {}>>;
export declare const updateActivity: (id: number, data: Partial<Activity>) => Promise<import("axios").AxiosResponse<any, any, {}>>;
export declare const deleteActivity: (id: number) => Promise<import("axios").AxiosResponse<any, any, {}>>;
export declare const getActivityStats: (id: number) => Promise<import("axios").AxiosResponse<any, any, {}>>;
export declare const getCheckinConfig: () => Promise<import("axios").AxiosResponse<any, any, {}>>;
export declare const updateCheckinConfig: (configs: Partial<CheckinConfig>[]) => Promise<import("axios").AxiosResponse<any, any, {}>>;
