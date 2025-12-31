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
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';

import type { Key } from '@/types/key';
import { useUpdateKey } from '@/hooks/useKeys';

interface KeyEditDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  keyData: Key | null;
}

// 编辑表单 Schema
const editSchema = z.object({
  max_concurrency: z.coerce.number().min(1).max(100),
  weight: z.coerce.number().min(1).max(100),
  status: z.union([z.literal(0), z.literal(1)]),
});

type EditFormValues = z.infer<typeof editSchema>;

export function KeyEditDialog({ open, onOpenChange, keyData }: KeyEditDialogProps) {
  const updateMutation = useUpdateKey();

  const form = useForm<EditFormValues>({
    resolver: zodResolver(editSchema),
    defaultValues: {
      max_concurrency: 3,
      weight: 10,
      status: 1,
    },
  });

  // 当 keyData 变化时，更新表单默认值
  useEffect(() => {
    if (keyData) {
      form.reset({
        max_concurrency: keyData.max_concurrency,
        weight: keyData.weight,
        status: keyData.status,
      });
    }
  }, [keyData, form]);

  const onSubmit = async (values: EditFormValues) => {
    if (!keyData) return;

    try {
      const result = await updateMutation.mutateAsync({
        id: keyData.id,
        data: values,
      });

      if (result.code === 0) {
        toast.success('密钥配置已更新');
        onOpenChange(false);
      }
    } catch (error: any) {
      toast.error(error.message || '更新失败');
    }
  };

  if (!keyData) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>编辑密钥配置</DialogTitle>
          <DialogDescription>
            修改密钥的并发数、权重和状态设置
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            {/* 密钥信息展示 */}
            <div className="rounded-lg border p-4 bg-muted/50">
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">ID:</span>
                  <span className="font-mono">{keyData.id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">平台:</span>
                  <span className="font-semibold">{keyData.platform.toUpperCase()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">密钥:</span>
                  <code className="text-xs bg-background px-2 py-1 rounded">
                    {keyData.key_secret.slice(0, 10)}...
                  </code>
                </div>
              </div>
            </div>

            {/* 最大并发数 */}
            <FormField
              control={form.control}
              name="max_concurrency"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>最大并发数 *</FormLabel>
                  <FormControl>
                    <div className="space-y-2">
                      <Slider
                        min={1}
                        max={20}
                        step={1}
                        value={[field.value]}
                        onValueChange={(v) => field.onChange(v[0])}
                      />
                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span>1</span>
                        <span className="font-semibold text-foreground">{field.value}</span>
                        <span>20</span>
                      </div>
                    </div>
                  </FormControl>
                  <FormDescription>
                    该密钥同时运行的最大任务数（当前使用: {keyData.current_usage}）
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* 权重 */}
            <FormField
              control={form.control}
              name="weight"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>权重 *</FormLabel>
                  <FormControl>
                    <div className="space-y-2">
                      <Slider
                        min={1}
                        max={100}
                        step={1}
                        value={[field.value]}
                        onValueChange={(v) => field.onChange(v[0])}
                      />
                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span>1</span>
                        <span className="font-semibold text-foreground">{field.value}</span>
                        <span>100</span>
                      </div>
                    </div>
                  </FormControl>
                  <FormDescription>权重越高，被选中概率越大</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* 状态 */}
            <FormField
              control={form.control}
              name="status"
              render={({ field }) => (
                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                  <div className="space-y-0.5">
                    <FormLabel className="text-base">启用状态</FormLabel>
                    <FormDescription>关闭后密钥将不会被分配给新任务</FormDescription>
                  </div>
                  <FormControl>
                    <Switch
                      checked={field.value === 1}
                      onCheckedChange={(checked) => field.onChange(checked ? 1 : 0)}
                    />
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
