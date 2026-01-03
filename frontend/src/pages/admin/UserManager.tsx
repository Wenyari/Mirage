import { Download, RefreshCw, Users, X } from 'lucide-react';
import { useCallback,useEffect, useState } from 'react';

import { UserBalanceDialog } from '@/components/admin/UserBalanceDialog';
import { UserEditDialog } from '@/components/admin/UserEditDialog';
import { UsersTable } from '@/components/tables/UsersTable';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useUpdateBalance, useUpdateProfile,useUsers } from '@/hooks/useUsers';
import type { User, UserLevel, UserListParams,UserStatus } from '@/types/user';

/**
 * 用户管理页面
 * 实现用户列表展示、搜索筛选、编辑、充值扣费等功能
 */
export default function UserManager() {
  // 查询参数状态
  const [params, setParams] = useState<UserListParams>({
    page: 1,
    limit: 10,
    email: '',
    level: undefined,
    status: undefined,
  });

  // 搜索输入状态（用于防抖）
  const [searchInput, setSearchInput] = useState('');

  // 防抖搜索逻辑
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchInput !== params.email) {
        setParams(prev => ({ ...prev, email: searchInput, page: 1 }));
      }
    }, 500); // 500ms防抖延迟

    return () => clearTimeout(timer);
  }, [searchInput, params.email]);

  // 同步params.email到搜索输入框（当通过其他方式重置时）
  useEffect(() => {
    // 只有当params.email被外部重置为空，且searchInput不为空时才同步
    if (params.email === '' && searchInput !== '') {
      setSearchInput('');
    }
  }, [params.email]);

  // 对话框状态
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [balanceDialogOpen, setBalanceDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);

  // 数据查询
  const { data, isLoading, refetch } = useUsers(params);

  // 更新操作
  const updateBalanceMutation = useUpdateBalance();
  const updateProfileMutation = useUpdateProfile();

  // 处理分页变化
  const handlePageChange = (page: number) => {
    setParams(prev => ({ ...prev, page }));
  };

  // 处理每页条数变化
  const handleLimitChange = (limit: number) => {
    setParams(prev => ({ ...prev, limit, page: 1 }));
  };

  // 处理搜索输入变化（防抖处理）
  const handleSearchChange = (email: string) => {
    setSearchInput(email);
  };

  // 清除搜索
  const handleClearSearch = () => {
    setSearchInput('');
    setParams(prev => ({ ...prev, email: '', page: 1 }));
  };

  // 处理等级筛选
  const handleLevelFilter = (level: UserLevel | undefined) => {
    setParams(prev => ({ ...prev, level, page: 1 }));
  };

  // 处理状态筛选
  const handleStatusFilter = (status: UserStatus | undefined) => {
    setParams(prev => ({ ...prev, status, page: 1 }));
  };

  // 处理编辑用户
  const handleEditUser = (user: User) => {
    setSelectedUser(user);
    setEditDialogOpen(true);
  };

  // 处理余额管理
  const handleBalanceEdit = (user: User) => {
    setSelectedUser(user);
    setBalanceDialogOpen(true);
  };

  // 处理状态变更
  const handleStatusChange = async (userId: number, status: UserStatus) => {
    try {
      await updateProfileMutation.mutateAsync({ userId, profile: { status } });
    } catch (error) {
      // 错误处理在Hook中完成
    }
  };

  // 处理编辑提交
  const handleEditSubmit = async (userId: number, data: { level?: UserLevel; status?: UserStatus }) => {
    try {
      await updateProfileMutation.mutateAsync({ userId, profile: data });
    } catch (error) {
      // 错误处理在Hook中完成
      throw error; // 重新抛出错误，让对话框知道操作失败
    }
  };

  // 处理余额操作提交
  const handleBalanceSubmit = async (userId: number, amount: number, reason: string) => {
    try {
      await updateBalanceMutation.mutateAsync({ userId, amount, reason });
    } catch (error) {
      // 错误处理在Hook中完成
      throw error; // 重新抛出错误，让对话框知道操作失败
    }
  };

  // 处理数据刷新
  const handleRefresh = () => {
    refetch();
  };

  // 处理导出
  const handleExport = () => {
    // TODO: 实现导出功能
    console.log('导出用户数据', params);
  };

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">用户管理</h1>
        <p className="text-muted-foreground">
          管理用户账户、充值和权限，共 {data?.total || 0} 名用户
        </p>
      </div>

      {/* 统计卡片 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">总用户数</CardTitle>
            <Users className="size-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.total || 0}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">正常用户</CardTitle>
            <Users className="size-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {data?.items?.filter(user => user.status === 1).length || 0}
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">封禁用户</CardTitle>
            <Users className="size-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {data?.items?.filter(user => user.status === 0).length || 0}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 操作栏 */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>用户列表</CardTitle>
              <CardDescription>
                查看和管理所有用户信息
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={handleRefresh} disabled={isLoading}>
                <RefreshCw className={`mr-2 size-4 ${isLoading ? 'animate-spin' : ''}`} />
                刷新
              </Button>
              <Button variant="outline" size="sm" onClick={handleExport}>
                <Download className="mr-2 size-4" />
                导出
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <UsersTable
            data={data}
            isLoading={isLoading}
            searchValue={searchInput}
            onEdit={handleEditUser}
            onBalanceEdit={handleBalanceEdit}
            onStatusChange={handleStatusChange}
            onPageChange={handlePageChange}
            onLimitChange={handleLimitChange}
            onSearch={handleSearchChange}
            onClearSearch={handleClearSearch}
            onLevelFilter={handleLevelFilter}
            onStatusFilter={handleStatusFilter}
          />
        </CardContent>
      </Card>

      {/* 编辑对话框 */}
      <UserEditDialog
        user={selectedUser}
        open={editDialogOpen}
        onOpenChange={setEditDialogOpen}
        onSubmit={handleEditSubmit}
        isLoading={updateProfileMutation.isPending}
      />

      {/* 余额管理对话框 */}
      <UserBalanceDialog
        user={selectedUser}
        open={balanceDialogOpen}
        onOpenChange={setBalanceDialogOpen}
        onSubmit={handleBalanceSubmit}
        isLoading={updateBalanceMutation.isPending}
      />
    </div>
  );
}
