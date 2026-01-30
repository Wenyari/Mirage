// 公告相关类型定义

/**
 * 公告信息
 */
export interface Announcement {
    id: number;
    title: string;
    content: string;
    publish_time: string;
    is_active: boolean;
    created_at: string;
    updated_at: string;
}

/**
 * 公告列表响应
 */
export interface AnnouncementListResponse {
    code: number;
    message: string;
    data: Announcement[];
}
