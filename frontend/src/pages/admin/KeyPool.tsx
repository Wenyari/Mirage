import { Activity, AlertCircle, Plus } from 'lucide-react';
import { useState } from 'react';
import { toast } from 'sonner';

import { KeyAddDialog } from '@/components/admin/KeyAddDialog';
import { KeyEditDialog } from '@/components/admin/KeyEditDialog';
import { KeyPoolStats } from '@/components/admin/KeyPoolStats';
import { KeysTable } from '@/components/tables/KeysTable';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { useHealthCheck, useKeys, useModels } from '@/hooks/useKeys';
import type { Key,ModelType } from '@/types/key';

export default function KeyPool() {
  const [model, setModel] = useState<ModelType | undefined>();
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [editKey, setEditKey] = useState<Key | null>(null);

  // 获取密钥列表（5秒自动刷新）
  const { data, isLoading, isError, error } = useKeys(model);

  // 获取模型列表
  const { data: modelsData, isLoading: modelsLoading } = useModels();

  // 健康检测
  const healthCheckMutation = useHealthCheck();

  const handleHealthCheck = async () => {
    try {
      toast.info('开始健康检测...');
      const result = await healthCheckMutation.mutateAsync(model);

      if ((result as any).code === 0) {
        const { total, active, cooling, disabled } = result.data;
        toast.success(
          `健康检测完成：${total} 个密钥，${active} 可用，${cooling} 冷却中，${disabled} 已停用`
        );
      }
    } catch (err: any) {
      toast.error(err.message || '健康检测失败');
    }
  };

  const handleModelChange = (value: string) => {
    setModel(value === 'all' ? undefined : (value as ModelType));
  };

  const handleEdit = (key: Key) => {
    setEditKey(key);
    setShowEditDialog(true);
  };

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">密钥池管理</h1>
        <p className="mt-2 text-muted-foreground">
          管理 API 密钥，实时监控并发状态和熔断信息
        </p>
      </div>

      {/* 统计卡片 */}
      <KeyPoolStats />

      {/* 操作栏 */}
      <div className="flex flex-col gap-4 md:flex-row">
        <Button onClick={() => setShowAddDialog(true)}>
          <Plus className="mr-2 size-4" />
          添加密钥
        </Button>

        <Button
          variant="outline"
          onClick={handleHealthCheck}
          disabled={healthCheckMutation.isPending}
        >
          <Activity className="mr-2 size-4" />
          {healthCheckMutation.isPending ? '检测中...' : '健康检测'}
        </Button>

        <Select value={model || 'all'} onValueChange={handleModelChange}>
          <SelectTrigger className="md:w-48">
            <SelectValue placeholder="选择模型" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部模型</SelectItem>
            {modelsLoading ? (
              <SelectItem value="loading" disabled>
                加载中...
              </SelectItem>
            ) : (
              (modelsData as any)?.data
                ?.filter((p: any) => p.enabled)
                .map((model: any) => (
                  <SelectItem key={model.key} value={model.key}>
                    {model.name}
                  </SelectItem>
                ))
            )}
          </SelectContent>
        </Select>
      </div>

      {/* 密钥列表 */}
      <div className="space-y-4">
        <h2 className="text-2xl font-semibold">密钥列表</h2>

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
              {(error as any)?.message || '加载密钥列表失败'}
            </AlertDescription>
          </Alert>
        )}

        {!isLoading && !isError && data?.data && (
          <KeysTable data={data.data} onEdit={handleEdit} />
        )}
      </div>

      {/* 添加密钥对话框 */}
      <KeyAddDialog open={showAddDialog} onOpenChange={setShowAddDialog} />

      {/* 编辑密钥对话框 */}
      <KeyEditDialog open={showEditDialog} onOpenChange={setShowEditDialog} keyData={editKey} />
    </div>
  );
}
