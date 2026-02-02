import { Coins, CreditCard, Gift, History, Wallet, Zap } from 'lucide-react';
import { useEffect, useState } from 'react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
// Link not used in this page; sidebar is provided by SettingsLayout
import api from '@/lib/api';
import { authService } from '@/services/auth';
import { useAuthStore } from '@/store/authStore';
import { useQueryClient } from '@tanstack/react-query';
import { CURRENT_USER_QUERY_KEY } from '@/hooks/useCurrentUser';
import wechatJpg from '@/assets/wechat.jpg';

export default function Credits() {
  const queryClient = useQueryClient();
  const [code, setCode] = useState('');
  const [transactions, setTransactions] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [balanceDetail, setBalanceDetail] = useState<{
    total_balance: number;
    recharge_balance: number;
    activity_balance: number;
  } | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogMsg, setDialogMsg] = useState('');
  const [dialogSuccess, setDialogSuccess] = useState(false);
  const [purchaseOpen, setPurchaseOpen] = useState(false);
  const [paymentQROpen, setPaymentQROpen] = useState(false);
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
          // setBalance(Number(current)); // Balance update is now handled by fetching balance again or updating detail
          fetchBalance();
        }

        // 刷新全局用户信息（余额/等级等）
        try {
          // Invalidate the current user query to trigger a refetch in UserNavbar
          queryClient.invalidateQueries({ queryKey: CURRENT_USER_QUERY_KEY });

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
      // console.log('Wallet balance response:', res);

      // 兼容两种响应结构：
      // 1. 标准结构 { code: 200, data: { ... } } -> res.data 是目标对象
      // 2. 直接返回数据结构 { total_balance: ... } -> res 是目标对象
      const data = res?.data || res;

      if (data && (typeof data.total_balance === 'number' || typeof data.balance === 'number')) {
        setBalanceDetail({
          total_balance: data.total_balance ?? data.balance ?? 0,
          recharge_balance: data.recharge_balance ?? 0,
          activity_balance: data.activity_balance ?? 0,
        });
      }
    } catch (e) {
      console.error('Fetch balance failed:', e);
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
            <h3 className="mb-2 flex items-center gap-2 font-semibold">
              <CreditCard className="size-5 text-primary" />
              充值积分
            </h3>
            <Button onClick={() => setPurchaseOpen(true)}>立即充值</Button>
            <Dialog open={purchaseOpen} onOpenChange={setPurchaseOpen}>
              <DialogContent className="w-[95vw] max-w-6xl">
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
                      bullets: ['360 积分 (送60)', '解锁T3权限', '解锁电影级 Pro 模型', 'Sora-2可享8折优惠'],
                      limited: true,
                    },
                    {
                      title: '标准包',
                      price: '¥49.9',
                      bullets: ['550 积分 (送50)', '解锁T3权限', '解锁电影级 Pro 模型', 'Sora-2可享8折优惠'],
                    },
                    {
                      title: '专业包',
                      price: '¥199',
                      bullets: ['2300 积分 (送300)', '解锁T4权限', 'Sora-2低至6折优惠'],
                    },
                  ].map((pkg) => (
                    <div
                      key={pkg.title}
                      className="relative flex min-w-[260px] flex-col justify-between rounded-xl border p-6 text-center"
                    >
                      {pkg.limited && (
                        <div className="absolute -top-3 right-3">
                          <span className="rounded-full bg-orange-400 px-2 py-1 text-xs text-white">用户每周限购一次！</span>
                        </div>
                      )}
                      <div>
                        <div className="text-sm text-muted-foreground">{pkg.title}</div>
                        <div className="my-4 text-2xl font-bold">{pkg.price}</div>
                        <ul className="list-inside space-y-1 text-left text-sm text-muted-foreground">
                          {pkg.bullets.map((b: string) => (
                            <li key={b} className="flex items-start gap-2">
                              <span className="text-green-500">✔</span>
                              <span>{b}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div className="mt-4">
                        <Button
                          className="w-full"
                          onClick={() => {
                            setPurchaseOpen(false);
                            setPaymentQROpen(true);
                          }}
                        >
                          立即购买
                        </Button>
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

            {/* 扫码支付弹窗 */}
            <Dialog open={paymentQROpen} onOpenChange={setPaymentQROpen}>
              <DialogContent className="sm:max-w-lg">
                <DialogTitle className="hidden">扫码支付</DialogTitle>
                <DialogDescription className="text-center text-lg font-medium">
                  请添加客服微信完成支付
                </DialogDescription>
                <div className="flex justify-center py-4">
                  <img src={wechatJpg} alt="WeChat Pay" className="h-auto w-full max-w-[400px] object-contain" />
                </div>
                <DialogFooter>
                  <DialogClose asChild>
                    <Button onClick={() => setPaymentQROpen(false)}>关闭</Button>
                  </DialogClose>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </Card>
        </div>
        <div className="w-64">
          <Card className="p-4">
            <div className="mb-2 flex items-center gap-2 text-sm text-muted-foreground">
              <Wallet className="size-4" />
              当前积分余额
            </div>
            <div className="text-2xl font-bold text-primary">
              {balanceDetail ? `${balanceDetail.total_balance.toFixed(2)}` : '—'}
            </div>
            {balanceDetail && (
              <div className="mt-3 space-y-2 text-xs text-muted-foreground">
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1">
                    <Coins className="size-3 text-yellow-500" />
                    充值余额:
                  </span>
                  <span className="font-medium">{balanceDetail.recharge_balance.toFixed(2)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1">
                    <Zap className="size-3 text-blue-500" />
                    活动余额:
                  </span>
                  <span className="font-medium">{balanceDetail.activity_balance.toFixed(2)}</span>
                </div>
              </div>
            )}
          </Card>
        </div>
      </div>

      <Card className="p-6">
        <h3 className="mb-4 flex items-center gap-2 font-semibold">
          <Gift className="size-5 text-purple-500" />
          卡密兑换
        </h3>
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
        <h4 className="mb-4 flex items-center gap-2 font-semibold">
          <History className="size-5 text-gray-500" />
          最近交易
        </h4>
        <ScrollArea className="h-48">
          {transactions.filter((t) => t.type === 'recharge').length === 0 ? (
            <div className="text-muted-foreground">暂无充值记录</div>
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
                {transactions
                  .filter((t) => t.type === 'recharge')
                  .map((t) => (
                    <tr key={t.id}>
                      <td>{t.created_at}</td>
                      <td>
                        {t.type}
                        {t.balance_type && <span className="ml-1 text-xs text-gray-500">({t.balance_type})</span>}
                      </td>
                      <td>{t.amount}</td>
                      <td>{t.remark || t.reason || '-'}</td>
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


