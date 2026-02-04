import { useQueryClient } from '@tanstack/react-query';
import { Lock, LogIn, Mail } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

import GeetestCaptcha from '@/components/auth/GeetestCaptcha';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { USER_NAVIGATION } from '@/config/user-navigation';
import { authService, GeetestParams } from '@/services/auth';
import { useAuthStore } from '@/store/authStore';

export default function UserLogin() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const login = useAuthStore((state) => state.login);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [geetestParams, setGeetestParams] = useState<GeetestParams | null>(null);
  const [countdown, setCountdown] = useState(0);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (countdown > 0) {
      timer = setTimeout(() => setCountdown((c) => c - 1), 1000);
    }
    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [countdown]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      toast.error('请输入邮箱和密码');
      return;
    }

    if (!geetestParams) {
      toast.error('请完成人机验证');
      return;
    }

    try {
      setIsLoading(true);
      const response = await authService.login({
        email,
        password,
        ...geetestParams
      });

      // 清除旧的查询缓存，确保新用户数据能被正确获取
      queryClient.clear();

      // 更新全局 Auth Store
      login((response as any).token, (response as any).user);

      toast.success('登录成功');
      navigate(USER_NAVIGATION.HOME.path);
    } catch (error: any) {
      toast.error(error.data.msg || '登录失败，请检查邮箱或密码');
      // 验证失败通常需要重置验证码，但 Geetest v4 可能不需要重置整个组件，
      // 除非是 session 过期。为了简单，这里清空 params 要求重新验证。
      setGeetestParams(null);
      // 注意：UI 上 Geetest 可能会显示错误或重置状态，
      // 如果需要手动重置 Geetest 组件，可能需要 ref。
      // 为简化集成，暂不处理自动重置 UI，用户需再次点击验证。
      setCountdown(10);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-[calc(100dvh-3.5rem)] items-center justify-center bg-muted/40 px-4 py-8">
      <Card className="w-full max-w-md shadow-lg">
        <CardHeader className="space-y-1 text-center">
          <div className="mb-2 flex justify-center">
            <div className="rounded-full bg-primary/10 p-3">
              <LogIn className="size-6 text-primary" />
            </div>
          </div>
          <CardTitle className="text-2xl font-bold tracking-tight">{USER_NAVIGATION.AUTH.LOGIN.label}</CardTitle>
          <CardDescription>
            请输入您的账号和密码登录 GoGen
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleLogin}>
          <CardContent className="grid gap-5">
            <div className="grid gap-2">
              <Label htmlFor="email" className="text-sm font-medium">邮箱</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-2.5 size-4 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  placeholder="name@example.com"
                  required
                  className="pl-9"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
            </div>
            <div className="grid gap-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password" className="text-sm font-medium">密码</Label>
                {/* 预留忘记密码链接位置 */}
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 size-4 text-muted-foreground" />
                <Input
                  id="password"
                  type="password"
                  placeholder="请输入您的密码"
                  required
                  className="pl-9"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            </div>
            <div className="flex justify-center py-2">
              <GeetestCaptcha
                onVerify={(params) => setGeetestParams(params)}
                onError={() => setGeetestParams(null)}
              />
            </div>
          </CardContent>
          <CardFooter className="flex flex-col gap-4 pt-2">
            <Button className="w-full text-base font-semibold shadow-sm" type="submit" disabled={isLoading || !geetestParams || countdown > 0} size="lg">
              {isLoading ? '登录中...' : (countdown > 0 ? `登录 (${countdown}s)` : '登录')}
            </Button>
            <div className="flex items-center justify-center gap-1 text-sm text-muted-foreground">
              <span>还没有账号？</span>
              <Link
                to={USER_NAVIGATION.AUTH.REGISTER.path}
                className="font-medium text-primary transition-all hover:underline"
              >
                立即注册
              </Link>
            </div>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
