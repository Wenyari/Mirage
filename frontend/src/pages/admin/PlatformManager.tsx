import { useState } from 'react';
import { Edit, Trash2, Plus, MoreVertical } from 'lucide-react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
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
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

import type { PlatformConfig } from '@/types/key';
import { usePlatforms, useUpdatePlatform, useDeletePlatform } from '@/hooks/useKeys';
import { CreatePlatformDialog } from '@/components/admin/CreatePlatformDialog';
import { EditPlatformDialog } from '@/components/admin/EditPlatformDialog';

export default function PlatformManager() {
  const [deleteDialog, setDeleteDialog] = useState<{ open: boolean; platform?: PlatformConfig }>({
    open: false,
  });
  const [editDialog, setEditDialog] = useState<{ open: boolean; platform?: PlatformConfig }>({
    open: false,
  });
  const [createDialog, setCreateDialog] = useState(false);

  const { data, isLoading, isError, error } = usePlatforms();
  const updateMutation = useUpdatePlatform();
  const deleteMutation = useDeletePlatform();

  // 切换启用状态
  const handleToggleEnabled = async (platform: PlatformConfig) => {
    try {
      await updateMutation.mutateAsync({
        key: platform.key,
        data: { enabled: !platform.enabled },
      });
      toast.success(platform.enabled ? '平台已禁用' : '平台已启用');
    } catch (err: any) {
      toast.error(err.message || '操作失败');
    }
  };

  // 删除平台
  const handleDelete = async () => {
    if (!deleteDialog.platform) return;

    try {
      await deleteMutation.mutateAsync(deleteDialog.platform.key);
      toast.success('平台已删除');
      setDeleteDialog({ open: false });
    } catch (err: any) {
      toast.error(err.message || '删除失败');
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (isError) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>{(error as any)?.message || '加载失败'}</AlertDescription>
      </Alert>
    );
  }

  const platforms = data?.data || [];

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">平台管理</h1>
        <p className="mt-2 text-muted-foreground">
          管理所有AI平台配置，包括平台信息、图标和并发限制
        </p>
      </div>

      {/* 操作栏 */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-semibold">平台列表</h2>
          <p className="text-sm text-muted-foreground mt-1">共 {platforms.length} 个平台</p>
        </div>
        <Button onClick={() => setCreateDialog(true)}>
          <Plus className="mr-2 h-4 w-4" />
          添加平台
        </Button>
      </div>

      {/* 平台列表表格 */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>平台</TableHead>
              <TableHead>描述</TableHead>
              <TableHead>图标</TableHead>
              <TableHead>颜色</TableHead>
              <TableHead>并发限制</TableHead>
              <TableHead>状态</TableHead>
              <TableHead>操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {platforms.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="h-24 text-center">
                  暂无平台数据
                </TableCell>
              </TableRow>
            ) : (
              platforms.map((platform) => (
                <TableRow key={platform.key}>
                  <TableCell>
                    <div className="flex flex-col gap-1">
                      <span className="font-medium">{platform.name}</span>
                      <code className="text-xs text-muted-foreground">{platform.key}</code>
                    </div>
                  </TableCell>
                  <TableCell>
                    <span className="text-sm text-muted-foreground">
                      {platform.description || '-'}
                    </span>
                  </TableCell>
                  <TableCell>
                    {platform.icon_url || platform.icon ? (
                      <img
                        src={platform.icon_url || platform.icon}
                        alt={platform.name}
                        className="h-8 w-8 object-contain"
                        onError={(e) => {
                          e.currentTarget.style.display = 'none';
                        }}
                      />
                    ) : (
                      <span className="text-xs text-muted-foreground">无</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {platform.color ? (
                      <Badge className={platform.color}>{platform.color}</Badge>
                    ) : (
                      <span className="text-xs text-muted-foreground">-</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <span className="text-sm">
                      {platform.max_concurrency_limit || '-'}
                    </span>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Switch
                        checked={platform.enabled}
                        onCheckedChange={() => handleToggleEnabled(platform)}
                        disabled={updateMutation.isPending}
                      />
                      <span className="text-sm">
                        {platform.enabled ? '启用' : '禁用'}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          onClick={() => setEditDialog({ open: true, platform })}
                        >
                          <Edit className="h-4 w-4 mr-2" />
                          编辑
                        </DropdownMenuItem>

                        <DropdownMenuSeparator />

                        <DropdownMenuItem
                          className="text-red-600"
                          onClick={() => setDeleteDialog({ open: true, platform })}
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          删除
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* 创建对话框 */}
      <CreatePlatformDialog open={createDialog} onOpenChange={setCreateDialog} />

      {/* 编辑对话框 */}
      <EditPlatformDialog
        open={editDialog.open}
        onOpenChange={(open) => setEditDialog({ open })}
        platform={editDialog.platform}
      />

      {/* 删除确认对话框 */}
      <AlertDialog open={deleteDialog.open} onOpenChange={(open) => setDeleteDialog({ open })}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认删除</AlertDialogTitle>
            <AlertDialogDescription>
              确定要删除平台 "{deleteDialog.platform?.name}" 吗？
              <br />
              注意：只有当该平台没有关联的密钥和任务时才能删除。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-red-600 hover:bg-red-700">
              确认删除
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
