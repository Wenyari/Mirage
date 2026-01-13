import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import api from '@/lib/api';

export default function Records() {
  const [transactions, setTransactions] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchTransactions = async () => {
    setIsLoading(true);
    try {
      const res: any = await api.get('/wallet/transactions?page=1&size=50');
      const list = res?.data?.list || res?.list || [];
      // only show deduction records (task_cost)
      setTransactions(list.filter((t: any) => t.type === 'task_cost'));
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
                  <th>模型</th>
                  <th>功能</th>
                  <th>花费</th>
                  <th>余额</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((t) => (
                  <tr key={t.id}>
                    <td>{t.created_at}</td>
                    <td>{t.model || '-'}</td>
                    <td>{t.type}</td>
                    <td>{t.amount}</td>
                    <td>{t.balance_snapshot}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </ScrollArea>
      </Card>
    </div>
  );
}


