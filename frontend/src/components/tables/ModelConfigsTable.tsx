import { useState } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  type ColumnDef,
} from '@tanstack/react-table';
import { Edit, Trash2, Plus, MoreVertical } from 'lucide-react';
import { toast } from 'sonner';

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
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

import type { ModelConfig } from '@/types/modelConfig';
import { MEMBERSHIP_TIER_LABELS } from '@/types/modelConfig';
import {
  useModelConfigs,
  useUpdateModelConfig,
  useDeleteModelConfig,
} from '@/hooks/useModelConfigs';
import { ModelConfigDialog } from '@/components/admin/ModelConfigDialog';

export function ModelConfigsTable() {
  const [deleteDialog, setDeleteDialog] = useState<{ open: boolean; config?: ModelConfig }>({
    open: false,
  });
  const [editDialog, setEditDialog] = useState<{ open: boolean; config?: ModelConfig }>({
    open: false,
  });
  const [createDialog, setCreateDialog] = useState(false);

  const { data, isLoading, isError, error } = useModelConfigs();
  const updateMutation = useUpdateModelConfig();
  const deleteMutation = useDeleteModelConfig();

  // 切换启用状态
  const handleToggleActive = async (config: ModelConfig) => {
    try {
      await updateMutation.mutateAsync({
        id: config.id,
        data: { is_active: !config.is_active },
      });
      toast.success(config.is_active ? '模型配置已禁用' : '模型配置已启用');
    } catch (err: any) {
      toast.error(err.message || '操作失败');
    }
  };

  // 删除配置
  const handleDelete = async () => {
    if (!deleteDialog.config) return;

    try {
      await deleteMutation.mutateAsync(deleteDialog.config.id);
      toast.success('配置已删除');
      setDeleteDialog({ open: false });
    } catch (err: any) {
      toast.error(err.message || '删除失败');
    }
  };

  // 定义列
  const columns: ColumnDef<ModelConfig>[] = [
    {
      accessorKey: 'model',
      header: '模型',
      cell: ({ row }) => (
        <div className="flex items-center gap-2">
          <Badge variant="outline">{row.original.model_name}</Badge>
          <code className="text-xs text-muted-foreground">{row.original.model}</code>
        </div>
      ),
    },
    {
      accessorKey: 'allowed_tiers',
      header: '允许等级',
      cell: ({ row }) => (
        <div className="flex flex-wrap gap-1">
          {row.original.allowed_tiers.map((tier) => (
            <Badge key={tier} variant="secondary" className="text-xs">
              {MEMBERSHIP_TIER_LABELS[tier]}
            </Badge>
          ))}
        </div>
      ),
    },
    {
      accessorKey: 'cost_per_call',
      header: '固定计费',
      cell: ({ row }) => (
        <span className="font-medium">{row.original.cost_per_call} 积分/次</span>
      ),
    },
    {
      accessorKey: 'token_cost_config',
      header: 'Token 计费',
      cell: ({ row }) => {
        const config = row.original.token_cost_config;
        if (!config.enabled) {
          return <span className="text-muted-foreground">未启用</span>;
        }
        return (
          <div className="text-sm">
            <div>输入: {config.input_cost}/千token</div>
            <div>输出: {config.output_cost}/千token</div>
          </div>
        );
      },
    },
    {
      accessorKey: 'params',
      header: '自定义参数',
      cell: ({ row }) => {
        const params = row.original.params;
        if (!params) {
          return <span className="text-xs text-muted-foreground">-</span>;
        }
        return (
          <div className="max-w-[150px] truncate text-xs font-mono text-muted-foreground" title={JSON.stringify(params, null, 2)}>
            {JSON.stringify(params)}
          </div>
        );
      },
    },
    {
      accessorKey: 'is_active',
      header: '状态',
      cell: ({ row }) => {
        const config = row.original;
        return (
          <div className="flex items-center gap-2">
            <Switch
              checked={config.is_active}
              onCheckedChange={() => handleToggleActive(config)}
              disabled={updateMutation.isPending}
            />
            <span className="text-sm">{config.is_active ? '启用' : '禁用'}</span>
          </div>
        );
      },
    },
    {
      id: 'actions',
      header: '操作',
      cell: ({ row }) => {
        const config = row.original;
        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => setEditDialog({ open: true, config })}>
                <Edit className="h-4 w-4 mr-2" />
                编辑配置
              </DropdownMenuItem>

              <DropdownMenuSeparator />

              <DropdownMenuItem
                className="text-red-600"
                onClick={() => setDeleteDialog({ open: true, config })}
              >
                <Trash2 className="h-4 w-4 mr-2" />
                删除配置
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        );
      },
    },
  ];

  const table = useReactTable({
    data: data?.data || [],
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

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

  return (
    <>
      {/* 操作栏 */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-semibold">模型配置列表</h2>
          <p className="text-sm text-muted-foreground mt-1">
            共 {data?.data.length} 个模型配置
          </p>
        </div>
        <Button onClick={() => setCreateDialog(true)}>
          <Plus className="mr-2 h-4 w-4" />
          添加配置
        </Button>
      </div>

      {/* 表格 */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id}>
                    {header.isPlaceholder
                      ? null
                      : flexRender(header.column.columnDef.header, header.getContext())}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow key={row.id}>
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center">
                  暂无数据
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* 创建对话框 */}
      <ModelConfigDialog
        open={createDialog}
        onOpenChange={setCreateDialog}
        mode="create"
      />

      {/* 编辑对话框 */}
      <ModelConfigDialog
        open={editDialog.open}
        onOpenChange={(open) => setEditDialog({ open })}
        mode="edit"
        config={editDialog.config}
      />

      {/* 删除确认对话框 */}
      <AlertDialog open={deleteDialog.open} onOpenChange={(open) => setDeleteDialog({ open })}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认删除</AlertDialogTitle>
            <AlertDialogDescription>
              确定要删除模型 "{deleteDialog.config?.model_name}" 的配置吗？
              <br />
              此操作不可撤销。
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
    </>
  );
}
