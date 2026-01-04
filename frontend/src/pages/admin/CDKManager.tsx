import { AlertCircle } from 'lucide-react';
import { useEffect, useState } from 'react';

import { CDKGenerateForm } from '@/components/admin/CDKGenerateForm';
import { CDKTable } from '@/components/tables/CDKTable';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { useCDKList } from '@/hooks/useCDK';
import type { CDKListParams, CDKStatus, CDKType } from '@/types/cdk';

export default function CDKManager() {
  // 查询参数状态
  const [params, setParams] = useState<CDKListParams>({
    page: 1,
    page_size: 10,
    search: '',
    type: undefined,
    status: undefined,
  });

  // 搜索输入状态（用于防抖）
  const [searchInput, setSearchInput] = useState('');

  // 防抖搜索逻辑
  useEffect(() => {
    const timer = setTimeout(() => {
      // 确保 params.search 即使为 undefined 也视为 ''
      const currentSearch = params.search || '';
      if (searchInput !== currentSearch) {
        setParams((prev) => ({ ...prev, search: searchInput, page: 1 }));
      }
    }, 500); // 500ms防抖延迟

    return () => clearTimeout(timer);
  }, [searchInput, params.search]);

  // 获取 CDK 列表
  const { data, isLoading, isError, error } = useCDKList(params);

  // 处理类型筛选
  const handleTypeChange = (value: CDKType | 'all') => {
    setParams((prev) => ({
      ...prev,
      type: value === 'all' ? undefined : value,
      page: 1,
    }));
  };

  // 处理状态筛选
  const handleStatusChange = (value: CDKStatus | 'all') => {
    setParams((prev) => ({
      ...prev,
      status: value === 'all' ? undefined : (value as CDKStatus),
      page: 1,
    }));
  };

  // 处理搜索
  const handleSearch = (value: string) => {
    setSearchInput(value);
  };

  // 清除搜索
  const handleClearSearch = () => {
    setSearchInput('');
    setParams((prev) => ({ ...prev, search: '', page: 1 }));
  };

  // 监听外部重置（如果有，比如其他逻辑重置了 params.search）
  useEffect(() => {
    const currentSearch = params.search || '';
    if (currentSearch === '' && searchInput !== '') {
      setSearchInput('');
    }
  }, [params.search]);

  // 处理分页变化
  const handlePageChange = (newPage: number) => {
    setParams((prev) => ({ ...prev, page: newPage }));
  };

  // 处理页面大小变化
  const handlePageSizeChange = (newPageSize: number) => {
    setParams((prev) => ({ ...prev, page_size: newPageSize, page: 1 }));
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">CDK 管理</h1>
        <p className="mt-2 text-muted-foreground">
          生成和管理兑换码，批量导出和作废
        </p>
      </div>

      <CDKGenerateForm />

      <div className="space-y-4">
        <h2 className="text-2xl font-semibold">CDK 列表</h2>

        {/* 首次加载且无数据时显示骨架屏 */}
        {isLoading && !data && (
          <div className="space-y-4">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-64 w-full" />
          </div>
        )}

        {isError && (
          <Alert variant="destructive">
            <AlertCircle className="size-4" />
            <AlertDescription>
              {(error as any)?.message || '加载CDK列表失败'}
            </AlertDescription>
          </Alert>
        )}

        {/* 只要有数据（包括旧数据）就显示表格 */}
        {data && (
          <CDKTable
            data={data.items}
            total={data.total}
            page={params.page || 1}
            pageSize={params.page_size || 10}
            onPageChange={handlePageChange}
            onPageSizeChange={handlePageSizeChange}
            onTypeChange={handleTypeChange}
            onStatusChange={handleStatusChange}
            onSearch={handleSearch}
            onClearSearch={handleClearSearch}
            searchValue={searchInput}
          />
        )}
      </div>
    </div>
  );
}
