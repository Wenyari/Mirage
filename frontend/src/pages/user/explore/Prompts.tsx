/**
 * AI媒体资产展示页面 (Prompts)
 * 所有用户可浏览,管理员可增删改
 * 使用无限滚动懒加载
 */
import { Loader2, Plus, Search } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import Masonry from 'react-masonry-css';
import { toast } from 'sonner';

import { AssetCard } from '@/components/user/AssetCard';
import { AssetDialog } from '@/components/user/AssetDialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import {
  useCreateAsset,
  useDeleteAsset,
  useInfiniteAssets,
  useUpdateAsset,
} from '@/hooks/useAiMediaAssets';
import { useAuthStore } from '@/store/authStore';
import type { AiMediaAsset, CreateAssetRequest, UpdateAssetRequest } from '@/types/aiMediaAsset';

export default function Prompts() {
  const { user, isAuthenticated } = useAuthStore();
  const isAdmin = isAuthenticated && user?.role === 'admin';

  // 筛选和搜索状态
  const [mediaType, setMediaType] = useState<'all' | 'image' | 'video'>('image'); // 默认显示图片
  const [keyword, setKeyword] = useState('');
  const [searchInput, setSearchInput] = useState('');

  // 对话框状态
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingAsset, setEditingAsset] = useState<AiMediaAsset | undefined>();

  // 删除确认对话框
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deletingAssetId, setDeletingAssetId] = useState<number | null>(null);

  // 无限滚动加载
  const loadMoreRef = useRef<HTMLDivElement>(null);

  // 数据查询 - 使用无限滚动
  const {
    data,
    isLoading,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteAssets({
    page_size: 20,
    media_type: mediaType === 'all' ? undefined : mediaType,
    keyword: keyword || undefined,
  });

  // 数据操作
  const createMutation = useCreateAsset();
  const updateMutation = useUpdateAsset();
  const deleteMutation = useDeleteAsset();

  // 无限滚动检测
  useEffect(() => {
    if (!loadMoreRef.current) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasNextPage && !isFetchingNextPage) {
          fetchNextPage();
        }
      },
      { threshold: 0.1 }
    );

    observer.observe(loadMoreRef.current);

    return () => {
      observer.disconnect();
    };
  }, [fetchNextPage, hasNextPage, isFetchingNextPage]);

  // 加载时禁用滚动,防止布局闪烁
  useEffect(() => {
    if (isFetchingNextPage) {
      // 禁用滚动
      document.body.style.overflow = 'hidden';
    } else {
      // 恢复滚动
      document.body.style.overflow = '';
    }

    // 清理函数:组件卸载时恢复滚动
    return () => {
      document.body.style.overflow = '';
    };
  }, [isFetchingNextPage]);

  // 处理搜索
  const handleSearch = () => {
    setKeyword(searchInput);
  };

  // 处理创建
  const handleCreate = () => {
    setEditingAsset(undefined);
    setDialogOpen(true);
  };

  // 处理编辑
  const handleEdit = (asset: AiMediaAsset) => {
    setEditingAsset(asset);
    setDialogOpen(true);
  };

  // 处理删除
  const handleDeleteClick = (id: number) => {
    setDeletingAssetId(id);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = async () => {
    if (!deletingAssetId) return;

    try {
      await deleteMutation.mutateAsync(deletingAssetId);
      toast.success('删除成功');
      setDeleteDialogOpen(false);
      setDeletingAssetId(null);
    } catch (error: any) {
      toast.error(error.response?.data?.message || '删除失败');
    }
  };

  // 处理表单提交
  const handleSubmit = async (formData: CreateAssetRequest | UpdateAssetRequest) => {
    try {
      if (editingAsset) {
        // 更新
        await updateMutation.mutateAsync({
          id: editingAsset.id,
          data: formData as UpdateAssetRequest,
        });
        toast.success('更新成功');
      } else {
        // 创建
        await createMutation.mutateAsync(formData as CreateAssetRequest);
        toast.success('创建成功');
      }
      setDialogOpen(false);
      setEditingAsset(undefined);
    } catch (error: any) {
      toast.error(error.response?.data?.message || '操作失败');
    }
  };

  // 处理媒体类型筛选
  const handleMediaTypeChange = (value: string) => {
    setMediaType(value as 'all' | 'image' | 'video');
  };

  // 合并所有页的数据
  const assets = data?.pages.flatMap((page) => page.data.items) || [];
  const total = data?.pages[0]?.data?.total || 0;

  return (
    <div className="container mx-auto space-y-6 p-6">
      {/* 页面头部 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">AI提示词库</h1>
          <p className="mt-1 text-muted-foreground">
            探索和学习优质的AI生成提示词 {total > 0 && `· 共 ${total} 条`}
          </p>
        </div>
        {isAdmin && (
          <Button onClick={handleCreate}>
            <Plus className="mr-2 h-4 w-4" />
            创建提示词
          </Button>
        )}
      </div>

      {/* 筛选和搜索栏 */}
      <div className="flex flex-col gap-4 sm:flex-row">
        {/* 媒体类型筛选 */}
        <Select value={mediaType} onValueChange={handleMediaTypeChange}>
          <SelectTrigger className="w-full sm:w-[180px]">
            <SelectValue placeholder="媒体类型" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部类型</SelectItem>
            <SelectItem value="image">图片</SelectItem>
            <SelectItem value="video">视频</SelectItem>
          </SelectContent>
        </Select>

        {/* 搜索框 */}
        <div className="flex flex-1 gap-2">
          <Input
            placeholder="搜索标题..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            className="flex-1"
          />
          <Button onClick={handleSearch} variant="outline">
            <Search className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* 内容区域 */}
      {error ? (
        <div className="rounded-lg border border-destructive bg-destructive/10 p-8 text-center">
          <p className="text-destructive">加载失败,请稍后重试</p>
        </div>
      ) : isLoading ? (
        // 加载骨架屏
        <Masonry
          breakpointCols={{
            default: 4,
            1280: 4,
            1024: 3,
            640: 2,
            0: 1
          }}
          className="flex -ml-6 w-auto"
          columnClassName="pl-6 bg-clip-padding"
        >
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="mb-6 space-y-3">
              <Skeleton className="aspect-[4/3] w-full rounded-lg" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-2/3" />
            </div>
          ))}
        </Masonry>
      ) : assets.length === 0 ? (
        // 空状态
        <div className="flex min-h-[400px] flex-col items-center justify-center rounded-lg border border-dashed p-8">
          <p className="text-lg text-muted-foreground">暂无数据</p>
          {keyword && (
            <Button
              variant="link"
              onClick={() => {
                setKeyword('');
                setSearchInput('');
              }}
            >
              清除搜索
            </Button>
          )}
        </div>
      ) : (
        <>
          {/* 资产网格 - 使用 Masonry 实现瀑布流效果 */}
          <Masonry
            breakpointCols={{
              default: 4,
              1280: 4, // xl
              1024: 3, // lg
              640: 2,  // sm
              0: 1     // mobile
            }}
            className="flex -ml-6 w-auto"
            columnClassName="pl-6 bg-clip-padding"
          >
            {assets.map((asset) => (
              <div key={asset.id} className="mb-6">
                <AssetCard
                  asset={asset}
                  isAdmin={isAdmin}
                  onEdit={handleEdit}
                  onDelete={handleDeleteClick}
                />
              </div>
            ))}
          </Masonry>

          {/* 加载更多指示器 */}
          <div ref={loadMoreRef} className="flex justify-center py-8">
            {isFetchingNextPage ? (
              <div className="flex items-center gap-2 text-muted-foreground">
                <Loader2 className="h-5 w-5 animate-spin" />
                <span>加载中...</span>
              </div>
            ) : hasNextPage ? (
              <div className="text-muted-foreground">滚动加载更多</div>
            ) : assets.length > 0 ? (
              <div className="text-muted-foreground">— 到底了 —</div>
            ) : null}
          </div>
        </>
      )}

      {/* 创建/编辑对话框 */}
      <AssetDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        asset={editingAsset}
        onSubmit={handleSubmit}
        isLoading={createMutation.isPending || updateMutation.isPending}
      />

      {/* 删除确认对话框 */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认删除</AlertDialogTitle>
            <AlertDialogDescription>
              此操作将永久删除该资产及其关联的R2文件,无法恢复。确定要继续吗?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deleteMutation.isPending ? '删除中...' : '确认删除'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
