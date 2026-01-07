import { zodResolver } from '@hookform/resolvers/zod';
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';
import * as z from 'zod';

import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { FancyMultiSelect } from '@/components/ui/fancy-multi-select';
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
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { useUpdateModel } from '@/hooks/useKeys';
import type { Model } from '@/types/key';

interface EditModelDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  model?: Model;
}

// 预定义常用标签 (与 CreateModelDialog 保持一致)
const SUGGESTED_TAGS = [
  { value: 'video', label: '视频 (video)' },
  { value: 'image', label: '图片 (image)' },
  { value: 'text', label: '文本 (text)' },
  { value: 'audio', label: '音频 (audio)' },
  { value: 'generation', label: '生成 (generation)' },
  { value: 'edit', label: '编辑 (edit)' },
  { value: 'chat', label: '对话 (chat)' },
  { value: 'transcription', label: '转录 (transcription)' },
  { value: 'hd', label: '高清 (hd)' },
  { value: 'realtime', label: '实时 (realtime)' },
  { value: 'multimodal', label: '多模态 (multimodal)' },
];

// 表单 Schema
const formSchema = z.object({
  name: z.string().min(2, '模型名称至少2个字符').max(100, '模型名称最多100个字符'),
  enabled: z.boolean(),
  description: z.string().max(500, '描述最多500个字符').optional(),
  color: z.string().optional(),
  icon_url: z.string().url('请输入有效的URL').or(z.literal('')).optional(),
  max_concurrency_limit: z.coerce.number().min(1).max(100).optional(),
  tags: z.array(z.string()).optional(),
});

type FormValues = z.infer<typeof formSchema>;

export function EditModelDialog({ open, onOpenChange, model }: EditModelDialogProps) {
  const updateMutation = useUpdateModel();

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: '',
      enabled: true,
      description: '',
      color: 'bg-blue-500',
      icon_url: '',
      max_concurrency_limit: 20,
      tags: [],
    },
  });

  // 当模型数据变化时，更新表单
  useEffect(() => {
    if (model) {
      form.reset({
        name: model.name,
        enabled: Boolean(model.enabled),
        description: model.description || '',
        color: model.color || 'bg-blue-500',
        icon_url: model.icon_url || model.icon || '',
        max_concurrency_limit: model.max_concurrency_limit || 20,
        tags: model.tags || [],
      });
    }
  }, [model, form]);

  const onSubmit = async (values: FormValues) => {
    if (!model) return;

    try {
      // 清理空字符串为 undefined
      const data = {
        ...values,
        icon_url: values.icon_url || undefined,
        description: values.description || undefined,
      };

      const result = await updateMutation.mutateAsync({
        key: model.key,
        data,
      });

      if (result.code === 0) {
        toast.success('模型更新成功');
        onOpenChange(false);
      }
    } catch (error: any) {
      toast.error(error.message || '更新失败');
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] max-w-2xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>编辑模型</DialogTitle>
          <DialogDescription>
            修改模型配置信息（模型标识不可修改）
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            {/* 模型标识（只读） */}
            {model && (
              <div className="space-y-2">
                <label className="text-sm font-medium">模型标识</label>
                <Input value={model.key} disabled className="bg-muted font-mono" />
                <p className="text-xs text-muted-foreground">模型标识不可修改</p>
              </div>
            )}

            {/* 模型名称 */}
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>模型名称 *</FormLabel>
                  <FormControl>
                    <Input placeholder="例如: GPT-4, Claude 3 Opus" {...field} />
                  </FormControl>
                  <FormDescription>用于前端显示的名称</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* 描述 */}
            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>描述</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="模型功能描述（可选）"
                      className="resize-none"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Tags */}
            <FormField
              control={form.control}
              name="tags"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>标签</FormLabel>
                  <FormControl>
                    <FancyMultiSelect
                      selected={field.value || []}
                      onChange={field.onChange}
                      options={SUGGESTED_TAGS}
                      placeholder="选择或输入标签..."
                    />
                  </FormControl>
                  <FormDescription>用于模型分类和筛选</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* 颜色 */}
            <FormField
              control={form.control}
              name="color"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>UI 颜色</FormLabel>
                  <FormControl>
                    <Input placeholder="例如: bg-blue-500" {...field} />
                  </FormControl>
                  <FormDescription>Tailwind CSS 颜色类</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* 图标 URL */}
            <FormField
              control={form.control}
              name="icon_url"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>图标 URL</FormLabel>
                  <FormControl>
                    <Input
                      type="url"
                      placeholder="https://example.com/icon.png"
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>模型图标URL（可选）</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* 最大并发限制 */}
            <FormField
              control={form.control}
              name="max_concurrency_limit"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>建议最大并发</FormLabel>
                  <FormControl>
                    <Input type="number" min={1} max={100} {...field} />
                  </FormControl>
                  <FormDescription>该模型建议的最大并发限制</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* 启用状态 */}
            <FormField
              control={form.control}
              name="enabled"
              render={({ field }) => (
                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                  <div className="space-y-0.5">
                    <FormLabel className="text-base">启用模型</FormLabel>
                    <FormDescription>关闭后用户将无法使用该模型</FormDescription>
                  </div>
                  <FormControl>
                    <Switch checked={field.value} onCheckedChange={field.onChange} />
                  </FormControl>
                </FormItem>
              )}
            />

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                取消
              </Button>
              <Button type="submit" disabled={updateMutation.isPending}>
                {updateMutation.isPending ? '保存中...' : '保存修改'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
