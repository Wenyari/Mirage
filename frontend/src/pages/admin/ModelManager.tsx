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

import type { Model } from '@/types/key';
import { useModels, useUpdateModel, useDeleteModel } from '@/hooks/useKeys';
import { CreateModelDialog } from '@/components/admin/CreateModelDialog';
import { EditModelDialog } from '@/components/admin/EditModelDialog';

export default function ModelManager() {
  const [deleteDialog, setDeleteDialog] = useState<{ open: boolean; model?: Model }>({
    open: false,
  });
  const [editDialog, setEditDialog] = useState<{ open: boolean; model?: Model }>({
    open: false,
  });
  const [createDialog, setCreateDialog] = useState(false);

  const { data, isLoading, isError, error } = useModels();
  const updateMutation = useUpdateModel();
  const deleteMutation = useDeleteModel();

  // 切换启用状态
  const handleToggleEnabled = async (model: Model) => {
    try {
      await updateMutation.mutateAsync({
        key: model.key,
        data: { enabled: !model.enabled },
      });
      toast.success(model.enabled ? '模型已禁用' : '模型已启用');
    } catch (err: any) {
      toast.error(err.message || '操作失败');
    }
  };

  // 删除模型
  const handleDelete = async () => {
    if (!deleteDialog.model) return;

    try {
      await deleteMutation.mutateAsync(deleteDialog.model.key);
      toast.success('模型已删除');
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

  const models = data?.data || [];

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">模型管理</h1>
        <p className="mt-2 text-muted-foreground">
          管理所有AI模型配置，包括模型信息、图标和并发限制
        </p>
      </div>

      {/* 操作栏 */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-semibold">模型列表</h2>
          <p className="text-sm text-muted-foreground mt-1">共 {models.length} 个模型</p>
        </div>
        <Button onClick={() => setCreateDialog(true)}>
          <Plus className="mr-2 h-4 w-4" />
          添加模型
        </Button>
      </div>

      {/* 模型列表表格 */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>模型</TableHead>
              <TableHead>描述</TableHead>
              <TableHead>图标</TableHead>
              <TableHead>颜色</TableHead>
              <TableHead>并发限制</TableHead>
              <TableHead>状态</TableHead>
              <TableHead>操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {models.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="h-24 text-center">
                  暂无模型数据
                </TableCell>
              </TableRow>
            ) : (
              models.map((model) => (
                <TableRow key={model.key}>
                  <TableCell>
                    <div className="flex flex-col gap-1">
                      <span className="font-medium">{model.name}</span>
                      <code className="text-xs text-muted-foreground">{model.key}</code>
                    </div>
                  </TableCell>
                  <TableCell>
                    <span className="text-sm text-muted-foreground">
                      {model.description || '-'}
                    </span>
                  </TableCell>
                  <TableCell>
                    {model.icon_url || model.icon ? (
                      <img
                        src={model.icon_url || model.icon}
                        alt={model.name}
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
                    {model.color ? (
                      <Badge className={model.color}>{model.color}</Badge>
                    ) : (
                      <span className="text-xs text-muted-foreground">-</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <span className="text-sm">
                      {model.max_concurrency_limit || '-'}
                    </span>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Switch
                        checked={model.enabled}
                        onCheckedChange={() => handleToggleEnabled(model)}
                        disabled={updateMutation.isPending}
                      />
                      <span className="text-sm">
                        {model.enabled ? '启用' : '禁用'}
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
                          onClick={() => setEditDialog({ open: true, model })}
                        >
                          <Edit className="h-4 w-4 mr-2" />
                          编辑
                        </DropdownMenuItem>

                        <DropdownMenuSeparator />

                        <DropdownMenuItem
                          className="text-red-600"
                          onClick={() => setDeleteDialog({ open: true, model })}
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
      <CreateModelDialog open={createDialog} onOpenChange={setCreateDialog} />

      {/* 编辑对话框 */}
      <EditModelDialog
        open={editDialog.open}
        onOpenChange={(open) => setEditDialog({ open })}
        model={editDialog.model}
      />

      {/* 删除确认对话框 */}
      <AlertDialog open={deleteDialog.open} onOpenChange={(open) => setDeleteDialog({ open })}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认删除</AlertDialogTitle>
            <AlertDialogDescription>
              确定要删除模型 "{deleteDialog.model?.name}" 吗？
              <br />
              注意：只有当该模型没有关联的密钥和任务时才能删除。
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
