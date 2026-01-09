import { useQuery } from '@tanstack/react-query';
import { useEffect } from 'react';

import { authService } from '@/services/auth';
import { useAuthStore } from '@/store/authStore';

export const CURRENT_USER_QUERY_KEY = ['currentUser'];

export function useCurrentUser() {
  const { isAuthenticated, setUser } = useAuthStore();

  const query = useQuery({
    queryKey: CURRENT_USER_QUERY_KEY,
    queryFn: () => authService.me(),
    enabled: isAuthenticated,
    // 既然需要实时性，staleTime 可以设短一点，或者依赖 invalidation
    staleTime: 1000 * 60 * 5, // 5分钟内认为数据是新鲜的，除非手动 invalidate
  });

  // 当 React Query 获取到最新数据时，同步更新到 zustand store
  // 这样可以保证应用中其他直接使用 useAuthStore 的地方也能得到更新
  useEffect(() => {
    if (query.data) {
      setUser(query.data);
    }
  }, [query.data, setUser]);

  return query;
}
