import { Outlet } from 'react-router-dom';

import { UserNavbar } from '@/components/user/UserNavbar';

export default function UserLayout() {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <UserNavbar />
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  );
}
