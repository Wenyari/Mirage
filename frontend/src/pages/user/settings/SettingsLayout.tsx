import { Outlet, NavLink } from 'react-router-dom';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';

export default function SettingsLayout() {
  const navItems = [
    { to: '/setting/account', label: '账号设置' },
    { to: '/setting/apikey', label: 'API 秘钥' },
    { to: '/setting/credits', label: '充值与兑换' },
    { to: '/setting/records', label: '使用记录' },
    { to: '/setting/tiers', label: '账号层级' },
    { to: '/setting/help', label: '支持与帮助' },
  ];

  return (
    <div className="flex flex-col md:flex-row gap-6 p-4 md:p-6 min-h-[calc(100vh-3.5rem)]">
      <div className="w-full md:w-64 shrink-0">
        <div className="mb-4 md:mb-6">
          <h4 className="text-lg font-semibold">设置</h4>
        </div>
        <nav className="flex flex-row md:flex-col gap-2 md:space-y-1 overflow-x-auto pb-2 md:pb-0 no-scrollbar">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  'whitespace-nowrap px-4 py-2 rounded transition-colors text-sm md:text-base',
                  isActive ? 'bg-muted/20 font-medium text-primary' : 'hover:bg-muted/50 text-muted-foreground'
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </div>

      <main className="flex-1 min-w-0">
        <Card className="p-0 overflow-hidden">
          <div className="p-4 md:p-6">
            <Outlet />
          </div>
        </Card>
      </main>
    </div>
  );
}


