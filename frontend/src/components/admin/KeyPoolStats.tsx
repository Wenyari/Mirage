import { Activity, AlertCircle, CheckCircle, Clock } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useKeyStats, usePlatforms } from '@/hooks/useKeys';

export function KeyPoolStats() {
  const { data, isLoading, isError, error } = useKeyStats();
  const { data: platformsData } = usePlatforms();

  // 创建平台名称映射
  const platformMap = new Map(
    platformsData?.data?.map((p) => [p.key, p.name]) || []
  );

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-32" />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>{(error as any)?.message || '加载统计数据失败'}</AlertDescription>
      </Alert>
    );
  }

  if (!data?.data) return null;

  const stats = data.data;

  // 计算总体数据
  const totalKeys = stats.by_platform.reduce((sum, p) => sum + p.total_keys, 0);
  const totalActive = stats.by_platform.reduce((sum, p) => sum + p.active_keys, 0);
  const totalCooling = stats.by_platform.reduce((sum, p) => sum + p.cooling_keys, 0);
  const totalConcurrency = stats.by_platform.reduce((sum, p) => sum + p.total_concurrency, 0);
  const totalUsage = stats.by_platform.reduce((sum, p) => sum + p.current_usage, 0);
  const usageRate = totalConcurrency > 0 ? (totalUsage / totalConcurrency) * 100 : 0;

  return (
    <div className="space-y-4">
      {/* 顶部总览卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">总密钥数</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalKeys}</div>
            <p className="text-xs text-muted-foreground mt-1">
              <span className="text-green-600">{totalActive} 可用</span>
              {totalCooling > 0 && (
                <span className="ml-2 text-red-600">{totalCooling} 冷却中</span>
              )}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">并发槽位</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {totalUsage} / {totalConcurrency}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              使用率：
              <span className={usageRate >= 80 ? 'text-red-600' : usageRate >= 60 ? 'text-yellow-600' : 'text-green-600'}>
                {usageRate.toFixed(1)}%
              </span>
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">今日调用</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_calls_today.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground mt-1">
              失败：{stats.total_errors_today.toLocaleString()}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">错误率</CardTitle>
            <AlertCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.error_rate.toFixed(2)}%</div>
            <p className={`text-xs mt-1 ${stats.error_rate < 1 ? 'text-green-600' : stats.error_rate < 5 ? 'text-yellow-600' : 'text-red-600'}`}>
              {stats.error_rate < 1 ? '状态良好' : stats.error_rate < 5 ? '需要关注' : '异常偏高'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 按平台统计 */}
      <Card>
        <CardHeader>
          <CardTitle>平台分布</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {stats.by_platform.filter(p => p.total_keys > 0).map((platform) => {
              const platformUsageRate = platform.total_concurrency > 0
                ? (platform.current_usage / platform.total_concurrency) * 100
                : 0;

              return (
                <div key={platform.platform} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Badge variant="outline">
                      {platformMap.get(platform.platform) || platform.platform}
                    </Badge>
                    <span className="text-sm text-muted-foreground">
                      {platform.total_keys} 个密钥
                    </span>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-sm">
                      <span className="text-green-600">{platform.active_keys} 可用</span>
                      {platform.cooling_keys > 0 && (
                        <span className="ml-2 text-red-600">{platform.cooling_keys} 冷却</span>
                      )}
                    </div>
                    <div className="text-sm font-medium">
                      {platform.current_usage} / {platform.total_concurrency}
                      <span className="ml-1 text-xs text-muted-foreground">
                        ({platformUsageRate.toFixed(0)}%)
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
