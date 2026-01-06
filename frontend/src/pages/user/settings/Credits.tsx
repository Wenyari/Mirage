import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { toast } from 'sonner';
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from '@/components/ui/dialog';
import { Link } from 'react-router-dom';
import api from '@/lib/api';

export default function Credits() {
  const [code, setCode] = useState('');
  const [transactions, setTransactions] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [balance, setBalance] = useState<number | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogMsg, setDialogMsg] = useState('');
  const [dialogSuccess, setDialogSuccess] = useState(false);

  const translateFailure = (msg: string) => {
    if (!msg) return '兑换失败';
    const low = msg.toLowerCase();
    if (low.includes('already been used') || low.includes('has already been used') || low.includes('已使用')) {
      return '兑换失败：该兑换码已被使用';
    }
    if (low.includes('invalidated') || low.includes('has been invalidated') || low.includes('已作废') || low.includes('失效')) {
      return '兑换失败：该兑换码已失效';
    }
    if (low.includes('invalid') || low.includes('invalid cdk') || low.includes('不存在') || low.includes('invalid cdk code')) {
      return '兑换失败：该兑换码不存在';
    }
    if (low.includes('expired') || low.includes('has expired') || low.includes('已过期')) {
      return '兑换失败：该兑换码已过期';
    }
    // fallback: show original message
    return `兑换失败：${msg}`;
  };

  const handleRedeem = async () => {
    if (!code) {
      toast.error('请输入兑换码');
      return;
    }
    try {
      setIsLoading(true);
      const res: any = await api.post('/wallet/redeem', { code });
      // res is { code, msg, data: { added_points, current_balance } }
      if (res && res.code === 200) {
        const added = res.data?.added_points;
        const current = res.data?.current_balance;
        const successMsg = `兑换成功，获得 ${added ?? '0'} 积分`;
        setDialogMsg(successMsg);
        setDialogSuccess(true);
        setDialogOpen(true);
        if (current !== undefined && current !== null) setBalance(Number(current));
      } else {
        const msg = res?.msg || '兑换失败';
        const zh = translateFailure(String(msg));
        setDialogMsg(zh);
        setDialogSuccess(false);
        setDialogOpen(true);
        toast.error(zh);
      }
      setCode('');
      fetchTransactions();
    } catch (e: any) {
      // api.ts rejects with an object that may contain `data` or `response.data`
      const raw =
        e?.data?.msg ??
        e?.data?.message ??
        e?.response?.data?.msg ??
        e?.response?.data?.message ??
        e?.message ??
        '兑换失败';
      const zh = translateFailure(String(raw));
      setDialogMsg(zh);
      setDialogSuccess(false);
      setDialogOpen(true);
      toast.error(zh);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchTransactions = async () => {
    try {
      const res = await api.get('/wallet/transactions');
      // res: { code, msg, data: { list, total, page, size } }
      const list = res?.data?.list || [];
      setTransactions(list);
    } catch (e) {
      // ignore
    }
  };

  const fetchBalance = async () => {
    try {
      const res = await api.get('/wallet/balance');
      const b = res?.data?.balance ?? null;
      setBalance(b);
    } catch (e) {
      // ignore
    }
  };

  useEffect(() => {
    fetchTransactions();
    fetchBalance();
  }, []);

  return (
    <div className="flex gap-6 p-6">
      <div className="w-64">
        <div className="mb-6">
          <h4 className="text-lg font-semibold">设置</h4>
        </div>
        <nav className="flex flex-col space-y-1">
          <Link to="/setting/account" className="px-4 py-2 rounded hover:bg-muted/50">账号设置</Link>
          <Link to="/setting/apikey" className="px-4 py-2 rounded hover:bg-muted/50">API 秘钥</Link>
          <Link to="/setting/credits" className="px-4 py-2 rounded bg-muted/20">充值与兑换</Link>
          <Link to="/setting/records" className="px-4 py-2 rounded hover:bg-muted/50">使用记录</Link>
          <Link to="/setting/tiers" className="px-4 py-2 rounded hover:bg-muted/50">账号层级</Link>
          <Link to="/setting/help" className="px-4 py-2 rounded hover:bg-muted/50">支持与帮助</Link>
        </nav>
      </div>

      <div className="flex-1 space-y-6">
        <div className="flex items-center justify-between gap-4">
          <div className="flex-1">
            <Card className="p-6">
              <h3 className="font-semibold mb-2">充值积分</h3>
              <Button onClick={() => window.open('/pay', '_blank')}>立即充值</Button>
            </Card>
          </div>
          <div className="w-64">
            <Card className="p-4">
              <div className="text-sm text-muted-foreground">当前积分余额</div>
              <div className="text-2xl font-bold">{balance !== null ? `${balance.toFixed(2)}` : '—'}</div>
            </Card>
          </div>
        </div>

        <Card className="p-6">
          <h3 className="font-semibold mb-2">卡密兑换</h3>
          <div className="flex gap-2">
            <Input value={code} onChange={(e) => setCode(e.target.value)} placeholder="输入兑换码" />
            <Button onClick={handleRedeem} disabled={isLoading}>{isLoading ? '兑换中' : '兑换'}</Button>
          </div>
        </Card>

        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogContent>
            <DialogTitle>{dialogSuccess ? '兑换成功' : '兑换结果'}</DialogTitle>
            <DialogDescription>
              {dialogMsg}
            </DialogDescription>
            <DialogFooter>
              <DialogClose asChild>
                <Button onClick={() => setDialogOpen(false)}>确定</Button>
              </DialogClose>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <Card className="p-6">
          <h4 className="font-semibold mb-4">最近交易</h4>
          <ScrollArea className="h-48">
            {transactions.length === 0 ? (
              <div className="text-muted-foreground">暂无交易记录</div>
            ) : (
              <table className="w-full">
                <thead>
                  <tr className="text-left">
                    <th>日期</th>
                    <th>类型</th>
                    <th>积分</th>
                    <th>说明</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.map((t) => (
                    <tr key={t.id}>
                      <td>{t.created_at}</td>
                      <td>{t.type}</td>
                      <td>{t.amount}</td>
                      <td>{t.remark}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </ScrollArea>
        </Card>
      </div>
    </div>
  );
}


