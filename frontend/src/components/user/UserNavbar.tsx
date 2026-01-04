import { LogOut, User as UserIcon } from 'lucide-react';
import * as React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from '@/components/ui/hover-card';
import {
  NavigationMenu,
  NavigationMenuContent,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuTrigger,
  navigationMenuTriggerStyle,
} from '@/components/ui/navigation-menu';
import { USER_NAVIGATION } from '@/config/user-navigation';
import { cn } from '@/lib/utils';
import { authService } from '@/services/auth';
import { useAuthStore } from '@/store/authStore';
import { LEVEL_COLORS,USER_LEVEL_LABELS } from '@/types/user';

export function UserNavbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, isAuthenticated, logout } = useAuthStore();

  const handleLogout = async () => {
    try {
      await authService.logout();
      logout();
      toast.success('已安全退出');
      navigate(USER_NAVIGATION.AUTH.LOGIN.path);
    } catch (error) {
      // 即使后端报错，前端也要执行登出
      logout();
      navigate(USER_NAVIGATION.AUTH.LOGIN.path);
    }
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center">
        <div className="mr-4 hidden md:flex">
          <Link to="/" className="mr-6 flex items-center space-x-2">
            <span className="hidden font-bold sm:inline-block">Mirage</span>
          </Link>
          <NavigationMenu>
            <NavigationMenuList>
              {/* Model Square */}
              <NavigationMenuItem>
                <Link to={USER_NAVIGATION.MODEL_SQUARE.path}>
                  <NavigationMenuLink className={navigationMenuTriggerStyle()}>
                    {USER_NAVIGATION.MODEL_SQUARE.label}
                  </NavigationMenuLink>
                </Link>
              </NavigationMenuItem>

              {/* Explore */}
              <NavigationMenuItem>
                <NavigationMenuTrigger>{USER_NAVIGATION.EXPLORE.label}</NavigationMenuTrigger>
                <NavigationMenuContent>
                  <ul className="grid w-[400px] gap-3 p-4 md:w-[500px] md:grid-cols-2 lg:w-[600px]">
                    <ListItem
                      href={USER_NAVIGATION.EXPLORE.children.PROMPTS.path}
                      title={USER_NAVIGATION.EXPLORE.children.PROMPTS.label}
                    >
                      探索各种高效的提示词，激发无限灵感。
                    </ListItem>
                    <ListItem
                      href={USER_NAVIGATION.EXPLORE.children.AGENTS.path}
                      title={USER_NAVIGATION.EXPLORE.children.AGENTS.label}
                    >
                      发现并使用功能强大的智能体。
                    </ListItem>
                    <ListItem
                      href={USER_NAVIGATION.EXPLORE.children.WORKFLOWS.path}
                      title={USER_NAVIGATION.EXPLORE.children.WORKFLOWS.label}
                    >
                      构建和分享自动化工作流。
                    </ListItem>
                  </ul>
                </NavigationMenuContent>
              </NavigationMenuItem>

              {/* Playground */}
              <NavigationMenuItem>
                <NavigationMenuTrigger>{USER_NAVIGATION.PLAYGROUND.label}</NavigationMenuTrigger>
                <NavigationMenuContent>
                  <ul className="grid gap-3 p-6 md:w-[400px] lg:w-[500px] lg:grid-cols-[.75fr_1fr]">
                    <li className="row-span-3">
                      <NavigationMenuLink asChild>
                        <a
                          className="flex size-full select-none flex-col justify-end rounded-md bg-gradient-to-b from-muted/50 to-muted p-6 no-underline outline-none focus:shadow-md"
                          href={USER_NAVIGATION.PLAYGROUND.path}
                        >
                          <div className="mb-2 mt-4 text-lg font-medium">
                            {USER_NAVIGATION.PLAYGROUND.label}
                          </div>
                          <p className="text-sm leading-tight text-muted-foreground">
                            沉浸式体验 AI 的强大能力。
                          </p>
                        </a>
                      </NavigationMenuLink>
                    </li>
                    <ListItem
                      href={USER_NAVIGATION.PLAYGROUND.children.CHAT.path}
                      title={USER_NAVIGATION.PLAYGROUND.children.CHAT.label}
                    >
                      与智能模型进行实时对话。
                    </ListItem>
                    <ListItem
                      href={USER_NAVIGATION.PLAYGROUND.children.VIDEO_GENERATION.path}
                      title={USER_NAVIGATION.PLAYGROUND.children.VIDEO_GENERATION.label}
                    >
                      一键生成创意视频。
                    </ListItem>
                  </ul>
                </NavigationMenuContent>
              </NavigationMenuItem>

              {/* More */}
              <NavigationMenuItem>
                <NavigationMenuTrigger>{USER_NAVIGATION.MORE.label}</NavigationMenuTrigger>
                <NavigationMenuContent>
                  <ul className="grid w-[400px] gap-3 p-4 md:w-[500px] md:grid-cols-2 lg:w-[600px]">
                    <ListItem
                      href={USER_NAVIGATION.MORE.children.UPDATES.path}
                      title={USER_NAVIGATION.MORE.children.UPDATES.label}
                    >
                      查看平台的最新动态和更新日志。
                    </ListItem>
                    <ListItem
                      href={USER_NAVIGATION.MORE.children.EVENTS.path}
                      title={USER_NAVIGATION.MORE.children.EVENTS.label}
                    >
                      参与精彩活动，赢取奖励。
                    </ListItem>
                    <ListItem
                      href={USER_NAVIGATION.MORE.children.COMMUNITY.path}
                      title={USER_NAVIGATION.MORE.children.COMMUNITY.label}
                    >
                      加入社区，与开发者交流。
                    </ListItem>
                  </ul>
                </NavigationMenuContent>
              </NavigationMenuItem>
            </NavigationMenuList>
          </NavigationMenu>
        </div>
        <div className="flex flex-1 items-center justify-between space-x-2 md:justify-end">
          <div className="w-full flex-1 md:w-auto md:flex-none">
            {/* 搜索框占位 */}
          </div>
          <nav className="flex items-center space-x-2">
            {isAuthenticated ? (
              <HoverCard>
                <HoverCardTrigger asChild>
                  <Button variant="ghost" className="relative size-8 rounded-full">
                    <Avatar className="size-8">
                      <AvatarImage src={user?.avatar} alt={user?.name || user?.email} />
                      <AvatarFallback>{(user?.name || user?.email || 'U').charAt(0).toUpperCase()}</AvatarFallback>
                    </Avatar>
                  </Button>
                </HoverCardTrigger>
                <HoverCardContent className="w-80" align="end">
                  <div className="flex flex-col space-y-4">
                    {/* User Info Header */}
                    <div className="flex items-center gap-4">
                      <Avatar className="size-12">
                        <AvatarImage src={user?.avatar} alt={user?.name || user?.email} />
                        <AvatarFallback>{(user?.name || user?.email || 'U').charAt(0).toUpperCase()}</AvatarFallback>
                      </Avatar>
                      <div className="space-y-1">
                        <h4 className="text-sm font-semibold">{user?.name || '用户'}</h4>
                        <p className="text-xs text-muted-foreground">{user?.email}</p>
                      </div>
                    </div>
                    
                    {/* Stats Grid */}
                    <div className="grid grid-cols-2 gap-4 rounded-lg border bg-muted/50 p-3">
                      <div className="space-y-1">
                        <p className="text-xs text-muted-foreground">积分余额</p>
                        <p className="text-lg font-bold text-primary">{user?.balance?.toFixed(2) || '0.00'}</p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-xs text-muted-foreground">会员等级</p>
                        <div className="flex items-center">
                          <span className={cn(
                            "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
                            user?.level ? LEVEL_COLORS[user.level] : "bg-gray-100 text-gray-800"
                          )}>
                            {user?.level ? USER_LEVEL_LABELS[user.level] : 'T1'}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="space-y-2">
                      {user?.role === 'admin' && (
                        <Button 
                          variant="outline" 
                          className="w-full justify-start" 
                          onClick={() => navigate('/wadminw')}
                        >
                          <UserIcon className="mr-2 size-4" />
                          进入管理后台
                        </Button>
                      )}
                      <Button 
                        variant="ghost" 
                        className="w-full justify-start text-red-600 hover:bg-red-50 hover:text-red-600" 
                        onClick={handleLogout}
                      >
                        <LogOut className="mr-2 size-4" />
                        退出登录
                      </Button>
                    </div>
                  </div>
                </HoverCardContent>
              </HoverCard>
            ) : (
              <>
                <Link to={USER_NAVIGATION.AUTH.LOGIN.path}>
                  <Button variant="ghost" size="sm">
                    {USER_NAVIGATION.AUTH.LOGIN.label}
                  </Button>
                </Link>
                <Link to={USER_NAVIGATION.AUTH.REGISTER.path}>
                  <Button size="sm">
                    {USER_NAVIGATION.AUTH.REGISTER.label}
                  </Button>
                </Link>
              </>
            )}
          </nav>
        </div>
      </div>
    </header>
  );
}

const ListItem = React.forwardRef<
  React.ElementRef<'a'>,
  React.ComponentPropsWithoutRef<'a'>
>(({ className, title, children, ...props }, ref) => {
  return (
    <li>
      <NavigationMenuLink asChild>
        <a
          ref={ref}
          className={cn(
            'block select-none space-y-1 rounded-md p-3 leading-none no-underline outline-none transition-colors hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground',
            className
          )}
          {...props}
        >
          <div className="text-sm font-medium leading-none">{title}</div>
          <p className="line-clamp-2 text-sm leading-snug text-muted-foreground">
            {children}
          </p>
        </a>
      </NavigationMenuLink>
    </li>
  );
});
ListItem.displayName = 'ListItem';
