import { Activity, AlertCircle, DollarSign, Users, Zap, Wallet, BarChart3 } from 'lucide-react';
import { useState } from 'react';

import { CdkRechargeChart } from '@/components/charts/CdkRechargeChart';
import { TokenUsageChart } from '@/components/charts/TokenUsageChart';
import { UserGrowthChart } from '@/components/charts/UserGrowthChart';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useChartData, useDashboardOverview } from '@/hooks/useDashboard';
import { formatCurrency, formatNumber } from '@/utils/format';

export default function Dashboard() {
  const [chartDays, setChartDays] = useState<'7' | '30'>('7');

  const { data: overview, isLoading: overviewLoading, error: overviewError } = useDashboardOverview();
  const { data: chartData, isLoading: chartLoading } = useChartData(chartDays);

  // 错误处理
  if (overviewError) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">仪表盘</h1>
          <p className="text-muted-foreground">查看系统核心指标和趋势</p>
        </div>
        <Alert variant="destructive">
          <AlertCircle className="size-4" />
          <AlertTitle>加载失败</AlertTitle>
          <AlertDescription>
            无法加载仪表盘数据，请稍后重试。
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">仪表盘</h1>
        <p className="text-muted-foreground">查看系统核心指标和趋势</p>
      </div>

      {/* 统计卡片 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {/* 今日新增用户 */}
        {overviewLoading ? (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="size-4 rounded-full" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-16" />
              <Skeleton className="mt-1 h-3 w-32" />
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">今日新增用户</CardTitle>
              <Users className="size-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{overview?.today_new_users || 0}</div>
            </CardContent>
          </Card>
        )}

        {/* 活跃任务数 */}
        {overviewLoading ? (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="size-4 rounded-full" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-16" />
              <Skeleton className="mt-1 h-3 w-32" />
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">活跃任务数</CardTitle>
              <Zap className="size-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{overview?.active_tasks || 0}</div>
              <p className="text-xs text-muted-foreground">当前正在处理</p>
            </CardContent>
          </Card>
        )}

        {/* 今日积分消耗 */}
        {overviewLoading ? (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="size-4 rounded-full" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-16" />
              <Skeleton className="mt-1 h-3 w-32" />
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">今日积分消耗</CardTitle>
              <Activity className="size-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatNumber(overview?.today_points_consumed || 0)}
              </div>
              {/* <p className="text-xs text-muted-foreground">较昨日增长 8%</p> */}
            </CardContent>
          </Card>
        )}

        {/* 今日 CDK 兑换 */}
        {overviewLoading ? (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="size-4 rounded-full" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-16" />
              <Skeleton className="mt-1 h-3 w-32" />
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">今日 CDK 兑换</CardTitle>
              <DollarSign className="size-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatNumber(overview?.today_cdk_recharge || 0)}
              </div>
              <p className="text-xs text-muted-foreground">积分充值</p>
            </CardContent>
          </Card>
        )}

        {/* 总发放积分 */}
        {overviewLoading ? (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="size-4 rounded-full" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-16" />
              <Skeleton className="mt-1 h-3 w-32" />
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">总发放积分</CardTitle>
              <Wallet className="size-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatNumber(overview?.total_points_distributed || 0)}
              </div>
              <p className="text-xs text-muted-foreground">历史累计发放</p>
            </CardContent>
          </Card>
        )}

        {/* 总消耗积分 */}
        {overviewLoading ? (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="size-4 rounded-full" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-16" />
              <Skeleton className="mt-1 h-3 w-32" />
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">总消耗积分</CardTitle>
              <BarChart3 className="size-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatNumber(overview?.total_points_consumed || 0)}
              </div>
              <p className="text-xs text-muted-foreground">历史累计消耗</p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* 趋势图表 */}
      <Tabs value={chartDays} onValueChange={(v) => setChartDays(v as '7' | '30')}>
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">数据趋势</h2>
          <TabsList>
            <TabsTrigger value="7">近 7 天</TabsTrigger>
            <TabsTrigger value="30">近 30 天</TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value={chartDays} className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {chartLoading ? (
              <>
                <Card>
                  <CardHeader>
                    <Skeleton className="h-6 w-32" />
                  </CardHeader>
                  <CardContent>
                    <Skeleton className="h-[300px] w-full" />
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <Skeleton className="h-6 w-32" />
                  </CardHeader>
                  <CardContent>
                    <Skeleton className="h-[300px] w-full" />
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <Skeleton className="h-6 w-32" />
                  </CardHeader>
                  <CardContent>
                    <Skeleton className="h-[300px] w-full" />
                  </CardContent>
                </Card>
              </>
            ) : chartData && chartData.length > 0 ? (
              <>
                <UserGrowthChart data={chartData} />
                <TokenUsageChart data={chartData} />
                <CdkRechargeChart data={chartData} />
              </>
            ) : (
              <div className="col-span-3 rounded-lg border p-8 text-center">
                <p className="text-muted-foreground">暂无数据</p>
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
