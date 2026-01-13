import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { useCurrentUser } from '@/hooks/useCurrentUser';

type Tier = {
  key: string;
  title: string;
  level: number; // numeric level: 0=免费, 1=T1 ... 5=T5(企业)
  bullets: string[];
};

const TIERS: Tier[] = [
  {
    key: 'T1',
    title: 'T1  免费用户',
    level: 1,
    bullets: [ '基础图片模型' , '累计签到积分10'],
  },
  {
    key: 'T2',
    title: 'T2 基础会员',
    level: 2,
    bullets: [ '基础图片模型', '基础视频模型','每日签到5积分'],
  },
  {
    key: 'T3',
    title: 'T3高级会员',
    level: 3,
    bullets: ['基础图片模型', '基础视频模型','电影级 Pro 模型','Sora-2可享8折优惠','每日签到10积分'],
  },
  {
    key: 'T4',
    title: 'T4pro会员',
    level: 4,
    bullets: [ '基础图片模型', '基础视频模型',  '电影级 Pro 模型', '新模型优先体验','Sora-2可享6折优惠','每日签到15积分'],
  },
  {
    key: 'T5',
    title: 'T5  企业用户',
    level: 5,
    bullets: ['图片/视频任务并发: 定制', '基础图片/视频模型', '工作流定制'],
  },
];

export default function Tiers() {
  const navigate = useNavigate();
  const { data: currentUser } = useCurrentUser();

  const currentLevel = currentUser ? Number(currentUser.level ?? 0) : 0;

  const tiersToRender = useMemo(() => TIERS, []);

  return (
    <div className="space-y-6 p-6">
      <div className="text-center">
        <h1 className="text-2xl font-bold">账号层级</h1>
        <p className="text-sm text-muted-foreground">根据账号层级，每日可使用权益通道的次数</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-6 items-stretch">
        {tiersToRender.map((tier) => {
          const isCurrent = tier.level === currentLevel;
          const isOwned = tier.level < currentLevel;
          const isHigher = tier.level > currentLevel;

          const baseCard = 'rounded-lg border p-6 flex flex-col justify-between h-full transition-transform duration-200';
          const currentModifiers = 'transform scale-105 md:scale-110 z-10 border-2 border-primary shadow-lg';
          const cardClass = [baseCard, isCurrent ? currentModifiers : 'bg-white'].join(' ');

          return (
            <Card key={tier.key} className={cardClass}>
              <CardHeader>
                <CardTitle className="text-lg">{tier.key}</CardTitle>
                <CardDescription className="mt-1">{tier.title}</CardDescription>
              </CardHeader>

              <CardContent className="mt-4 flex-1">
                <ul className="space-y-2 text-sm text-muted-foreground">
                  {tier.bullets.map((b) => (
                    <li key={b} className="flex items-start gap-2">
                      <span className="text-green-500">✔</span>
                      <span>{b}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>

              <div className="mt-4">
                {tier.level === 5 ? (
                  // Enterprise special case: contact customization
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => {
                      // fallback: navigate to contact page if exists or open mail
                      if (typeof window !== 'undefined') {
                        window.location.href = 'mailto:business@example.com';
                      }
                    }}
                  >
                    联系定制
                  </Button>
                ) : isCurrent ? (
                  <Button className="w-full" disabled>
                    当前层级
                  </Button>
                ) : isOwned ? (
                  <Button className="w-full" variant="ghost" disabled>
                    已拥有
                  </Button>
                ) : (
                  <Button
                    className="w-full"
                    onClick={() => {
                      // go to recharge/credits page
                      navigate('/setting/credits');
                    }}
                  >
                    去充值
                  </Button>
                )}
              </div>
            </Card>
          );
        })}
      </div>

      <Separator />
      <div className="text-sm text-muted-foreground">
        提示：若需更详细的企业方案请点击「联系定制」，团队会与您对接。
      </div>
    </div>
  );
}
