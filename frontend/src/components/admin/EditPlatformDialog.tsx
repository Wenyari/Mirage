import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { toast } from 'sonner';

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
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';

import type { PlatformConfig } from '@/types/key';
import { useUpdatePlatform } from '@/hooks/useKeys';

interface EditPlatformDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  platform?: PlatformConfig;
}

// 表单 Schema
const formSchema = z.object({
  name: z.string().min(2, '平台名称至少2个字符').max(100, '平台名称最多100个字符'),
  enabled: z.boolean(),
  description: z.string().max(500, '描述最多500个字符').optional(),
  color: z.string().optional(),
  icon_url: z.string().url('请输入有效的URL').or(z.literal('')).optional(),
  max_concurrency_limit: z.coerce.number().min(1).max(100).optional(),
});

type FormValues = z.infer<typeof formSchema>;

export function EditPlatformDialog({ open, onOpenChange, platform }: EditPlatformDialogProps) {
  const updateMutation = useUpdatePlatform();

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: '',
      enabled: true,
      description: '',
      color: 'bg-blue-500',
      icon_url: '',
      max_concurrency_limit: 20,
    },
  });

  // 当平台数据变化时，更新表单
  useEffect(() => {
    if (platform) {
      form.reset({
        name: platform.name,
        enabled: platform.enabled,
        description: platform.description || '',
        color: platform.color || 'bg-blue-500',
        icon_url: platform.icon_url || platform.icon || '',
        max_concurrency_limit: platform.max_concurrency_limit || 20,
      });
    }
  }, [platform, form]);

  const onSubmit = async (values: FormValues) => {
    if (!platform) return;

    try {
      // 清理空字符串为 undefined
      const data = {
        ...values,
        icon_url: values.icon_url || undefined,
        description: values.description || undefined,
      };

      const result = await updateMutation.mutateAsync({
        key: platform.key,
        data,
      });

      if (result.code === 0) {
        toast.success('平台更新成功');
        onOpenChange(false);
      }
    } catch (error: any) {
      toast.error(error.message || '更新失败');
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>编辑平台</DialogTitle>
          <DialogDescription>
            修改平台配置信息（平台标识不可修改）
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            {/* 平台标识（只读） */}
            {platform && (
              <div className="space-y-2">
                <label className="text-sm font-medium">平台标识</label>
                <Input value={platform.key} disabled className="font-mono bg-muted" />
                <p className="text-xs text-muted-foreground">平台标识不可修改</p>
              </div>
            )}

            {/* 平台名称 */}
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>平台名称 *</FormLabel>
                  <FormControl>
                    <Input placeholder="例如: OpenAI, Claude, Gemini" {...field} />
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
                      placeholder="平台功能描述（可选）"
                      className="resize-none"
                      {...field}
                    />
                  </FormControl>
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
                  <FormDescription>平台图标URL（可选）</FormDescription>
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
                  <FormDescription>该平台建议的最大并发限制</FormDescription>
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
                    <FormLabel className="text-base">启用平台</FormLabel>
                    <FormDescription>关闭后用户将无法使用该平台</FormDescription>
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
