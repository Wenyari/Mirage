import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import api from '@/lib/api';
import { formatDateTime } from '@/utils/format';

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
        <ScrollArea className="h-96">
          {isLoading ? (
            <div className="text-muted-foreground">加载中...</div>
          ) : transactions.length === 0 ? (
            <div className="text-muted-foreground">暂无扣费记录</div>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="text-left">
                  <th>日期</th>
                  <th>类型</th>
                  <th>模型</th>
                  <th>金额</th>
                  <th>余额</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((t) => {
                  const typeConfig = TRANSACTION_TYPES[t.type as keyof typeof TRANSACTION_TYPES] || { label: t.type, color: '', sign: '' };
                  return (
                    <tr key={t.id}>
                      <td>{formatDateTime(t.created_at)}</td>
                      <td className={typeConfig.color}>{typeConfig.label}</td>
                      <td>{t.model || '-'}</td>
                      <td className={typeConfig.color}>
                        {typeConfig.sign}{Math.abs(t.amount)}
                      </td>
                      <td>{t.balance_snapshot}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </ScrollArea>
      </Card>
    </div>
  );
}


