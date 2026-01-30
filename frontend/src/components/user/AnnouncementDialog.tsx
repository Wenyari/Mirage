import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2 } from 'lucide-react';
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import * as z from 'zod';

import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import type { Announcement } from '@/types/announcement';

const announcementSchema = z.object({
    title: z.string().min(1, '标题不能为空').max(200, '标题不能超过200字符'),
    content: z.string().min(1, '内容不能为空'),
    publish_time: z.string().min(1, '发布时间不能为空'),
    is_active: z.boolean().default(true),
});

type AnnouncementFormData = z.infer<typeof announcementSchema>;

interface AnnouncementDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    announcement?: Announcement;
    onSubmit: (data: AnnouncementFormData) => Promise<void>;
    isLoading?: boolean;
}

export function AnnouncementDialog({
    open,
    onOpenChange,
    announcement,
    onSubmit,
    isLoading = false,
}: AnnouncementDialogProps) {
    const form = useForm<AnnouncementFormData>({
        resolver: zodResolver(announcementSchema),
        defaultValues: {
            title: '',
            content: '',
            publish_time: new Date().toISOString().slice(0, 16),
            is_active: true,
        },
    });

    // 当announcement变化时更新表单
    useEffect(() => {
        if (announcement) {
            form.reset({
                title: announcement.title,
                content: announcement.content,
                publish_time: announcement.publish_time.slice(0, 16),
                is_active: announcement.is_active,
            });
        } else {
            form.reset({
                title: '',
                content: '',
                publish_time: new Date().toISOString().slice(0, 16),
                is_active: true,
            });
        }
    }, [announcement, form]);

    const handleSubmit = async (data: AnnouncementFormData) => {
        await onSubmit(data);
        form.reset();
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-2xl">
                <DialogHeader>
                    <DialogTitle>{announcement ? '编辑公告' : '创建公告'}</DialogTitle>
                </DialogHeader>

                <Form {...form}>
                    <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
                        {/* 标题 */}
                        <FormField
                            control={form.control}
                            name="title"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>标题</FormLabel>
                                    <FormControl>
                                        <Input placeholder="输入公告标题" {...field} />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        {/* 内容 */}
                        <FormField
                            control={form.control}
                            name="content"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>内容</FormLabel>
                                    <FormControl>
                                        <Textarea
                                            placeholder="输入公告内容"
                                            className="min-h-[200px]"
                                            {...field}
                                        />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        {/* 发布时间 */}
                        <FormField
                            control={form.control}
                            name="publish_time"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>发布时间</FormLabel>
                                    <FormControl>
                                        <Input type="datetime-local" {...field} />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        {/* 启用状态 */}
                        <FormField
                            control={form.control}
                            name="is_active"
                            render={({ field }) => (
                                <FormItem className="flex items-center justify-between rounded-lg border p-4">
                                    <div className="space-y-0.5">
                                        <FormLabel className="text-base">启用状态</FormLabel>
                                        <div className="text-sm text-muted-foreground">
                                            启用后用户可以看到此公告
                                        </div>
                                    </div>
                                    <FormControl>
                                        <Switch checked={field.value} onCheckedChange={field.onChange} />
                                    </FormControl>
                                </FormItem>
                            )}
                        />

                        {/* 提交按钮 */}
                        <div className="flex justify-end gap-2">
                            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                                取消
                            </Button>
                            <Button type="submit" disabled={isLoading}>
                                {isLoading && <Loader2 className="mr-2 size-4 animate-spin" />}
                                {announcement ? '更新' : '创建'}
                            </Button>
                        </div>
                    </form>
                </Form>
            </DialogContent>
        </Dialog>
    );
}
