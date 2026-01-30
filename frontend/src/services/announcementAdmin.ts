import api from '@/lib/api';

export interface CreateAnnouncementRequest {
    title: string;
    content: string;
    publish_time: string;
    is_active: boolean;
}

export interface UpdateAnnouncementRequest {
    title?: string;
    content?: string;
    publish_time?: string;
    is_active?: boolean;
}

/**
 * 创建公告（管理员）
 */
export async function createAnnouncement(data: CreateAnnouncementRequest) {
    const response = await api.post('/admin/announcements', data);
    return response.data;
}

/**
 * 更新公告（管理员）
 */
export async function updateAnnouncement(id: number, data: UpdateAnnouncementRequest) {
    const response = await api.put(`/admin/announcements/${id}`, data);
    return response.data;
}

/**
 * 删除公告（管理员）
 */
export async function deleteAnnouncement(id: number) {
    const response = await api.delete(`/admin/announcements/${id}`);
    return response.data;
}
