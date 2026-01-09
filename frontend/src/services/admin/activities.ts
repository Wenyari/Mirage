import api from '@/lib/api';

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

export const getActivities = async (params: { page: number; size: number; status?: string }) => {
    return api.get('/admin/activities', { params });
};

export const createActivity = async (data: Partial<Activity>) => {
    return api.post('/admin/activities', data);
};

export const updateActivity = async (id: number, data: Partial<Activity>) => {
    return api.put(`/admin/activities/${id}`, data);
};

export const deleteActivity = async (id: number) => {
    return api.delete(`/admin/activities/${id}`);
};

export const getActivityStats = async (id: number) => {
    return api.get(`/admin/activities/${id}/stats`);
};

export const getCheckinConfig = async () => {
    return api.get('/admin/checkin/config');
};

export const updateCheckinConfig = async (configs: Partial<CheckinConfig>[]) => {
    return api.put('/admin/checkin/config', { configs });
};
