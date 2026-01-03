import { Link } from 'react-router-dom';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { USER_NAVIGATION } from '@/config/user-navigation';

export default function UserRegister() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/40 px-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle className="text-2xl">{USER_NAVIGATION.AUTH.REGISTER.label}</CardTitle>
          <CardDescription>
            创建一个新账号以开始使用 Mirage
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4">
          <div className="grid gap-2">
            <Label htmlFor="username">用户名</Label>
            <Input id="username" type="text" placeholder="您的昵称" required />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="email">邮箱</Label>
            <Input id="email" type="email" placeholder="m@example.com" required />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="password">密码</Label>
            <Input id="password" type="password" required />
          </div>
        </CardContent>
        <CardFooter className="flex flex-col gap-2">
          <Button className="w-full">注册</Button>
          <div className="text-center text-sm text-muted-foreground">
            已有账号？{' '}
            <Link to={USER_NAVIGATION.AUTH.LOGIN.path} className="underline">
              直接登录
            </Link>
          </div>
        </CardFooter>
      </Card>
    </div>
  );
}
