import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Bell, ChevronDown, Coins, CreditCard, Crown, LogOut, QrCode, Settings, User as UserIcon, Wallet, Wifi,Zap } from 'lucide-react';
import * as React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

import Logo from '@/assets/logo.svg';
import qqJpg from '@/assets/qq.jpg';
import wechatJpg from '@/assets/wechat.jpg';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from '@/components/ui/hover-card';
import { AnnouncementNotifier } from '@/components/user/AnnouncementNotifier';
import { USER_NAVIGATION } from '@/config/user-navigation';
import { useCurrentUser } from '@/hooks/useCurrentUser';
import { cn } from '@/lib/utils';
import { getAnnouncements } from '@/services/announcement';
import { authService, UserStats } from '@/services/auth';
import { useAuthStore } from '@/store/authStore';
import type { Announcement } from '@/types/announcement';
import { LEVEL_COLORS, USER_LEVEL_LABELS } from '@/types/user';

export function UserNavbar() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user, isAuthenticated, logout } = useAuthStore();
  const { data: currentUser } = useCurrentUser();

  const displayUser = currentUser || user;

  const [exploreOpen, setExploreOpen] = React.useState(false);
  const [playgroundOpen, setPlaygroundOpen] = React.useState(false);
  const [moreOpen, setMoreOpen] = React.useState(false);
  const [qrDialogOpen, setQrDialogOpen] = React.useState(false);
  const [announcements, setAnnouncements] = React.useState<Announcement[]>([]);

  // 获取公告列表
  React.useEffect(() => {
    const fetchAnnouncements = async () => {
      try {
        const response = await getAnnouncements(5); // 获取最近5条公告
        if (response.code === 0) {
          setAnnouncements(response.data);
        }
      } catch {
        // 静默失败,不影响导航栏显示
      }
    };

    fetchAnnouncements();
  }, []);

  const handleLogout = async () => {
    try {
      await authService.logout();
      logout();
      // 清除所有 React Query 缓存，确保切换用户后不会显示旧数据
      queryClient.clear();
      toast.success('已安全退出');
      navigate(USER_NAVIGATION.AUTH.LOGIN.path);
    } catch {
      // 即使后端报错,前端也要执行登出
      logout();
      // 清除所有 React Query 缓存
      queryClient.clear();
      navigate(USER_NAVIGATION.AUTH.LOGIN.path);
    }
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="mx-auto flex h-14 max-w-none items-center px-4 sm:px-6 lg:px-8">
        <div className="mr-4 hidden md:flex">
          <Link to="/" className="mr-6 flex items-center space-x-2">
            <img src={Logo} alt="GoGen Logo" className="size-8" />
            <span className="hidden text-xl font-bold sm:inline-block">GoGen</span>
          </Link>
          <div className="flex items-center space-x-1">
            {/* Model Square */}
            <Link
              to={USER_NAVIGATION.MODEL_SQUARE.path}
              className="inline-flex h-9 items-center justify-center rounded-md bg-background px-4 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground focus:outline-none disabled:pointer-events-none disabled:opacity-50"
            >
              {USER_NAVIGATION.MODEL_SQUARE.label}
            </Link>

            {/* Explore */}
            <HoverCard open={exploreOpen} onOpenChange={setExploreOpen} openDelay={20} closeDelay={20}>
              <HoverCardTrigger asChild>
                <Button
                  variant="ghost"
                  className="inline-flex h-9 items-center justify-center rounded-md bg-background px-4 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground focus:outline-none disabled:pointer-events-none disabled:opacity-50 data-[state=open]:bg-accent/50 data-[state=open]:text-accent-foreground data-[state=open]:hover:bg-accent data-[state=open]:focus:bg-accent"
                >
                  {USER_NAVIGATION.EXPLORE.label}
                  <ChevronDown className={cn("ml-1 h-3 w-3 transition-transform duration-200", exploreOpen && "rotate-180")} />
                </Button>
              </HoverCardTrigger>
              <HoverCardContent
                align="start"
                className="w-48 p-0"
                sideOffset={4}
              >
                <div className="py-1">
                  <Link
                    to={USER_NAVIGATION.EXPLORE.children.PROMPTS.path}
                    className="block px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground"
                  >
                    {USER_NAVIGATION.EXPLORE.children.PROMPTS.label}
                  </Link>
                  <Link
                    to={USER_NAVIGATION.EXPLORE.children.AGENTS.path}
                    className="block px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground"
                  >
                    {USER_NAVIGATION.EXPLORE.children.AGENTS.label}
                  </Link>
                  <Link
                    to={USER_NAVIGATION.EXPLORE.children.WORKFLOWS.path}
                    className="block px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground"
                  >
                    {USER_NAVIGATION.EXPLORE.children.WORKFLOWS.label}
                  </Link>
                </div>
              </HoverCardContent>
            </HoverCard>

            {/* Playground */}
            <HoverCard open={playgroundOpen} onOpenChange={setPlaygroundOpen} openDelay={20} closeDelay={20}>
              <HoverCardTrigger asChild>
                <Button
                  variant="ghost"
                  className="inline-flex h-9 items-center justify-center rounded-md bg-background px-4 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground focus:outline-none disabled:pointer-events-none disabled:opacity-50 data-[state=open]:bg-accent/50 data-[state=open]:text-accent-foreground data-[state=open]:hover:bg-accent data-[state=open]:focus:bg-accent"
                >
                  {USER_NAVIGATION.PLAYGROUND.label}
                  <ChevronDown className={cn("ml-1 h-3 w-3 transition-transform duration-200", playgroundOpen && "rotate-180")} />
                </Button>
              </HoverCardTrigger>
              <HoverCardContent
                align="start"
                className="w-48 p-0"
                sideOffset={4}
              >
                <div className="py-1">
                  {/* <Link
                    to={USER_NAVIGATION.PLAYGROUND.path}
                    className="block px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground"
                  >
                    {USER_NAVIGATION.PLAYGROUND.label}
                  </Link>
                  <Link
                    to={USER_NAVIGATION.PLAYGROUND.children.CHAT.path}
                    className="block px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground"
                  >
                    {USER_NAVIGATION.PLAYGROUND.children.CHAT.label}
                  </Link> */}
                  <Link
                    to={USER_NAVIGATION.PLAYGROUND.children.VIDEO_GENERATION.path}
                    className="block px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground"
                  >
                    {USER_NAVIGATION.PLAYGROUND.children.VIDEO_GENERATION.label}
                  </Link>
                  <Link
                    to={USER_NAVIGATION.PLAYGROUND.children.IMAGE_GENERATION.path}
                    className="block px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground"
                  >
                    {USER_NAVIGATION.PLAYGROUND.children.IMAGE_GENERATION.label}
                  </Link>
                </div>
              </HoverCardContent>
            </HoverCard>

            {/* More */}
            <HoverCard open={moreOpen} onOpenChange={setMoreOpen} openDelay={20} closeDelay={20}>
              <HoverCardTrigger asChild>
                <Button
                  variant="ghost"
                  className="inline-flex h-9 items-center justify-center rounded-md bg-background px-4 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground focus:outline-none disabled:pointer-events-none disabled:opacity-50 data-[state=open]:bg-accent/50 data-[state=open]:text-accent-foreground data-[state=open]:hover:bg-accent data-[state=open]:focus:bg-accent"
                >
                  {USER_NAVIGATION.MORE.label}
                  <ChevronDown className={cn("ml-1 h-3 w-3 transition-transform duration-200", moreOpen && "rotate-180")} />
                </Button>
              </HoverCardTrigger>
              <HoverCardContent
                align="start"
                className="w-48 p-0"
                sideOffset={4}
              >
                <div className="py-1">
                  <Link
                    to={USER_NAVIGATION.MORE.children.UPDATES.path}
                    className="block px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground"
                  >
                    {USER_NAVIGATION.MORE.children.UPDATES.label}
                  </Link>
                  <Link
                    to={USER_NAVIGATION.MORE.children.EVENTS.path}
                    className="block px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground"
                  >
                    {USER_NAVIGATION.MORE.children.EVENTS.label}
                  </Link>
                  <Link
                    to={USER_NAVIGATION.MORE.children.COMMUNITY.path}
                    className="block px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground"
                  >
                    {USER_NAVIGATION.MORE.children.COMMUNITY.label}
                  </Link>
                </div>
              </HoverCardContent>
            </HoverCard>

            {/* QR Code Dialog Trigger */}
            <Button
              variant="ghost"
              size="icon"
              className="size-9"
              onClick={() => setQrDialogOpen(true)}
            >
              <QrCode className="size-4" />
            </Button>
          </div>
        </div>
        <div className="flex flex-1 items-center justify-between space-x-2 md:justify-end">
          <div className="w-full flex-1 md:w-auto md:flex-none">
            {/* 搜索框占位 */}
          </div>
          <nav className="flex items-center space-x-2">
            {/* 在线统计 */}
            <UserStatsIndicator />

            {/* 公告图标 */}
            <Link to={USER_NAVIGATION.MORE.children.UPDATES.path}>
              <Button variant="ghost" size="icon" className="size-8">
                <Bell className="size-4" />
              </Button>
            </Link>

            {isAuthenticated ? (
              <HoverCard>
                <HoverCardTrigger asChild>
                  <Button variant="ghost" className="relative size-8 rounded-full">
                    <Avatar className="size-8">
                      <AvatarImage src={displayUser?.avatar} alt={displayUser?.name || displayUser?.email} />
                      <AvatarFallback>{(displayUser?.name || displayUser?.email || 'U').charAt(0).toUpperCase()}</AvatarFallback>
                    </Avatar>
                  </Button>
                </HoverCardTrigger>
                <HoverCardContent className="w-80" align="end">
                  <div className="flex flex-col space-y-4">
                    {/* User Info Header */}
                    <div className="flex items-center gap-4">
                      <Avatar className="size-12">
                        <AvatarImage src={displayUser?.avatar} alt={displayUser?.name || displayUser?.email} />
                        <AvatarFallback>{(displayUser?.name || displayUser?.email || 'U').charAt(0).toUpperCase()}</AvatarFallback>
                      </Avatar>
                      <div className="space-y-1">
                        <h4 className="text-sm font-semibold">{displayUser?.name || '用户'}</h4>
                        <p className="text-xs text-muted-foreground">{displayUser?.email}</p>
                      </div>
                    </div>

                    {/* Stats Grid */}
                    <div className="grid grid-cols-2 gap-4 rounded-lg border bg-muted/50 p-3">
                      <div className="space-y-1">
                        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                          <Wallet className="size-3.5" />
                          积分余额
                        </div>
                        <p className="text-lg font-bold text-primary">
                          {(displayUser?.balance_detail?.total_balance ?? displayUser?.balance ?? 0).toFixed(2)}
                        </p>
                        {displayUser?.balance_detail && (
                          <div className="flex flex-col gap-0.5 text-[10px] text-muted-foreground">
                            <div className="flex items-center gap-1">
                              <Coins className="size-3 text-yellow-500" />
                              <span>{displayUser.balance_detail.recharge_balance.toFixed(0)}</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <Zap className="size-3 text-blue-500" />
                              <span>{displayUser.balance_detail.activity_balance.toFixed(0)}</span>
                            </div>
                          </div>
                        )}
                      </div>
                      <div className="space-y-1">
                        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                          <Crown className="size-3.5" />
                          会员等级
                        </div>
                        <div className="flex items-center pt-1">
                          <span className={cn(
                            "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
                            displayUser?.level ? LEVEL_COLORS[displayUser.level as keyof typeof LEVEL_COLORS] : "bg-gray-100 text-gray-800"
                          )}>
                            {displayUser?.level ? USER_LEVEL_LABELS[displayUser.level as keyof typeof USER_LEVEL_LABELS] : 'T1'}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="space-y-2">
                      {displayUser?.role === 'admin' && (
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
                        variant="outline"
                        className="w-full justify-start"
                        onClick={() => navigate('/setting/account')}
                      >
                        <Settings className="mr-2 size-4" />
                        账户设置
                      </Button>
                      <Button
                        variant="outline"
                        className="w-full justify-start"
                        onClick={() => navigate('/setting/credits')}
                      >
                        <CreditCard className="mr-2 size-4" />
                        充值与兑换
                      </Button>
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

      {/* 公告通知弹窗 */}
      <AnnouncementNotifier announcements={announcements} />

      {/* Connectivity/Stats Indicator */}
      <div className="fixed bottom-4 left-4 z-50 hidden md:block">
        {/* This is just a placeholder if we wanted floating, but user asked for "left of announcement icon" in navbar. */}
      </div>

      {/* QR Code Dialog */}
      <Dialog open={qrDialogOpen} onOpenChange={setQrDialogOpen}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>联系我们</DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-8 py-4">
            <div className="flex flex-col items-center justify-center">
              <div className="mb-2 rounded-lg border bg-white p-2">
                <img src={wechatJpg} alt="WeChat Support" className="h-auto w-full max-w-[250px] object-contain" />
              </div>
              <p className="font-medium">客服微信</p>
              <p className="text-sm text-muted-foreground">扫码添加客服微信</p>
            </div>
            <div className="flex flex-col items-center justify-center">
              <div className="mb-2 rounded-lg border bg-white p-2">
                <img src={qqJpg} alt="QQ Community" className="h-auto w-full max-w-[250px] object-contain" />
              </div>
              <p className="font-medium">官方社群</p>
              <p className="text-sm text-muted-foreground">扫码加入官方QQ社群</p>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </header>
  );
}

function UserStatsIndicator() {
  const [open, setOpen] = React.useState(false);
  const { data: stats } = useQuery({
    queryKey: ['public-stats'],
    queryFn: authService.getPublicStats,
    refetchInterval: 30 * 1000, // 5 minutes
    staleTime: 30 * 1000,
  });

  const getLevelColor = (level: string) => {
    switch (level) {
      case '1': return 'text-gray-500';
      case '2': return 'text-green-500';
      case '3': return 'text-blue-500';
      case '4': return 'text-purple-500';
      case '5': return 'text-orange-500';
      default: return 'text-foreground';
    }
  };

  const getLevelLabel = (level: string) => `T${level}`;

  return (
    <HoverCard open={open} onOpenChange={setOpen} openDelay={20} closeDelay={20}>
      <HoverCardTrigger asChild>
        <Button variant="ghost" size="icon" className="size-8">
          <Wifi className="size-4" />
        </Button>
      </HoverCardTrigger>
      <HoverCardContent className="w-64" align="end">
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">当前在线</span>
            <span className="text-xl font-bold text-primary">{(stats as unknown as UserStats)?.online_count || 0}</span>
          </div>
          <div className="space-y-1.5">
            <span className="text-xs text-muted-foreground">用户分布</span>
            <div className="grid grid-cols-5 gap-2 text-center text-xs">
              {['1', '2', '3', '4', '5'].map((level) => (
                <div key={level} className="flex flex-col items-center gap-1">
                  <span className={cn("font-bold", getLevelColor(level))}>
                    {getLevelLabel(level)}
                  </span>
                  <span>{(stats as unknown as UserStats)?.level_distribution?.[level] || 0}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </HoverCardContent>
    </HoverCard>
  );
}

