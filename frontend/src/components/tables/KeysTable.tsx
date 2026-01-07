import {
  type ColumnDef,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from '@tanstack/react-table';
import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import {
  Clock,
  Copy,
  Edit,
  Eye,
  EyeOff,
  MoreVertical,
  Power,
  PowerOff,
  Trash2,
} from 'lucide-react';
import { useState } from 'react';
import { toast } from 'sonner';

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
import { Progress } from '@/components/ui/progress';
import { Switch } from '@/components/ui/switch';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { useDeleteKey, useModels,useTriggerCooldown, useUpdateKey } from '@/hooks/useKeys';
import type { Key } from '@/types/key';
import { getConcurrencyColorClass, getConcurrencyRate } from '@/types/key';

interface KeysTableProps {
  data: Key[];
  onEdit: (key: Key) => void;
}

export function KeysTable({ data, onEdit }: KeysTableProps) {
  const [showKeys, setShowKeys] = useState<Record<number, boolean>>({});
  const [deleteDialog, setDeleteDialog] = useState<{ open: boolean; keyId?: number }>({
    open: false,
  });
  const [cooldownDialog, setCooldownDialog] = useState<{
    open: boolean;
    keyId?: number;
    action?: 'trigger' | 'release';
  }>({ open: false });

  const deleteMutation = useDeleteKey();
  const updateMutation = useUpdateKey();
  const cooldownMutation = useTriggerCooldown();
  const { data: modelsData } = useModels();

  // 创建模型名称映射
  const modelMap = new Map(
    modelsData?.data?.map((p) => [p.key, p.name]) || []
  );

  // 切换密钥显示/隐藏
  const toggleShowKey = (id: number) => {
    setShowKeys((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  // 复制密钥
  const copyKey = (keySecret: string) => {
    navigator.clipboard.writeText(keySecret);
    toast.success('密钥已复制到剪贴板');
  };

  // 切换状态
  const handleToggleStatus = async (id: number, currentStatus: 0 | 1) => {
    try {
      await updateMutation.mutateAsync({
        id,
        data: { status: currentStatus === 1 ? 0 : 1 },
      });
      toast.success(currentStatus === 1 ? '密钥已停用' : '密钥已启用');
    } catch (error: any) {
      toast.error(error.message || '操作失败');
    }
  };

  // 删除密钥
  const handleDelete = async () => {
    if (!deleteDialog.keyId) return;

    try {
      await deleteMutation.mutateAsync(deleteDialog.keyId);
      toast.success('密钥已删除');
      setDeleteDialog({ open: false });
    } catch (error: any) {
      toast.error(error.message || '删除失败');
    }
  };

  // 触发/解除熔断
  const handleCooldown = async () => {
    if (!cooldownDialog.keyId || !cooldownDialog.action) return;

    try {
      await cooldownMutation.mutateAsync({
        id: cooldownDialog.keyId,
        data: { action: cooldownDialog.action, duration: 300 },
      });
      toast.success(
        cooldownDialog.action === 'trigger' ? '已触发熔断（5分钟）' : '已解除熔断'
      );
      setCooldownDialog({ open: false });
    } catch (error: any) {
      toast.error(error.message || '操作失败');
    }
  };

  // 定义列
  const columns: ColumnDef<Key>[] = [
    {
      accessorKey: 'id',
      header: 'ID',
      cell: ({ row }) => <span className="font-mono text-sm">{row.original.id}</span>,
    },
    {
      accessorKey: 'models',
      header: '模型',
      cell: ({ row }) => (
        <div className="flex flex-wrap gap-1 max-w-[200px]">
          {row.original.models.map((modelKey) => (
            <Badge key={modelKey} variant="outline" className="text-xs">
              {modelMap.get(modelKey) || modelKey}
            </Badge>
          ))}
        </div>
      ),
    },
    {
      accessorKey: 'api_base',
      header: 'API Base',
      cell: ({ row }) => {
        const key = row.original;
        // 如果有 detailed config，显示 "多端点" 提示
        if (key.model_configs && key.model_configs.length > 0) {
          return (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger>
                  <div className="flex items-center gap-1">
                    <Badge variant="secondary" className="font-normal text-xs">
                      {key.model_configs.length} 个配置
                    </Badge>
                  </div>
                </TooltipTrigger>
                <TooltipContent className="max-w-[300px] p-0">
                  <div className="p-2 space-y-2">
                    <div className="text-xs font-semibold border-b pb-1">详细配置</div>
                    {key.model_configs.map((config) => (
                      <div key={config.model} className="text-xs grid grid-cols-[80px_1fr] gap-2">
                        <span className="font-medium truncate">{modelMap.get(config.model) || config.model}</span>
                        <span className="text-muted-foreground truncate font-mono">{config.api_base || '默认'}</span>
                      </div>
                    ))}
                  </div>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          );
        }

        // 否则显示全局 api_base
        return (
          <div className="max-w-[150px] truncate text-xs text-muted-foreground" title={row.original.api_base || '默认'}>
            {row.original.api_base || '默认'}
          </div>
        );
      },
    },
    {
      accessorKey: 'key_secret',
      header: '密钥',
      cell: ({ row }) => {
        const key = row.original;
        const isShow = showKeys[key.id];
        return (
          <div className="flex items-center gap-2">
            <code className="rounded bg-muted px-2 py-1 font-mono text-xs">
              {isShow ? key.key_secret : key.key_secret}
            </code>
            <Button
              variant="ghost"
              size="icon"
              className="size-7"
              onClick={() => toggleShowKey(key.id)}
            >
              {isShow ? <EyeOff className="size-3" /> : <Eye className="size-3" />}
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="size-7"
              onClick={() => copyKey(key.key_secret)}
            >
              <Copy className="size-3" />
            </Button>
          </div>
        );
      },
    },
    {
      accessorKey: 'concurrency',
      header: '并发槽位',
      cell: ({ row }) => {
        const key = row.original;
        const rate = getConcurrencyRate(key.current_usage, key.max_concurrency);
        const colorClass = getConcurrencyColorClass(rate);

        return (
          <div className="w-48">
            <div className="mb-1 flex items-center gap-2">
              <span className="text-sm font-medium">
                {key.current_usage} / {key.max_concurrency}
              </span>
              <span className="text-xs text-muted-foreground">({rate.toFixed(0)}%)</span>
            </div>
            <Progress
              value={rate}
              className="h-2"
              indicatorClassName={colorClass}
            />
          </div>
        );
      },
    },
    {
      accessorKey: 'weight',
      header: '权重',
      cell: ({ row }) => (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger>
              <span className="text-sm font-medium">{row.original.weight}</span>
            </TooltipTrigger>
            <TooltipContent>
              <p>权重越高，被选中概率越大</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      ),
    },
    {
      accessorKey: 'status',
      header: '状态',
      cell: ({ row }) => {
        const key = row.original;
        return (
          <div className="flex items-center gap-2">
            <Switch
              checked={key.status === 1}
              onCheckedChange={() => handleToggleStatus(key.id, key.status)}
              disabled={updateMutation.isPending}
            />
            <span className="text-sm">{key.status === 1 ? '启用' : '停用'}</span>
          </div>
        );
      },
    },
    {
      accessorKey: 'cooling',
      header: '冷却状态',
      cell: ({ row }) => {
        const key = row.original;
        if (!key.is_cooling) {
          return <Badge variant="secondary">正常</Badge>;
        }

        const timeLeft = key.cooling_until
          ? formatDistanceToNow(new Date(key.cooling_until), {
              locale: zhCN,
              addSuffix: true,
            })
          : '';

        return (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger>
                <Badge variant="destructive" className="cursor-help">
                  <Clock className="mr-1 size-3" />
                  冷却中
                </Badge>
              </TooltipTrigger>
              <TooltipContent>
                <p>预计{timeLeft}恢复</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        );
      },
    },
    {
      accessorKey: 'stats',
      header: '统计',
      cell: ({ row }) => {
        const key = row.original;
        const errorRate =
          key.total_calls > 0 ? ((key.total_errors / key.total_calls) * 100).toFixed(2) : '0.00';

        return (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger>
                <div className="text-xs">
                  <div className="text-green-600">{key.total_calls.toLocaleString()} 次</div>
                  <div className="text-red-600">{key.total_errors.toLocaleString()} 错误</div>
                </div>
              </TooltipTrigger>
              <TooltipContent>
                <p>错误率: {errorRate}%</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        );
      },
    },
    {
      id: 'actions',
      header: '操作',
      cell: ({ row }) => {
        const key = row.original;

        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="size-8">
                <MoreVertical className="size-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onEdit(key)}>
                <Edit className="mr-2 size-4" />
                编辑配置
              </DropdownMenuItem>

              <DropdownMenuSeparator />

              {key.is_cooling ? (
                <DropdownMenuItem
                  onClick={() =>
                    setCooldownDialog({ open: true, keyId: key.id, action: 'release' })
                  }
                >
                  <Power className="mr-2 size-4" />
                  解除熔断
                </DropdownMenuItem>
              ) : (
                <DropdownMenuItem
                  onClick={() =>
                    setCooldownDialog({ open: true, keyId: key.id, action: 'trigger' })
                  }
                >
                  <PowerOff className="mr-2 size-4" />
                  触发熔断
                </DropdownMenuItem>
              )}

              <DropdownMenuSeparator />

              <DropdownMenuItem
                className="text-red-600"
                onClick={() => setDeleteDialog({ open: true, keyId: key.id })}
              >
                <Trash2 className="mr-2 size-4" />
                删除密钥
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        );
      },
    },
  ];

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <>
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

      {/* 删除确认对话框 */}
      <AlertDialog open={deleteDialog.open} onOpenChange={(open) => setDeleteDialog({ open })}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认删除</AlertDialogTitle>
            <AlertDialogDescription>
              确定要删除这个密钥吗？此操作不可撤销。
              <br />
              如果密钥正在被使用，删除操作将失败。
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

      {/* 熔断控制对话框 */}
      <AlertDialog
        open={cooldownDialog.open}
        onOpenChange={(open) => setCooldownDialog({ open })}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {cooldownDialog.action === 'trigger' ? '触发熔断' : '解除熔断'}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {cooldownDialog.action === 'trigger'
                ? '触发熔断后，该密钥将在 5 分钟内不会被分配给新任务。'
                : '解除熔断后，该密钥将立即恢复可用状态。'}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction onClick={handleCooldown}>确认</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
