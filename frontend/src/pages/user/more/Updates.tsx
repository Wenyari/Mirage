import { Edit, Loader2, Plus, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { toast } from 'sonner';

import { AnnouncementDialog } from '@/components/user/AnnouncementDialog';
import { AnnouncementTimeline } from '@/components/user/AnnouncementTimeline';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { getAnnouncements } from '@/services/announcement';
import {
  createAnnouncement,
  deleteAnnouncement,
  updateAnnouncement,
} from '@/services/announcementAdmin';
import { useAuthStore } from '@/store/authStore';
import type { Announcement } from '@/types/announcement';

export default function Updates() {
  const { user, isAuthenticated } = useAuthStore();
  const isAdmin = isAuthenticated && user?.role === 'admin';

  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [loading, setLoading] = useState(true);

  // Dialog状态
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingAnnouncement, setEditingAnnouncement] = useState<Announcement | undefined>();
  const [submitting, setSubmitting] = useState(false);

  // 删除确认对话框
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [deleting, setDeleting] = useState(false);

  // 获取公告列表
  const fetchAnnouncements = async () => {
    try {
      setLoading(true);
      const response = await getAnnouncements(20);
      if ((response as unknown as Announcement[]).length > 0) {
        setAnnouncements(response as unknown as Announcement[]);
      } else {
        setAnnouncements([]);
      }
    } catch (error) {
      console.error('Failed to fetch announcements:', error);
      toast.error('获取公告失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnnouncements();
  }, []);

  // 处理创建
  const handleCreate = () => {
    setEditingAnnouncement(undefined);
    setDialogOpen(true);
  };

  // 处理编辑
  const handleEdit = (announcement: Announcement) => {
    setEditingAnnouncement(announcement);
    setDialogOpen(true);
  };

  // 处理删除点击
  const handleDeleteClick = (id: number) => {
    setDeletingId(id);
    setDeleteDialogOpen(true);
  };

  // 确认删除
  const confirmDelete = async () => {
    if (!deletingId) return;

    try {
      setDeleting(true);
      await deleteAnnouncement(deletingId);
      toast.success('删除成功');
      setDeleteDialogOpen(false);
      setDeletingId(null);
      // 刷新列表
      await fetchAnnouncements();
    } catch (error: any) {
      toast.error(error.response?.data?.message || '删除失败');
    } finally {
      setDeleting(false);
    }
  };

  // 处理表单提交
  const handleSubmit = async (formData: any) => {
    try {
      setSubmitting(true);
      if (editingAnnouncement) {
        // 更新
        await updateAnnouncement(editingAnnouncement.id, formData);
        toast.success('更新成功');
      } else {
        // 创建
        await createAnnouncement(formData);
        toast.success('创建成功');
      }
      setDialogOpen(false);
      setEditingAnnouncement(undefined);
      // 刷新列表
      await fetchAnnouncements();
    } catch (error: any) {
      toast.error(error.response?.data?.message || '操作失败');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {/* 页面头部 */}
      <div className="mb-8 flex items-center justify-between">
        <div className="text-center flex-1">
          <h1 className="mb-2 text-3xl font-bold">最新更新</h1>
          <p className="text-muted-foreground">了解我们的最新动态和功能更新</p>
        </div>
        {isAdmin && (
          <Button onClick={handleCreate}>
            <Plus className="mr-2 size-4" />
            创建公告
          </Button>
        )}
      </div>

      {loading ? (
        <div className="flex min-h-[400px] items-center justify-center">
          <Loader2 className="size-8 animate-spin text-primary" />
        </div>
      ) : isAdmin ? (
        // 管理员视图：带编辑按钮的卡片列表
        <div className="mx-auto max-w-4xl space-y-4">
          {announcements.length === 0 ? (
            <div className="flex min-h-[400px] items-center justify-center">
              <p className="text-muted-foreground">暂无公告</p>
            </div>
          ) : (
            announcements.map((announcement) => {
              const publishDate = new Date(announcement.publish_time);
              const formattedDate = publishDate.toLocaleDateString('zh-CN', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
              });

              return (
                <Card key={announcement.id}>
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center gap-2">
                          <h3 className="text-lg font-semibold">{announcement.title}</h3>
                          {!announcement.is_active && (
                            <span className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                              已禁用
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground">{formattedDate}</p>
                        <p className="whitespace-pre-wrap text-sm leading-relaxed">
                          {announcement.content}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="icon"
                          onClick={() => handleEdit(announcement)}
                        >
                          <Edit className="size-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="icon"
                          onClick={() => handleDeleteClick(announcement.id)}
                        >
                          <Trash2 className="size-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })
          )}
        </div>
      ) : (
        // 普通用户视图：时间线
        <AnnouncementTimeline announcements={announcements} />
      )}

      {/* 创建/编辑对话框 */}
      <AnnouncementDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        announcement={editingAnnouncement}
        onSubmit={handleSubmit}
        isLoading={submitting}
      />

      {/* 删除确认对话框 */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认删除</AlertDialogTitle>
            <AlertDialogDescription>
              此操作将永久删除该公告，无法恢复。确定要继续吗？
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deleting ? '删除中...' : '确认删除'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
