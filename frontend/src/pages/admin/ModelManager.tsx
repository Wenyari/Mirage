import { Edit, Filter,MoreVertical, Plus, Trash2 } from 'lucide-react';
import { AlertCircle } from 'lucide-react';
import { useState } from 'react';
import { toast } from 'sonner';

import { CreateModelDialog } from '@/components/admin/CreateModelDialog';
import { EditModelDialog } from '@/components/admin/EditModelDialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
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
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { Switch } from '@/components/ui/switch';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useDeleteModel,useModels, useUpdateModel } from '@/hooks/useKeys';
import type { Model } from '@/types/key';

export default function ModelManager() {
  const [deleteDialog, setDeleteDialog] = useState<{ open: boolean; model?: Model }>({
    open: false,
  });
  const [editDialog, setEditDialog] = useState<{ open: boolean; model?: Model }>({
    open: false,
  });
  const [createDialog, setCreateDialog] = useState(false);
  
  // 筛选状态
  const [tagFilter, setTagFilter] = useState('');

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
        <AlertCircle className="size-4" />
        <AlertDescription>{(error as any)?.message || '加载失败'}</AlertDescription>
      </Alert>
    );
  }

  let models = data?.data || [];

  // 前端筛选逻辑 (API 也支持 tags 参数，但这里为了简单直接在前端筛选，除非数据量很大)
  if (tagFilter) {
    const filterTag = tagFilter.toLowerCase().trim();
    models = models.filter(m => 
      m.tags && m.tags.some(t => t.toLowerCase().includes(filterTag))
    );
  }

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">模型管理</h1>
        <p className="mt-2 text-muted-foreground">
          管理所有AI模型配置，包括模型信息、图标、标签和并发限制
        </p>
      </div>

      {/* 操作栏 */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-semibold">模型列表</h2>
          <p className="mt-1 text-sm text-muted-foreground">共 {models.length} 个模型</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Filter className="absolute left-2.5 top-2.5 size-4 text-muted-foreground" />
            <Input
              placeholder="按标签筛选..."
              value={tagFilter}
              onChange={(e) => setTagFilter(e.target.value)}
              className="w-[200px] pl-9"
            />
          </div>
          <Button onClick={() => setCreateDialog(true)}>
            <Plus className="mr-2 size-4" />
            添加模型
          </Button>
        </div>
      </div>

      {/* 模型列表表格 */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>模型</TableHead>
              <TableHead>描述</TableHead>
              <TableHead>标签</TableHead>
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
                <TableCell colSpan={8} className="h-24 text-center">
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
                    <span className="block max-w-[200px] truncate text-sm text-muted-foreground" title={model.description || ''}>
                      {model.description || '-'}
                    </span>
                  </TableCell>
                  <TableCell>
                    <div className="flex max-w-[200px] flex-wrap gap-1">
                      {model.tags && model.tags.length > 0 ? (
                        model.tags.map(tag => (
                          <Badge key={tag} variant="outline" className="px-1.5 py-0 text-xs">
                            {tag}
                          </Badge>
                        ))
                      ) : (
                        <span className="text-xs text-muted-foreground">-</span>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    {model.icon_url || model.icon ? (
                      <img
                        src={model.icon_url || model.icon}
                        alt={model.name}
                        className="size-8 object-contain"
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
                        <Button variant="ghost" size="icon" className="size-8">
                          <MoreVertical className="size-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          onClick={() => setEditDialog({ open: true, model })}
                        >
                          <Edit className="mr-2 size-4" />
                          编辑
                        </DropdownMenuItem>

                        <DropdownMenuSeparator />

                        <DropdownMenuItem
                          className="text-red-600"
                          onClick={() => setDeleteDialog({ open: true, model })}
                        >
                          <Trash2 className="mr-2 size-4" />
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
