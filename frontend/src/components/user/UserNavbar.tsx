import * as React from 'react';
import { Link, useLocation } from 'react-router-dom';

import { Button } from '@/components/ui/button';
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

export function UserNavbar() {
  const location = useLocation();

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
