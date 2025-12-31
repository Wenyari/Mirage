import { AlertCircle } from 'lucide-react';
import { useState } from 'react';

import { CDKGenerateForm } from '@/components/admin/CDKGenerateForm';
import { CDKTable } from '@/components/tables/CDKTable';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { useCDKList } from '@/hooks/useCDK';
import type { CDKStatus,CDKType } from '@/types/cdk';

export default function CDKManager() {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [type, setType] = useState<CDKType | undefined>();
  const [status, setStatus] = useState<CDKStatus | undefined>();
  const [search, setSearch] = useState('');

  // 获取 CDK 列表
  const { data, isLoading, isError, error } = useCDKList({
    page,
    page_size: pageSize,
    type,
    status,
    search,
  });

  // 处理类型筛选
  const handleTypeChange = (value: CDKType | 'all') => {
    setType(value === 'all' ? undefined : value);
    setPage(1);
  };

  // 处理状态筛选
  const handleStatusChange = (value: CDKStatus | 'all') => {
    setStatus(value === 'all' ? undefined : (value as CDKStatus));
    setPage(1);
  };

  // 处理搜索
  const handleSearch = (value: string) => {
    setSearch(value);
    setPage(1);
  };

  // 处理分页变化
  const handlePageChange = (newPage: number) => {
    setPage(newPage);
  };

  // 处理页面大小变化
  const handlePageSizeChange = (newPageSize: number) => {
    setPageSize(newPageSize);
    setPage(1);
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

        {isLoading && (
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

        {!isLoading && !isError && data && (
          <CDKTable
            data={data.data}
            total={data.total}
            page={page}
            pageSize={pageSize}
            onPageChange={handlePageChange}
            onPageSizeChange={handlePageSizeChange}
            onTypeChange={handleTypeChange}
            onStatusChange={handleStatusChange}
            onSearch={handleSearch}
          />
        )}
      </div>
    </div>
  );
}
