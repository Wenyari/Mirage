import { Outlet } from 'react-router-dom';

import { UserNavbar } from '@/components/user/UserNavbar';

export default function UserLayout() {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <UserNavbar />
      <main className="flex-1">
        <Outlet />
      </main>
      <footer className="border-t py-6 md:px-8 md:py-0">
        <div className="container flex flex-col items-center justify-between gap-4 md:h-24 md:flex-row">
          <p className="text-balance text-center text-sm leading-loose text-muted-foreground md:text-left">
            Built by Mirage Team. The source code is available on GitHub.
          </p>
        </div>
      </footer>
    </div>
  );
}
