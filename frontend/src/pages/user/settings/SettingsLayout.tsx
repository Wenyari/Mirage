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
    <div className="flex gap-6 p-6">
      <div className="w-64">
        <div className="mb-6">
          <h4 className="text-lg font-semibold">设置</h4>
        </div>
        <nav className="flex flex-col space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  'px-4 py-2 rounded transition-colors',
                  isActive ? 'bg-muted/20 font-medium' : 'hover:bg-muted/50'
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </div>

      <main className="flex-1">
        <Card className="p-0">
          <div className="p-6">
            <Outlet />
          </div>
        </Card>
      </main>
    </div>
  );
}


