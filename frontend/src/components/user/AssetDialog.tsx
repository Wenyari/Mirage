/**
 * AI媒体资产创建/编辑对话框
 */
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

import { Button } from '@/components/ui/button';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import {
    Form,
    FormControl,
    FormDescription,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import type { AiMediaAsset } from '@/types/aiMediaAsset';

const assetFormSchema = z.object({
    title: z.string().min(1, '标题不能为空').max(255, '标题过长'),
    media_type: z.enum(['image', 'video']).default('image'),
    prompt_en: z.string().optional(),
    prompt_zh: z.string().optional(),
    width: z.coerce.number().int().min(0).optional(),
    height: z.coerce.number().int().min(0).optional(),
    r2_key: z.string().optional(),
    r2_url: z.string().url('请输入有效的URL').optional().or(z.literal('')),
    cover_r2_key: z.string().optional(),
    cover_r2_url: z.string().url('请输入有效的URL').optional().or(z.literal('')),
});

type AssetFormValues = z.infer<typeof assetFormSchema>;

interface AssetDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    asset?: AiMediaAsset;
    onSubmit: (data: AssetFormValues) => void;
    isLoading?: boolean;
}

export function AssetDialog({ open, onOpenChange, asset, onSubmit, isLoading }: AssetDialogProps) {
    const form = useForm<AssetFormValues>({
        resolver: zodResolver(assetFormSchema),
        defaultValues: asset
            ? {
                title: asset.title,
                media_type: asset.media_type,
                prompt_en: asset.prompt_en || '',
                prompt_zh: asset.prompt_zh || '',
                width: asset.width,
                height: asset.height,
                r2_key: asset.r2_key || '',
                r2_url: asset.r2_url || '',
                cover_r2_key: asset.cover_r2_key || '',
                cover_r2_url: asset.cover_r2_url || '',
            }
            : {
                title: '',
                media_type: 'image',
                prompt_en: '',
                prompt_zh: '',
                width: 0,
                height: 0,
                r2_key: '',
                r2_url: '',
                cover_r2_key: '',
                cover_r2_url: '',
            },
    });

    const handleSubmit = (data: AssetFormValues) => {
        onSubmit(data);
        form.reset();
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-[600px]">
                <DialogHeader>
                    <DialogTitle>{asset ? '编辑资产' : '创建资产'}</DialogTitle>
                    <DialogDescription>
                        {asset ? '修改AI媒体资产的信息' : '添加新的AI媒体资产到库中'}
                    </DialogDescription>
                </DialogHeader>

                <Form {...form}>
                    <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
                        {/* 标题 */}
                        <FormField
                            control={form.control}
                            name="title"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>标题 *</FormLabel>
                                    <FormControl>
                                        <Input placeholder="输入资产标题" {...field} />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        {/* 媒体类型 */}
                        <FormField
                            control={form.control}
                            name="media_type"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>媒体类型</FormLabel>
                                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                                        <FormControl>
                                            <SelectTrigger>
                                                <SelectValue placeholder="选择媒体类型" />
                                            </SelectTrigger>
                                        </FormControl>
                                        <SelectContent>
                                            <SelectItem value="image">图片</SelectItem>
                                            <SelectItem value="video">视频</SelectItem>
                                        </SelectContent>
                                    </Select>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        {/* 中文提示词 */}
                        <FormField
                            control={form.control}
                            name="prompt_zh"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>中文提示词</FormLabel>
                                    <FormControl>
                                        <Textarea
                                            placeholder="输入中文提示词..."
                                            className="min-h-[100px] resize-none"
                                            {...field}
                                        />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        {/* 英文提示词 */}
                        <FormField
                            control={form.control}
                            name="prompt_en"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>英文提示词</FormLabel>
                                    <FormControl>
                                        <Textarea
                                            placeholder="Enter English prompt..."
                                            className="min-h-[100px] resize-none"
                                            {...field}
                                        />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        {/* 尺寸 */}
                        <div className="grid grid-cols-2 gap-4">
                            <FormField
                                control={form.control}
                                name="width"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>宽度</FormLabel>
                                        <FormControl>
                                            <Input type="number" placeholder="1024" {...field} />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            <FormField
                                control={form.control}
                                name="height"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>高度</FormLabel>
                                        <FormControl>
                                            <Input type="number" placeholder="768" {...field} />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                        </div>

                        {/* R2文件URL */}
                        <FormField
                            control={form.control}
                            name="r2_url"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>资源URL</FormLabel>
                                    <FormControl>
                                        <Input placeholder="https://..." {...field} />
                                    </FormControl>
                                    <FormDescription>R2存储的资源访问链接</FormDescription>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        {/* 封面URL (仅视频) */}
                        {form.watch('media_type') === 'video' && (
                            <FormField
                                control={form.control}
                                name="cover_r2_url"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>封面URL</FormLabel>
                                        <FormControl>
                                            <Input placeholder="https://..." {...field} />
                                        </FormControl>
                                        <FormDescription>视频封面图片链接</FormDescription>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                        )}

                        <DialogFooter>
                            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                                取消
                            </Button>
                            <Button type="submit" disabled={isLoading}>
                                {isLoading ? '保存中...' : asset ? '保存修改' : '创建'}
                            </Button>
                        </DialogFooter>
                    </form>
                </Form>
            </DialogContent>
        </Dialog>
    );
}
