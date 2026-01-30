import { Calendar, Clock } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import type { Announcement } from '@/types/announcement';
import { cn } from '@/lib/utils';

interface AnnouncementTimelineProps {
    announcements: Announcement[];
}

export function AnnouncementTimeline({ announcements }: AnnouncementTimelineProps) {
    if (!announcements || announcements.length === 0) {
        return (
            <div className="flex min-h-[400px] items-center justify-center">
                <p className="text-muted-foreground">暂无公告</p>
            </div>
        );
    }

    return (
        <div className="relative mx-auto max-w-4xl py-8">
            {/* 垂直时间线 */}
            <div className="absolute left-1/2 top-0 h-full w-0.5 -translate-x-1/2 bg-gradient-to-b from-primary/20 via-primary/10 to-transparent" />

            <div className="space-y-12">
                {announcements.map((announcement, index) => {
                    const isLeft = index % 2 === 0;
                    const isLatest = index === 0;
                    const publishDate = new Date(announcement.publish_time);
                    const formattedDate = publishDate.toLocaleDateString('zh-CN', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                    });
                    const formattedTime = publishDate.toLocaleTimeString('zh-CN', {
                        hour: '2-digit',
                        minute: '2-digit',
                    });

                    return (
                        <div
                            key={announcement.id}
                            className={cn(
                                'relative flex items-center',
                                isLeft ? 'justify-start' : 'justify-end'
                            )}
                        >
                            {/* 时间线节点 */}
                            <div className="absolute left-1/2 z-10 -translate-x-1/2">
                                <div
                                    className={cn(
                                        'flex size-4 items-center justify-center rounded-full border-4 border-background',
                                        isLatest
                                            ? 'animate-pulse bg-gradient-to-br from-primary to-primary/60 shadow-lg shadow-primary/50'
                                            : 'bg-primary/30'
                                    )}
                                >
                                    {isLatest && (
                                        <div className="absolute size-6 animate-ping rounded-full bg-primary/20" />
                                    )}
                                </div>
                            </div>

                            {/* 公告卡片 */}
                            <div className={cn('w-[calc(50%-2rem)]', isLeft ? 'pr-8' : 'pl-8')}>
                                <Card
                                    className={cn(
                                        'group relative overflow-hidden transition-all duration-300 hover:shadow-lg',
                                        isLatest &&
                                        'border-primary/50 bg-gradient-to-br from-primary/5 via-background to-background shadow-md shadow-primary/10'
                                    )}
                                >
                                    {isLatest && (
                                        <div className="absolute right-0 top-0">
                                            <div className="relative">
                                                <div className="h-0 w-0 border-b-[60px] border-l-[60px] border-b-transparent border-l-primary/10" />
                                                <span className="absolute right-1 top-1 rotate-[-45deg] text-[10px] font-bold text-primary">
                                                    NEW
                                                </span>
                                            </div>
                                        </div>
                                    )}

                                    <CardContent className="p-6">
                                        {/* 日期标签 */}
                                        <div className="mb-3 flex items-center gap-4 text-sm text-muted-foreground">
                                            <div className="flex items-center gap-1.5">
                                                <Calendar className="size-4" />
                                                <span>{formattedDate}</span>
                                            </div>
                                            <div className="flex items-center gap-1.5">
                                                <Clock className="size-4" />
                                                <span>{formattedTime}</span>
                                            </div>
                                        </div>

                                        {/* 标题 */}
                                        <h3
                                            className={cn(
                                                'mb-3 text-lg font-semibold transition-colors group-hover:text-primary',
                                                isLatest && 'text-primary'
                                            )}
                                        >
                                            {announcement.title}
                                        </h3>

                                        {/* 内容 */}
                                        <div className="whitespace-pre-wrap text-sm leading-relaxed text-muted-foreground">
                                            {announcement.content}
                                        </div>
                                    </CardContent>
                                </Card>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
