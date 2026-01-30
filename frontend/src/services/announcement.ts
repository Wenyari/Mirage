import api from '@/lib/api';
import type { AnnouncementListResponse } from '@/types/announcement';

/**
 * 获取公告列表（用户端）
 * @param limit 返回的最大数量（默认10，最大50）
 */
export async function getAnnouncements(limit = 10): Promise<AnnouncementListResponse> {
    const response = await api.get('/announcements', { params: { limit } });
    return response.data;
}
