import { NavLink } from 'react-router-dom';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  Users,
  Ticket,
  Key,
  Settings,
  Microscope,
} from 'lucide-react';

const menuItems = [
  {
    path: '/wadminw/dashboard',
    label: '仪表盘',
    icon: LayoutDashboard,
  },
  {
    path: '/wadminw/users',
    label: '用户管理',
    icon: Users,
  },
  {
    path: '/wadminw/cdk',
    label: 'CDK管理',
    icon: Ticket,
  },
  {
    path: '/wadminw/keys',
    label: '密钥池',
    icon: Key,
  },
  {
    path: '/wadminw/models',
    label: '模型配置',
    icon: Settings,
  },
  {
    path: '/wadminw/playground',
    label: '测试沙箱',
    icon: Microscope,
  },
];

export function AdminSidebar() {
  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 border-r bg-background">
      <div className="flex h-full flex-col">
        {/* Logo */}
        <div className="flex h-16 items-center border-b px-6">
          <h1 className="text-xl font-bold">AIGC 管理后台</h1>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 p-4">
          {menuItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                )
              }
            >
              <item.icon className="h-5 w-5" />
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="border-t p-4">
          <p className="text-xs text-muted-foreground">
            © 2024 AIGC Platform
          </p>
        </div>
      </div>
    </aside>
  );
}
