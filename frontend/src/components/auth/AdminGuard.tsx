import { Navigate, useLocation } from 'react-router-dom';

import { useAuthStore } from '@/store/authStore';

interface AdminGuardProps {
  children: React.ReactNode;
}

export default function AdminGuard({ children }: AdminGuardProps) {
  const { user, isAuthenticated } = useAuthStore();
  const location = useLocation();

  if (!isAuthenticated) {
    // Check if we are already at login page to avoid loops, though Guard is usually used on protected routes
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (user?.role !== 'admin') {
    return <Navigate to="/404" replace />;
  }

  return <>{children}</>;
}
