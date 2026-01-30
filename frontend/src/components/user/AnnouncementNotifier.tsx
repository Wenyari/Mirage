import { Bell, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { Announcement } from '@/types/announcement';

const STORAGE_KEY = 'mirage_last_seen_announcement_id';

interface AnnouncementNotifierProps {
    announcements: Announcement[];
}

/**
 * 公告通知组件
 * 检测是否有新公告，如果有则显示弹窗提示用户
 */
export function AnnouncementNotifier({ announcements }: AnnouncementNotifierProps) {
    const [isVisible, setIsVisible] = useState(false);

    // 从 announcements 中获取最新的公告
    const latestAnnouncement = announcements && announcements.length > 0 ? announcements[0] : null;

    useEffect(() => {
        if (!latestAnnouncement) {
            return;
        }

        // 检查是否已经看过这条公告
        const lastSeenId = localStorage.getItem(STORAGE_KEY);
        const lastSeenIdNum = lastSeenId ? parseInt(lastSeenId, 10) : 0;

        // 如果最新公告ID大于上次看过的ID，说明有新公告
        if (latestAnnouncement.id > lastSeenIdNum) {
            setIsVisible(true);
        }
    }, [latestAnnouncement]);

    const handleClose = () => {
        if (latestAnnouncement) {
            // 记录已经看过这条公告
            localStorage.setItem(STORAGE_KEY, latestAnnouncement.id.toString());
        }
        setIsVisible(false);
    };

    if (!isVisible || !latestAnnouncement) {
        return null;
    }

    const publishDate = new Date(latestAnnouncement.publish_time);
    const formattedDate = publishDate.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
    });

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
            <Card className="relative w-full max-w-lg animate-in fade-in zoom-in-95 duration-300">
                {/* 关闭按钮 */}
                <Button
                    variant="ghost"
                    size="icon"
                    className="absolute right-2 top-2 size-8 rounded-full hover:bg-muted"
                    onClick={handleClose}
                >
                    <X className="size-4" />
                </Button>

                <CardHeader>
                    <div className="flex items-start gap-3">
                        <div className="rounded-full bg-primary/10 p-2">
                            <Bell className="size-5 text-primary" />
                        </div>
                        <div className="flex-1">
                            <CardTitle className="text-lg">最新更新</CardTitle>
                            <p className="mt-1 text-sm text-muted-foreground">{formattedDate}</p>
                        </div>
                    </div>
                </CardHeader>

                <CardContent className="space-y-4">
                    {/* 公告标题 */}
                    <div>
                        <h3 className="mb-2 text-base font-semibold">{latestAnnouncement.title}</h3>
                        {/* 公告内容 */}
                        <div className="max-h-[300px] overflow-y-auto whitespace-pre-wrap text-sm leading-relaxed text-muted-foreground">
                            {latestAnnouncement.content}
                        </div>
                    </div>

                    {/* 操作按钮 */}
                    <div className="flex gap-2">
                        <Link to="/more/updates" className="flex-1" onClick={handleClose}>
                            <Button className="w-full" variant="default">
                                查看所有更新
                            </Button>
                        </Link>
                        <Button className="flex-1" variant="outline" onClick={handleClose}>
                            我知道了
                        </Button>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}

/**
 * 标记所有公告为已读
 */
export function markAllAnnouncementsAsRead(announcements: Announcement[]) {
    if (announcements && announcements.length > 0) {
        const latestId = announcements[0].id;
        localStorage.setItem(STORAGE_KEY, latestId.toString());
    }
}
