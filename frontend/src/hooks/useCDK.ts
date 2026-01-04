import { keepPreviousData,useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type {
  CDKGenerateRequest,
  CDKListParams,
  CDKVoidRequest,
} from '@/types/cdk';
import { generateCDK, getBatchList,getCDKList, voidCDK } from '@/services/admin/cdk';

/**
 * 获取 CDK 列表
 */
export function useCDKList(params: CDKListParams) {
  return useQuery({
    queryKey: ['admin', 'cdk', 'list', params],
    queryFn: () => getCDKList(params),
    placeholderData: keepPreviousData,
  });
}

/**
 * 生成 CDK
 */
export function useGenerateCDK() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CDKGenerateRequest) => generateCDK(data),
    onSuccess: () => {
      // 刷新 CDK 列表
      queryClient.invalidateQueries({ queryKey: ['admin', 'cdk', 'list'] });
    },
  });
}

/**
 * 作废 CDK
 */
export function useVoidCDK() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CDKVoidRequest) => voidCDK(data),
    onSuccess: () => {
      // 刷新 CDK 列表
      queryClient.invalidateQueries({ queryKey: ['admin', 'cdk', 'list'] });
    },
  });
}

/**
 * 获取批次列表
 */
export function useBatchList() {
  return useQuery({
    queryKey: ['admin', 'cdk', 'batches'],
    queryFn: getBatchList,
  });
}
