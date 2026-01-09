import { LogOut, Moon, Sun } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
} from '@/components/ui/breadcrumb';
import { Button } from '@/components/ui/button';
import { logout } from '@/services/admin/auth';
import { useAuthStore } from '@/store/authStore';

const routeNames: Record<string, string> = {
  '/wadminw/dashboard': '仪表盘',
  '/wadminw/users': '用户管理',
  '/wadminw/cdk': 'CDK管理',
  '/wadminw/keys': '密钥池',
  '/wadminw/models': '模型配置',
  '/wadminw/activities': '营销活动',
  '/wadminw/playground': '测试沙箱',
};

export function AdminHeader() {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout: storeLogout } = useAuthStore();

  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  useEffect(() => {
    // 读取系统主题偏好
    const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const storedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null;
    const initialTheme = storedTheme || (isDark ? 'dark' : 'light');

    setTheme(initialTheme);
    document.documentElement.classList.toggle('dark', initialTheme === 'dark');
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    document.documentElement.classList.toggle('dark', newTheme === 'dark');
  };

  const handleLogout = async () => {
    try {
      await logout();
      storeLogout();
      toast.success('登出成功，您已安全退出系统');
      navigate('/wadminw/login');
    } catch (error) {
      // 即使后端报错，前端也要登出
      storeLogout();
      navigate('/wadminw/login');
    }
  };

  const currentPageName = routeNames[location.pathname] || '未知页面';

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b bg-background px-6">
      {/* Breadcrumb */}
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink href="/wadminw/dashboard">首页</BreadcrumbLink>
          </BreadcrumbItem>
          {location.pathname !== '/wadminw/dashboard' && (
            <>
              <BreadcrumbItem>
                <BreadcrumbPage>{currentPageName}</BreadcrumbPage>
              </BreadcrumbItem>
            </>
          )}
        </BreadcrumbList>
      </Breadcrumb>

      {/* Actions */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleTheme}
          aria-label="Toggle theme"
        >
          {theme === 'light' ? (
            <Moon className="size-5" />
          ) : (
            <Sun className="size-5" />
          )}
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={handleLogout}
          aria-label="Logout"
          className="text-muted-foreground hover:text-foreground"
        >
          <LogOut className="size-5" />
        </Button>
      </div>
    </header>
  );
}
