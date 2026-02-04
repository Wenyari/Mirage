import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import api from '@/lib/api';
import { formatDateTime } from '@/utils/format';
import { cn } from '@/lib/utils';

// 交易类型配置
const TRANSACTION_TYPES = {
  'task_cost': { label: '消费', color: 'text-red-500', sign: '-' },
  'refund': { label: '退款', color: 'text-green-500', sign: '+' },
  'recharge': { label: '充值', color: 'text-blue-500', sign: '+' },
  'checkin': { label: '签到', color: 'text-green-500', sign: '+' },
  'activity_grant': { label: '活动奖励', color: 'text-green-500', sign: '+' },
  'activity_expire': { label: '活动过期', color: 'text-orange-500', sign: '-' },
  'system': { label: '系统调整', color: 'text-gray-500', sign: '?' },
} as const;

export default function Records() {
  const [transactions, setTransactions] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchTransactions = async () => {
    setIsLoading(true);
    try {
      const res: any = await api.get('/wallet/transactions?page=1&size=50');
      const list = res?.data?.list || res?.list || [];
      // 显示消费记录和退款记录
      setTransactions(list.filter((t: any) =>
        t.type === 'task_cost' || t.type === 'refund'
      ));
    } catch (e) {
      // ignore
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTransactions();
  }, []);

  return (
    <div className="space-y-6 p-6">
      <h2 className="text-xl font-semibold mb-4">使用记录</h2>

      <Card className="p-6">
        <div className="h-96 w-full overflow-auto rounded-md border">
          {isLoading ? (
            <div className="p-4 text-muted-foreground">加载中...</div>
          ) : transactions.length === 0 ? (
            <div className="p-4 text-muted-foreground">暂无扣费记录</div>
          ) : (
            <table className="w-full min-w-[500px]">
              <thead className="bg-muted/50 sticky top-0">
                <tr className="text-left text-sm text-muted-foreground border-b">
                  <th className="p-2 whitespace-nowrap">日期</th>
                  <th className="p-2 whitespace-nowrap">类型</th>
                  <th className="p-2 whitespace-nowrap">模型</th>
                  <th className="p-2 whitespace-nowrap">金额</th>
                  <th className="p-2 whitespace-nowrap">余额</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {transactions.map((t) => {
                  const typeConfig = TRANSACTION_TYPES[t.type as keyof typeof TRANSACTION_TYPES] || { label: t.type, color: '', sign: '' };
                  return (
                    <tr key={t.id} className="text-sm">
                      <td className="p-2 whitespace-nowrap">{formatDateTime(t.created_at)}</td>
                      <td className={cn("p-2 whitespace-nowrap font-medium", typeConfig.color)}>{typeConfig.label}</td>
                      <td className="p-2 whitespace-nowrap max-w-[150px] truncate" title={t.model}>{t.model || '-'}</td>
                      <td className={cn("p-2 whitespace-nowrap font-medium", typeConfig.color)}>
                        {typeConfig.sign}{Math.abs(t.amount)}
                      </td>
                      <td className="p-2 whitespace-nowrap">{t.balance_snapshot}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </Card>
    </div>
  );
}


