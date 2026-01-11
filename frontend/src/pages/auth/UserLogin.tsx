import { Turnstile, type TurnstileInstance } from '@marsidev/react-turnstile';
import { Lock,LogIn, Mail } from 'lucide-react';
import { useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { USER_NAVIGATION } from '@/config/user-navigation';
import { authService } from '@/services/auth';
import { useAuthStore } from '@/store/authStore';

export default function UserLogin() {
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const turnstileRef = useRef<TurnstileInstance>(null);
  const [turnstileToken, setTurnstileToken] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      toast.error('请输入邮箱和密码');
      return;
    }

    if (!turnstileToken) {
      toast.error('请完成人机验证');
      return;
    }

    try {
      setIsLoading(true);
      const response = await authService.login({ email, password, cf_token: turnstileToken });
      
      // 更新全局 Auth Store
      login((response as any).token, (response as any).user);
      
      toast.success('登录成功');
      navigate(USER_NAVIGATION.HOME.path);
    } catch (error: any) {
      toast.error(error.data.msg || '登录失败，请检查邮箱或密码');
      turnstileRef.current?.reset();
      setTurnstileToken('');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/40 px-4 py-8">
      <Card className="w-full max-w-md shadow-lg">
        <CardHeader className="space-y-1 text-center">
          <div className="mb-2 flex justify-center">
            <div className="rounded-full bg-primary/10 p-3">
              <LogIn className="size-6 text-primary" />
            </div>
          </div>
          <CardTitle className="text-2xl font-bold tracking-tight">{USER_NAVIGATION.AUTH.LOGIN.label}</CardTitle>
          <CardDescription>
            请输入您的账号和密码登录 Mirage
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
              <Turnstile
                ref={turnstileRef}
                siteKey="0x4AAAAAACLPiWv7g_o7HXD3"
                options={{
                  theme: 'light',
                  size: 'flexible',
                }}
                onSuccess={(token) => setTurnstileToken(token)}
                onExpire={() => setTurnstileToken('')}
                onError={() => {
                  setTurnstileToken('');
                  turnstileRef.current?.reset();
                }}
              />
            </div>
          </CardContent>
          <CardFooter className="flex flex-col gap-4 pt-2">
            <Button className="w-full text-base font-semibold shadow-sm" type="submit" disabled={isLoading || !turnstileToken} size="lg">
              {isLoading ? '登录中...' : '登录'}
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
