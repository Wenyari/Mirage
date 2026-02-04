import { CheckCircle2, KeyRound, Lock, Mail, UserPlus } from 'lucide-react';
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

export default function UserRegister() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSendingCode, setIsSendingCode] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const [isRegistering, setIsRegistering] = useState(false);
  const [geetestParams, setGeetestParams] = useState<GeetestParams | null>(null);
  const [registerCountdown, setRegisterCountdown] = useState(0);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (registerCountdown > 0) {
      timer = setTimeout(() => setRegisterCountdown((c) => c - 1), 1000);
    }
    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [registerCountdown]);

  // 发送验证码
  const handleSendCode = async () => {
    if (!email) {
      toast.error('请输入邮箱地址');
      return;
    }

    if (!geetestParams) {
      toast.error('请完成人机验证');
      return;
    }

    // 简单的邮箱格式校验
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      toast.error('请输入有效的邮箱地址');
      return;
    }

    try {
      setIsSendingCode(true);
      await authService.sendCode({
        email,
        ...geetestParams
      });
      toast.success('验证码已发送，请查收邮箱');

      // 开始倒计时
      setCountdown(60);
      const timer = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(timer);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } catch (error: any) {
      toast.error(error.data.msg || '发送验证码失败');
      setGeetestParams(null); // 重置验证码
    } finally {
      setIsSendingCode(false);
    }
  };

  // 注册提交
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !code || !password || !confirmPassword) {
      toast.error('请填写完整信息');
      return;
    }

    if (password !== confirmPassword) {
      toast.error('两次输入的密码不一致');
      return;
    }

    try {
      setIsRegistering(true);
      await authService.register({ email, code, password });
      toast.success('注册成功，请登录');
      navigate(USER_NAVIGATION.AUTH.LOGIN.path);
    } catch (error: any) {
      toast.error(error.data.msg || '注册失败');
      setRegisterCountdown(10);
    } finally {
      setIsRegistering(false);
    }
  };

  return (
    <div className="flex min-h-[calc(100vh-3.5rem)] items-center justify-center bg-muted/40 px-4 py-8">
      <Card className="w-full max-w-md shadow-lg">
        <CardHeader className="space-y-1 text-center">
          <div className="mb-2 flex justify-center">
            <div className="rounded-full bg-primary/10 p-3">
              <UserPlus className="size-6 text-primary" />
            </div>
          </div>
          <CardTitle className="text-2xl font-bold tracking-tight">{USER_NAVIGATION.AUTH.REGISTER.label}</CardTitle>
          <CardDescription>
            创建一个新账号以开始使用 GoGen
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleRegister}>
          <CardContent className="grid gap-5">
            {/* 邮箱输入与验证码发送 */}
            <div className="grid gap-2">
              <Label htmlFor="email" className="text-sm font-medium">邮箱地址</Label>
              <div className="relative flex gap-2">
                <div className="relative flex-1">
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
                <Button
                  type="button"
                  variant="secondary"
                  className="w-28 px-0 font-medium"
                  onClick={handleSendCode}
                  disabled={isSendingCode || countdown > 0 || !geetestParams}
                >
                  {countdown > 0 ? `${countdown}s` : (isSendingCode ? '发送中' : '获取验证码')}
                </Button>
              </div>

              {/* Geetest 放置在邮箱输入框下方，作为一个验证步骤 */}
              <div className="flex justify-center py-2">
                <GeetestCaptcha
                  onVerify={(params) => setGeetestParams(params)}
                  onError={() => setGeetestParams(null)}
                />
              </div>
            </div>

            {/* 验证码输入 */}
            <div className="grid gap-2">
              <Label htmlFor="code" className="text-sm font-medium">验证码</Label>
              <div className="relative">
                <KeyRound className="absolute left-3 top-2.5 size-4 text-muted-foreground" />
                <Input
                  id="code"
                  type="text"
                  placeholder="请输入6位验证码"
                  required
                  className="pl-9 tracking-widest"
                  maxLength={6}
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                />
              </div>
            </div>

            {/* 密码输入 */}
            <div className="grid gap-2">
              <Label htmlFor="password" className="text-sm font-medium">设置密码</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 size-4 text-muted-foreground" />
                <Input
                  id="password"
                  type="password"
                  placeholder="设置您的登录密码"
                  required
                  className="pl-9"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            </div>

            {/* 确认密码 */}
            <div className="grid gap-2">
              <Label htmlFor="confirmPassword" className="text-sm font-medium">确认密码</Label>
              <div className="relative">
                <CheckCircle2 className="absolute left-3 top-2.5 size-4 text-muted-foreground" />
                <Input
                  id="confirmPassword"
                  type="password"
                  placeholder="再次输入密码"
                  required
                  className="pl-9"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                />
              </div>
            </div>

          </CardContent>
          <CardFooter className="flex flex-col gap-4 pt-2">
            <Button className="w-full text-base font-semibold shadow-sm" type="submit" disabled={isRegistering || registerCountdown > 0} size="lg">
              {isRegistering ? '正在注册...' : (registerCountdown > 0 ? `立即注册 (${registerCountdown}s)` : '立即注册')}
            </Button>
            <div className="flex items-center justify-center gap-1 text-sm text-muted-foreground">
              <span>已有账号？</span>
              <Link
                to={USER_NAVIGATION.AUTH.LOGIN.path}
                className="font-medium text-primary transition-all hover:underline"
              >
                直接登录
              </Link>
            </div>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
