import { Outlet } from 'react-router-dom';

import Logo from '@/assets/logo.svg';

export default function AuthLayout() {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="mx-auto flex h-14 max-w-none items-center px-4 sm:px-6 lg:px-8">
          <div className="mr-4 flex items-center">
            <a href="/" className="flex items-center space-x-2">
              <img src={Logo} alt="GoGen Logo" className="size-8" />
              <span className="hidden text-xl font-bold sm:inline-block">GoGen</span>
            </a>
          </div>
        </div>
      </header>
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  );
}

