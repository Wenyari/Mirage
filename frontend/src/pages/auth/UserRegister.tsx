import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { USER_NAVIGATION } from '@/config/user-navigation';
import { authService } from '@/services/auth';

export default function UserRegister() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [password, setPassword] = useState('');
  const [isSendingCode, setIsSendingCode] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const [isRegistering, setIsRegistering] = useState(false);

  // 发送验证码
  const handleSendCode = async () => {
    if (!email) {
      toast.error('请输入邮箱地址');
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
      await authService.sendCode({ email });
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
      toast.error(error.message || '发送验证码失败');
    } finally {
      setIsSendingCode(false);
    }
  };

  // 注册提交
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !code || !password) {
      toast.error('请填写完整信息');
      return;
    }

    try {
      setIsRegistering(true);
      await authService.register({ email, code, password });
      toast.success('注册成功，请登录');
      navigate(USER_NAVIGATION.AUTH.LOGIN.path);
    } catch (error: any) {
      toast.error(error.message || '注册失败');
    } finally {
      setIsRegistering(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/40 px-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle className="text-2xl">{USER_NAVIGATION.AUTH.REGISTER.label}</CardTitle>
          <CardDescription>
            创建一个新账号以开始使用 Mirage
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleRegister}>
          <CardContent className="grid gap-4">
            <div className="grid gap-2">
              <Label htmlFor="email">邮箱</Label>
              <div className="flex gap-2">
                <Input 
                  id="email" 
                  type="email" 
                  placeholder="m@example.com" 
                  required 
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
                <Button 
                  type="button" 
                  variant="outline" 
                  className="w-24 px-0"
                  onClick={handleSendCode}
                  disabled={isSendingCode || countdown > 0}
                >
                  {countdown > 0 ? `${countdown}s` : (isSendingCode ? '发送中' : '获取验证码')}
                </Button>
              </div>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="code">验证码</Label>
              <Input 
                id="code" 
                type="text" 
                placeholder="6位验证码" 
                required 
                value={code}
                onChange={(e) => setCode(e.target.value)}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="password">密码</Label>
              <Input 
                id="password" 
                type="password" 
                required 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </CardContent>
          <CardFooter className="flex flex-col gap-2">
            <Button className="w-full" type="submit" disabled={isRegistering}>
              {isRegistering ? '注册中...' : '注册'}
            </Button>
            <div className="text-center text-sm text-muted-foreground">
              已有账号？{' '}
              <Link to={USER_NAVIGATION.AUTH.LOGIN.path} className="underline">
                直接登录
              </Link>
            </div>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
