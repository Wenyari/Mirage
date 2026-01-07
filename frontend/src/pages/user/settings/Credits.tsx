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
// Link not used in this page; sidebar is provided by SettingsLayout
import api from '@/lib/api';
import { useAuthStore } from '@/store/authStore';
import { authService } from '@/services/auth';

export default function Credits() {
  const [code, setCode] = useState('');
  const [transactions, setTransactions] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [balance, setBalance] = useState<number | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogMsg, setDialogMsg] = useState('');
  const [dialogSuccess, setDialogSuccess] = useState(false);
  const [purchaseOpen, setPurchaseOpen] = useState(false);
  const { user, setUser } = useAuthStore();

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
        const upgraded = res.data?.upgraded_to;
        let successMsg = `兑换成功，获得 ${added ?? '0'} 积分`;
        if (upgraded) {
          successMsg += `，并升级至 T${upgraded}`;
        }
        setDialogMsg(successMsg);
        setDialogSuccess(true);
        setDialogOpen(true);
        if (current !== undefined && current !== null) {
          setBalance(Number(current));
        }

        // 刷新全局用户信息（余额/等级等）
        try {
          const me = await authService.me();
          if (me) setUser(me);
        } catch (err) {
          // ignore
        }
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
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
      <div className="flex-1">
          <Card className="p-6">
            <h3 className="font-semibold mb-2">充值积分</h3>
            <Button onClick={() => setPurchaseOpen(true)}>立即充值</Button>
            <Dialog open={purchaseOpen} onOpenChange={setPurchaseOpen}>
            <DialogContent className="max-w-6xl w-[95vw]">
                <DialogTitle>选择充值套餐</DialogTitle>
                <DialogDescription>请选择适合你的充值包。</DialogDescription>
                <div className="mt-4 grid grid-cols-4 gap-6">
                  {[
                    {
                      title: '体验包',
                      price: '¥9.9',
                      bullets: ['100 积分', '解锁T2权限'],
                    },
                    {
                      title: 'T3体验包',
                      price: '¥29.9',
                      bullets: ['360 积分 (送60)', '解锁T3权限', '解锁电影级 Pro 模型','Sora-2可享8折优惠'],
                      limited: true,
                    },
                    {
                      title: '标准包',
                      price: '¥49.9',
                      bullets: ['550 积分 (送50)', '解锁T3权限','解锁电影级 Pro 模型','Sora-2可享8折优惠'],
                    },
                    {
                      title: '专业包',
                      price: '¥199',
                      bullets: ['2300 积分 (送300)', '解锁T4权限','Sora-2低至6折优惠'],
                    },
                  ].map((pkg) => (
                    <div
                      key={pkg.title}
                      className="relative border rounded-xl p-6 text-center flex flex-col justify-between min-w-[260px]"
                    >
                      {pkg.limited && (
                        <div className="absolute -top-3 right-3">
                          <span className="bg-orange-400 text-white text-xs px-2 py-1 rounded-full">用户每周限购一次！</span>
                        </div>
                      )}
                      <div>
                        <div className="text-sm text-muted-foreground">{pkg.title}</div>
                        <div className="text-2xl font-bold my-4">{pkg.price}</div>
                        <ul className="text-sm text-left list-inside space-y-1 text-muted-foreground">
                          {pkg.bullets.map((b: string) => (
                            <li key={b} className="flex items-start gap-2">
                              <span className="text-green-500">✔</span>
                              <span>{b}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div className="mt-4">
                        <Button className="w-full">立即购买</Button>
                      </div>
                    </div>
                  ))}
                </div>

                <DialogFooter>
                  <DialogClose asChild>
                    <Button onClick={() => setPurchaseOpen(false)}>关闭</Button>
                  </DialogClose>
                </DialogFooter>
              </DialogContent>
            </Dialog>
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
  );
}


