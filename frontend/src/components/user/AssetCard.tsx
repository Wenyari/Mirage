/**
 * AI媒体资产卡片组件
 */
import { Edit, Play, Trash2 } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';
import type { AiMediaAsset } from '@/types/aiMediaAsset';

interface AssetCardProps {
    asset: AiMediaAsset;
    isAdmin: boolean;
    onEdit?: (asset: AiMediaAsset) => void;
    onDelete?: (id: number) => void;
}

export function AssetCard({ asset, isAdmin, onEdit, onDelete }: AssetCardProps) {
    const promptText = asset.prompt_zh || asset.prompt_en || '暂无提示词';
    const imageUrls = asset.r2_url || [];

    return (
        <Card className="group flex h-full flex-col overflow-hidden transition-all hover:shadow-lg">
            {/* 预览图区域 - 多张图片垂直排列 */}
            {imageUrls.length > 0 && (
                <div className="relative">
                    {asset.media_type === 'image' ? (
                        <div className="flex flex-col gap-2 bg-muted p-2">
                            {imageUrls.map((url, index) => (
                                <img
                                    key={index}
                                    src={url}
                                    alt={`${asset.title} - 图片 ${index + 1}`}
                                    className="w-full rounded object-cover transition-transform group-hover:scale-[1.02]"
                                    loading="lazy"
                                />
                            ))}
                        </div>
                    ) : (
                        <div className="relative aspect-[4/3] overflow-hidden bg-muted">
                            {asset.cover_r2_url ? (
                                <img
                                    src={asset.cover_r2_url}
                                    alt={asset.title}
                                    className="h-full w-full object-cover"
                                    loading="lazy"
                                />
                            ) : (
                                <div className="flex h-full items-center justify-center bg-gradient-to-br from-purple-500/20 to-pink-500/20">
                                    <Play className="h-16 w-16 text-white/80" />
                                </div>
                            )}
                            <div className="absolute inset-0 flex items-center justify-center bg-black/20">
                                <Play className="h-12 w-12 text-white" />
                            </div>
                        </div>
                    )}

                    {/* 管理员操作按钮 */}
                    {isAdmin && (
                        <div className="absolute right-2 top-2 flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                            <Button
                                variant="secondary"
                                size="icon"
                                className="h-8 w-8 bg-black/50 text-white hover:bg-black/70"
                                onClick={() => onEdit?.(asset)}
                            >
                                <Edit className="h-4 w-4" />
                            </Button>
                            <Button
                                variant="destructive"
                                size="icon"
                                className="h-8 w-8"
                                onClick={() => onDelete?.(asset.id)}
                            >
                                <Trash2 className="h-4 w-4" />
                            </Button>
                        </div>
                    )}
                </div>
            )}

            {/* 卡片内容 */}
            <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-2">
                    <h3 className="line-clamp-2 text-base font-semibold leading-tight">{asset.title}</h3>
                </div>
            </CardHeader>

            <CardContent className="flex-1 space-y-3">
                {/* 提示词 - 不限制长度 */}
                <div>
                    <p className="whitespace-pre-wrap text-sm text-muted-foreground">
                        {promptText}
                    </p>
                </div>

                {/* 标签 */}
                <div className="flex flex-wrap gap-2">
                    <Badge variant="secondary" className="capitalize">
                        {asset.media_type}
                    </Badge>
                    {imageUrls.length > 1 && (
                        <Badge variant="outline">
                            {imageUrls.length} 张图片
                        </Badge>
                    )}
                    {asset.width > 0 && asset.height > 0 && (
                        <Badge variant="outline">
                            {asset.width} × {asset.height}
                        </Badge>
                    )}
                    {asset.aspect_ratio > 0 && (
                        <Badge variant="outline">{asset.aspect_ratio.toFixed(2)}</Badge>
                    )}
                </div>
            </CardContent>

            <CardFooter className="pt-0 text-xs text-muted-foreground">
                创建于 {new Date(asset.created_at).toLocaleDateString('zh-CN')}
            </CardFooter>
        </Card>
    );
}
