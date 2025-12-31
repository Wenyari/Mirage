import { useState } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  type ColumnDef,
} from '@tanstack/react-table';
import { format } from 'date-fns';
import { Copy, Trash2, Download, Eye, EyeOff } from 'lucide-react';
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
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

import type { CDK, CDKStatus, CDKType } from '@/types/cdk';
import { useVoidCDK } from '@/hooks/useCDK';
import { exportCDKToExcel } from '@/utils/export';

interface CDKTableProps {
  data: CDK[];
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
  onTypeChange: (type: CDKType | 'all') => void;
  onStatusChange: (status: CDKStatus | 'all') => void;
  onSearch: (search: string) => void;
}

export function CDKTable({
  data,
  total,
  page,
  pageSize,
  onPageChange,
  onPageSizeChange,
  onTypeChange,
  onStatusChange,
  onSearch,
}: CDKTableProps) {
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showCodes, setShowCodes] = useState<Record<number, boolean>>({});
  const voidMutation = useVoidCDK();

  // 切换显示/隐藏兑换码
  const toggleShowCode = (id: number) => {
    setShowCodes((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  // 复制兑换码
  const copyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    toast.success('兑换码已复制到剪贴板');
  };

  // 隐藏兑换码（前6位 + ****）
  const maskCode = (code: string): string => {
    if (code.length <= 6) return code;
    return code.substring(0, 6) + '****';
  };

  // 状态徽章
  const getStatusBadge = (status: CDKStatus) => {
    switch (status) {
      case 0:
        return <Badge variant="outline">未使用</Badge>;
      case 1:
        return <Badge variant="default">已使用</Badge>;
      case 2:
        return <Badge variant="destructive">已作废</Badge>;
      default:
        return <Badge variant="secondary">未知</Badge>;
    }
  };

  // 类型徽章
  const getTypeBadge = (type: CDKType) => {
    return type === 'once' ? (
      <Badge variant="secondary">一次性</Badge>
    ) : (
      <Badge variant="outline">通用码</Badge>
    );
  };

  // 定义列
  const columns: ColumnDef<CDK>[] = [
    {
      id: 'select',
      header: ({ table }) => (
        <input
          type="checkbox"
          checked={table.getIsAllPageRowsSelected()}
          onChange={(e) => {
            table.toggleAllPageRowsSelected(!!e.target.checked);
            if (e.target.checked) {
              setSelectedIds(data.map((item) => item.id));
            } else {
              setSelectedIds([]);
            }
          }}
          className="cursor-pointer"
        />
      ),
      cell: ({ row }) => (
        <input
          type="checkbox"
          checked={selectedIds.includes(row.original.id)}
          onChange={(e) => {
            if (e.target.checked) {
              setSelectedIds((prev) => [...prev, row.original.id]);
            } else {
              setSelectedIds((prev) => prev.filter((id) => id !== row.original.id));
            }
          }}
          className="cursor-pointer"
        />
      ),
    },
    {
      accessorKey: 'id',
      header: 'ID',
    },
    {
      accessorKey: 'code',
      header: '兑换码',
      cell: ({ row }) => {
        const code = row.original.code;
        const isShow = showCodes[row.original.id];
        return (
          <div className="flex items-center gap-2">
            <code className="text-sm bg-muted px-2 py-1 rounded">
              {isShow ? code : maskCode(code)}
            </code>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => toggleShowCode(row.original.id)}
            >
              {isShow ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => copyCode(code)}
            >
              <Copy className="h-4 w-4" />
            </Button>
          </div>
        );
      },
    },
    {
      accessorKey: 'points',
      header: '积分',
      cell: ({ row }) => (
        <span className="font-semibold text-primary">{row.original.points}</span>
      ),
    },
    {
      accessorKey: 'type',
      header: '类型',
      cell: ({ row }) => getTypeBadge(row.original.type),
    },
    {
      accessorKey: 'batch_no',
      header: '批次号',
      cell: ({ row }) => row.original.batch_no || '-',
    },
    {
      accessorKey: 'status',
      header: '状态',
      cell: ({ row }) => getStatusBadge(row.original.status),
    },
    {
      accessorKey: 'used_by',
      header: '使用者',
      cell: ({ row }) => row.original.used_by || '-',
    },
    {
      accessorKey: 'created_at',
      header: '创建时间',
      cell: ({ row }) => format(new Date(row.original.created_at), 'yyyy-MM-dd HH:mm'),
    },
    {
      accessorKey: 'expire_at',
      header: '过期时间',
      cell: ({ row }) =>
        row.original.expire_at
          ? format(new Date(row.original.expire_at), 'yyyy-MM-dd HH:mm')
          : '永不过期',
    },
  ];

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    manualPagination: true,
    pageCount: Math.ceil(total / pageSize),
  });

  // 批量作废
  const handleBatchVoid = async () => {
    if (selectedIds.length === 0) {
      toast.error('请先选择要作废的CDK');
      return;
    }

    try {
      await voidMutation.mutateAsync({ ids: selectedIds });
      toast.success(`成功作废 ${selectedIds.length} 个CDK`);
      setSelectedIds([]);
      setShowDeleteDialog(false);
    } catch (error: any) {
      toast.error(error.message || '作废失败');
    }
  };

  // 导出当前列表
  const handleExport = () => {
    if (data.length === 0) {
      toast.error('暂无数据可导出');
      return;
    }
    exportCDKToExcel(data);
    toast.success('导出成功');
  };

  return (
    <div className="space-y-4">
      {/* 筛选和操作栏 */}
      <div className="flex flex-col md:flex-row gap-4">
        <Input
          placeholder="搜索兑换码或批次号..."
          onChange={(e) => onSearch(e.target.value)}
          className="md:w-80"
        />

        <Select onValueChange={(value) => onTypeChange(value as CDKType | 'all')}>
          <SelectTrigger className="md:w-40">
            <SelectValue placeholder="类型筛选" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部类型</SelectItem>
            <SelectItem value="once">一次性</SelectItem>
            <SelectItem value="universal">通用码</SelectItem>
          </SelectContent>
        </Select>

        <Select onValueChange={(value) => onStatusChange(value as any)}>
          <SelectTrigger className="md:w-40">
            <SelectValue placeholder="状态筛选" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部状态</SelectItem>
            <SelectItem value="0">未使用</SelectItem>
            <SelectItem value="1">已使用</SelectItem>
            <SelectItem value="2">已作废</SelectItem>
          </SelectContent>
        </Select>

        <div className="flex gap-2 md:ml-auto">
          <Button variant="outline" onClick={handleExport}>
            <Download className="h-4 w-4 mr-2" />
            导出列表
          </Button>
          <Button
            variant="destructive"
            onClick={() => setShowDeleteDialog(true)}
            disabled={selectedIds.length === 0}
          >
            <Trash2 className="h-4 w-4 mr-2" />
            批量作废 ({selectedIds.length})
          </Button>
        </div>
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

      {/* 分页 */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-muted-foreground">
          共 {total} 条，第 {page} / {Math.ceil(total / pageSize)} 页
        </div>
        <div className="flex items-center gap-2">
          <Select
            value={pageSize.toString()}
            onValueChange={(value) => onPageSizeChange(parseInt(value))}
          >
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="10">10 条/页</SelectItem>
              <SelectItem value="20">20 条/页</SelectItem>
              <SelectItem value="50">50 条/页</SelectItem>
              <SelectItem value="100">100 条/页</SelectItem>
            </SelectContent>
          </Select>

          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(page - 1)}
            disabled={page === 1}
          >
            上一页
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(page + 1)}
            disabled={page >= Math.ceil(total / pageSize)}
          >
            下一页
          </Button>
        </div>
      </div>

      {/* 作废确认对话框 */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认作废</AlertDialogTitle>
            <AlertDialogDescription>
              确定要作废选中的 {selectedIds.length} 个CDK吗？此操作不可撤销。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction onClick={handleBatchVoid}>确认作废</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
