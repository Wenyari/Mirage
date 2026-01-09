import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  useReactTable,
} from '@tanstack/react-table';
import { DollarSign, Edit, MoreHorizontal, UserCheck, UserX, X } from 'lucide-react';

import { LevelBadge } from '@/components/admin/LevelBadge';
import { StatusBadge } from '@/components/admin/StatusBadge';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import type { User, UserLevel, UserListResponse,UserStatus } from '@/types/user';
import { USER_LEVEL_LABELS } from '@/types/user';
import { formatDate } from '@/utils/format';

interface UsersTableProps {
  data: UserListResponse | undefined;
  isLoading: boolean;
  searchValue: string;
  onEdit: (user: User) => void;
  onBalanceEdit: (user: User) => void;
  onStatusChange: (userId: number, status: UserStatus) => void;
  onPageChange: (page: number) => void;
  onLimitChange: (limit: number) => void;
  onSearch: (email: string) => void;
  onClearSearch: () => void;
  onLevelFilter: (level: UserLevel | undefined) => void;
  onStatusFilter: (status: UserStatus | undefined) => void;
}

export function UsersTable({
  data,
  isLoading,
  searchValue,
  onEdit,
  onBalanceEdit,
  onStatusChange,
  onPageChange,
  onLimitChange,
  onSearch,
  onClearSearch,
  onLevelFilter,
  onStatusFilter,
}: UsersTableProps) {
  // 表格列定义
  const columns: ColumnDef<User>[] = [
    {
      accessorKey: 'id',
      header: 'ID',
      cell: ({ row }) => (
        <div className="font-mono text-sm">#{row.getValue('id')}</div>
      ),
    },
    {
      accessorKey: 'email',
      header: '邮箱',
      cell: ({ row }) => {
        const email = row.getValue('email') as string;
        const role = row.original.role;
        return (
          <div className="flex items-center gap-2">
            <div className="font-medium">{email}</div>
            {role === 'admin' && (
              <Badge variant="outline" className="text-xs">
                管理员
              </Badge>
            )}
          </div>
        );
      },
    },
    {
      accessorKey: 'level',
      header: '等级',
      cell: ({ row }) => {
        const level = row.getValue('level') as UserLevel;
        return <LevelBadge level={level} />;
      },
    },
    {
      accessorKey: 'total_balance',
      header: '积分余额',
      cell: ({ row }) => {
        const balance = row.getValue('total_balance') as number;
        return (
          <div className="font-medium">
            {balance.toLocaleString()}
          </div>
        );
      },
    },
    {
      accessorKey: 'status',
      header: '状态',
      cell: ({ row }) => {
        const user = row.original;
        return (
          <StatusBadge
            status={user.status}
            onChange={(newStatus) => onStatusChange(user.id, newStatus)}
          />
        );
      },
    },
    {
      accessorKey: 'register_ip',
      header: '注册IP',
      cell: ({ row }) => {
        const ip = row.getValue('register_ip') as string;
        return <div className="font-mono text-sm text-gray-600">{ip}</div>;
      },
    },
    {
      accessorKey: 'created_at',
      header: '注册时间',
      cell: ({ row }) => {
        const date = row.getValue('created_at') as string;
        return <div className="text-sm">{formatDate(date)}</div>;
      },
    },
    {
      id: 'actions',
      cell: ({ row }) => {
        const user = row.original;
        
        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="size-8 p-0">
                <span className="sr-only">打开菜单</span>
                <MoreHorizontal className="size-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>操作</DropdownMenuLabel>
              <DropdownMenuItem onClick={() => onEdit(user)}>
                <Edit className="mr-2 size-4" />
                编辑资料
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onBalanceEdit(user)}>
                <DollarSign className="mr-2 size-4" />
                积分管理
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              {user.status === 1 ? (
                <DropdownMenuItem 
                  onClick={() => onStatusChange(user.id, 0)}
                  className="text-red-600"
                >
                  <UserX className="mr-2 size-4" />
                  封禁用户
                </DropdownMenuItem>
              ) : (
                <DropdownMenuItem 
                  onClick={() => onStatusChange(user.id, 1)}
                  className="text-green-600"
                >
                  <UserCheck className="mr-2 size-4" />
                  解封用户
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        );
      },
    },
  ];
  const table = useReactTable({
    data: data?.items || [],
    columns,
    pageCount: data ? Math.ceil(data.total / data.limit) : 0,
    state: {
      pagination: {
        pageIndex: data ? data.page - 1 : 0,
        pageSize: data?.limit || 10,
      },
    },
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    manualPagination: true,
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        {/* 搜索和筛选栏 */}
        <div className="flex items-center gap-4">
          <div className="relative">
            <Skeleton className="h-10 w-64" />
          </div>
          <Skeleton className="h-10 w-32" />
          <Skeleton className="h-10 w-32" />
        </div>
        
        {/* 表格骨架 */}
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                {Array.from({ length: 8 }).map((_, i) => (
                  <TableHead key={i}>
                    <Skeleton className="h-4 w-16" />
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {Array.from({ length: 10 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 8 }).map((_, j) => (
                    <TableCell key={j}>
                      <Skeleton className="h-4 w-20" />
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
        
        {/* 分页骨架 */}
        <div className="flex items-center justify-between">
          <Skeleton className="h-8 w-32" />
          <div className="flex gap-2">
            <Skeleton className="h-8 w-20" />
            <Skeleton className="h-8 w-20" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 搜索和筛选栏 */}
      <div className="flex items-center gap-4">
        <div className="relative max-w-sm">
          <Input
            placeholder="搜索邮箱..."
            className="pr-8"
            value={searchValue}
            onChange={(e) => onSearch(e.target.value)}
          />
          {searchValue && (
            <Button
              variant="ghost"
              size="sm"
              className="absolute right-0 top-0 h-full px-2 py-1 hover:bg-transparent"
              onClick={onClearSearch}
            >
              <X className="size-4 text-muted-foreground" />
            </Button>
          )}
        </div>
        <Select onValueChange={(value) => onLevelFilter(value !== 'all' ? parseInt(value) as UserLevel : undefined)}>
          <SelectTrigger className="w-32">
            <SelectValue placeholder="所有等级" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">所有等级</SelectItem>
            {Object.entries(USER_LEVEL_LABELS).map(([level, label]) => (
              <SelectItem key={level} value={level}>
                {label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select onValueChange={(value) => onStatusFilter(value !== 'all' ? parseInt(value) as UserStatus : undefined)}>
          <SelectTrigger className="w-32">
            <SelectValue placeholder="所有状态" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">所有状态</SelectItem>
            <SelectItem value="1">正常</SelectItem>
            <SelectItem value="0">封禁</SelectItem>
          </SelectContent>
        </Select>
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
                      : flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  data-state={row.getIsSelected() && "selected"}
                >
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
                  没有找到用户数据
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* 分页 */}
      <div className="flex items-center justify-between">
        <div className="flex-1 text-sm text-muted-foreground">
          共 {data?.total || 0} 条记录
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange((data?.page || 1) - 1)}
            disabled={!data || data.page <= 1}
          >
            上一页
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange((data?.page || 1) + 1)}
            disabled={!data || data.page >= Math.ceil(data.total / data.limit)}
          >
            下一页
          </Button>
        </div>
      </div>
    </div>
  );
}