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

import { useCreateModel } from '@/hooks/useKeys';

interface CreateModelDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: (modelKey: string) => void;
}

// 表单 Schema
const formSchema = z.object({
  key: z
    .string()
    .min(2, '模型标识至少2个字符')
    .max(50, '模型标识最多50个字符')
    .regex(/^[a-z0-9_.-]+$/, '仅支持小写字母、数字、下划线、点、中划线'),
  name: z.string().min(2, '模型名称至少2个字符').max(100, '模型名称最多100个字符'),
  enabled: z.boolean(),
  description: z.string().max(500, '描述最多500个字符').optional(),
  color: z.string().optional(),
  icon_url: z.string().url('请输入有效的URL').or(z.literal('')).optional(),
  max_concurrency_limit: z.coerce.number().min(1).max(100).optional(),
});

type FormValues = z.infer<typeof formSchema>;

export function CreateModelDialog({ open, onOpenChange, onSuccess }: CreateModelDialogProps) {
  const createMutation = useCreateModel();

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      key: '',
      name: '',
      enabled: true,
      description: '',
      color: 'bg-blue-500',
      icon_url: '',
      max_concurrency_limit: 20,
    },
  });

  const onSubmit = async (values: FormValues) => {
    try {
      // 清理空字符串为 undefined
      const data = {
        ...values,
        icon_url: values.icon_url || undefined,
        description: values.description || undefined,
      };

      const result = await createMutation.mutateAsync(data);

      if (result.code === 0) {
        toast.success('模型创建成功');
        form.reset();
        onOpenChange(false);
        onSuccess?.(values.key);
      }
    } catch (error: any) {
      toast.error(error.message || '创建失败');
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>添加新模型</DialogTitle>
          <DialogDescription>创建一个新的AI模型配置</DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            {/* 模型标识 */}
            <FormField
              control={form.control}
              name="key"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>模型标识 *</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="例如: gpt-4, claude-3-opus"
                      {...field}
                      className="font-mono"
                    />
                  </FormControl>
                  <FormDescription>
                    唯一标识符，支持小写字母、数字、下划线、点、中划线
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

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
                    <FormDescription>创建后立即启用该模型</FormDescription>
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
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending ? '创建中...' : '创建模型'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
