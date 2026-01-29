/**
 * AI媒体资产React Query Hooks
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
    batchDeleteAssets,
    createAsset,
    deleteAsset,
    getAssetById,
    getAssets,
    updateAsset,
} from '@/services/aiMediaAssets';
import type {
    BatchDeleteRequest,
    CreateAssetRequest,
    GetAssetsParams,
    UpdateAssetRequest,
} from '@/types/aiMediaAsset';

/**
 * 获取资产列表
 */
export function useAssets(params?: GetAssetsParams) {
    return useQuery({
        queryKey: ['ai-media-assets', params],
        queryFn: () => getAssets(params),
    });
}

/**
 * 获取单个资产详情
 */
export function useAsset(id: number) {
    return useQuery({
        queryKey: ['ai-media-assets', id],
        queryFn: () => getAssetById(id),
        enabled: !!id,
    });
}

/**
 * 创建资产
 */
export function useCreateAsset() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: CreateAssetRequest) => createAsset(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['ai-media-assets'] });
        },
    });
}

/**
 * 更新资产
 */
export function useUpdateAsset() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ id, data }: { id: number; data: UpdateAssetRequest }) => updateAsset(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['ai-media-assets'] });
        },
    });
}

/**
 * 删除资产
 */
export function useDeleteAsset() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (id: number) => deleteAsset(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['ai-media-assets'] });
        },
    });
}

/**
 * 批量删除资产
 */
export function useBatchDeleteAssets() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: BatchDeleteRequest) => batchDeleteAssets(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['ai-media-assets'] });
        },
    });
}
