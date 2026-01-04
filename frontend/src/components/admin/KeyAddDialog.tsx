import { zodResolver } from '@hookform/resolvers/zod';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';
import * as z from 'zod';

import { CreateModelDialog } from '@/components/admin/CreateModelDialog';
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
import { Separator } from '@/components/ui/separator';
import { Slider } from '@/components/ui/slider';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { useAddKey, useBatchAddKeys, useModels } from '@/hooks/useKeys';
import type { ModelType } from '@/types/key';

interface KeyAddDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

// 单个添加表单 Schema（动态验证模型）
const singleSchema = z.object({
  model: z.string().min(1, '请选择模型'),
  api_base: z.string().url('请输入有效的 URL').optional().or(z.literal('')),
  key_secret: z.string().min(10, '密钥长度至少10个字符'),
  max_concurrency: z.coerce.number().min(1).max(100),
  weight: z.coerce.number().min(1).max(100),
});

// 批量添加表单 Schema（动态验证模型）
const batchSchema = z.object({
  model: z.string().min(1, '请选择模型'),
  api_base: z.string().url('请输入有效的 URL').optional().or(z.literal('')),
  keys: z.string().min(1, '请输入至少一个密钥'),
  max_concurrency: z.coerce.number().min(1).max(100),
  weight: z.coerce.number().min(1).max(100),
});

type SingleFormValues = z.infer<typeof singleSchema>;
type BatchFormValues = z.infer<typeof batchSchema>;

export function KeyAddDialog({ open, onOpenChange }: KeyAddDialogProps) {
  const [mode, setMode] = useState<'single' | 'batch'>('single');
  const [weightValue, setWeightValue] = useState([10]);
  const [concurrencyValue, setConcurrencyValue] = useState([3]);
  const [showCreateModelDialog, setShowCreateModelDialog] = useState(false);

  const addMutation = useAddKey();
  const batchAddMutation = useBatchAddKeys();
  const { data: modelsData, isLoading: modelsLoading } = useModels();

  // 获取启用的模型列表
  const enabledModels = modelsData?.data?.filter((p) => p.enabled) || [];

  // 单个添加表单
  const singleForm = useForm<SingleFormValues>({
    resolver: zodResolver(singleSchema),
    defaultValues: {
      api_base: '',
      max_concurrency: 3,
      weight: 10,
    },
  });

  // 批量添加表单
  const batchForm = useForm<BatchFormValues>({
    resolver: zodResolver(batchSchema),
    defaultValues: {
      api_base: '',
      max_concurrency: 3,
      weight: 10,
    },
  });

  // 单个添加提交
  const onSingleSubmit = async (values: SingleFormValues) => {
    try {
      const result = await addMutation.mutateAsync(values);
      if (result.code === 0) {
        toast.success('密钥添加成功');
        singleForm.reset();
        onOpenChange(false);
      }
    } catch (error: any) {
      toast.error(error.message || '添加失败');
    }
  };

  // 批量添加提交
  const onBatchSubmit = async (values: BatchFormValues) => {
    try {
      // 解析密钥列表
      const keys = values.keys
        .split('\n')
        .map((line) => line.trim())
        .filter((line) => line.length > 0);

      if (keys.length === 0) {
        toast.error('请输入至少一个密钥');
        return;
      }

      if (keys.length > 100) {
        toast.error('单次最多导入 100 个密钥');
        return;
      }

      const result = await batchAddMutation.mutateAsync({
        model: values.model,
        keys,
        max_concurrency: values.max_concurrency,
        weight: values.weight,
      });

      if (result.success) {
        const { success_count, failed_count } = result.data;
        if (failed_count === 0) {
          toast.success(`成功导入 ${success_count} 个密钥`);
        } else {
          toast.warning(
            `导入完成：${success_count} 个成功，${failed_count} 个失败（可能重复）`
          );
        }
        batchForm.reset();
        onOpenChange(false);
      }
    } catch (error: any) {
      toast.error(error.message || '批量添加失败');
    }
  };

  // 创建模型成功后的回调
  const handleModelCreated = (modelKey: string) => {
    // 自动选择新创建的模型
    singleForm.setValue('model', modelKey);
    batchForm.setValue('model', modelKey);
  };

  // 渲染模型选择器
  const renderModelSelect = (field: any, form: any) => {
    const handleValueChange = (value: string) => {
      if (value === '__add_new__') {
        setShowCreateModelDialog(true);
      } else {
        field.onChange(value);
      }
    };

    return (
      <Select onValueChange={handleValueChange} value={field.value}>
        <FormControl>
          <SelectTrigger>
            <SelectValue placeholder="选择模型" />
          </SelectTrigger>
        </FormControl>
        <SelectContent>
          {modelsLoading ? (
            <SelectItem value="loading" disabled>
              加载中...
            </SelectItem>
          ) : (
            <>
              {enabledModels.map((model) => (
                <SelectItem key={model.key} value={model.key}>
                  {model.name}
                </SelectItem>
              ))}
              <Separator className="my-1" />
              <SelectItem value="__add_new__" className="font-medium text-primary">
                + 添加新模型
              </SelectItem>
            </>
          )}
        </SelectContent>
      </Select>
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>添加 API 密钥</DialogTitle>
          <DialogDescription>
            支持单个添加或批量导入密钥
          </DialogDescription>
        </DialogHeader>

        <Tabs value={mode} onValueChange={(v) => setMode(v as 'single' | 'batch')}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="single">单个添加</TabsTrigger>
            <TabsTrigger value="batch">批量导入</TabsTrigger>
          </TabsList>

          {/* 单个添加 */}
          <TabsContent value="single" className="mt-4 space-y-4">
            <Form {...singleForm}>
              <form onSubmit={singleForm.handleSubmit(onSingleSubmit)} className="space-y-4">
                <FormField
                  control={singleForm.control}
                  name="model"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>模型 *</FormLabel>
                      {renderModelSelect(field, singleForm)}
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={singleForm.control}
                  name="api_base"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>API Base URL (可选)</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="例如: https://api.openai.com/v1"
                          {...field}
                          className="font-mono text-sm"
                        />
                      </FormControl>
                      <FormDescription>如果不填，则默认使用该模型的官方地址</FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={singleForm.control}
                  name="key_secret"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>API 密钥 *</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="sk-proj-..."
                          {...field}
                          className="font-mono text-sm"
                        />
                      </FormControl>
                      <FormDescription>完整的 API 密钥字符串</FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={singleForm.control}
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
                            onValueChange={(v) => {
                              field.onChange(v[0]);
                              setConcurrencyValue(v);
                            }}
                          />
                          <div className="flex justify-between text-xs text-muted-foreground">
                            <span>1</span>
                            <span className="font-semibold text-foreground">{field.value}</span>
                            <span>20</span>
                          </div>
                        </div>
                      </FormControl>
                      <FormDescription>该密钥同时运行的最大任务数</FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={singleForm.control}
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
                            onValueChange={(v) => {
                              field.onChange(v[0]);
                              setWeightValue(v);
                            }}
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

                <DialogFooter>
                  <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                    取消
                  </Button>
                  <Button type="submit" disabled={addMutation.isPending}>
                    {addMutation.isPending ? '添加中...' : '添加密钥'}
                  </Button>
                </DialogFooter>
              </form>
            </Form>
          </TabsContent>

          {/* 批量导入 */}
          <TabsContent value="batch" className="mt-4 space-y-4">
            <Form {...batchForm}>
              <form onSubmit={batchForm.handleSubmit(onBatchSubmit)} className="space-y-4">
                <FormField
                  control={batchForm.control}
                  name="model"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>模型 *</FormLabel>
                      {renderModelSelect(field, batchForm)}
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={batchForm.control}
                  name="api_base"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>API Base URL (可选)</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="例如: https://api.openai.com/v1"
                          {...field}
                          className="font-mono text-sm"
                        />
                      </FormControl>
                      <FormDescription>所有批量导入的密钥将共用此 API 地址</FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={batchForm.control}
                  name="keys"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>API 密钥列表 *</FormLabel>
                      <FormControl>
                        <Textarea
                          placeholder="每行一个密钥，例如：&#10;sk-proj-abc123...&#10;sk-proj-def456...&#10;sk-proj-ghi789..."
                          className="min-h-[150px] font-mono text-sm"
                          {...field}
                        />
                      </FormControl>
                      <FormDescription>
                        每行一个密钥，最多 100 个
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <div className="grid grid-cols-2 gap-4">
                  <FormField
                    control={batchForm.control}
                    name="max_concurrency"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>最大并发数 *</FormLabel>
                        <FormControl>
                          <Input type="number" min={1} max={20} {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={batchForm.control}
                    name="weight"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>权重 *</FormLabel>
                        <FormControl>
                          <Input type="number" min={1} max={100} {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>

                <DialogFooter>
                  <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                    取消
                  </Button>
                  <Button type="submit" disabled={batchAddMutation.isPending}>
                    {batchAddMutation.isPending ? '导入中...' : '批量导入'}
                  </Button>
                </DialogFooter>
              </form>
            </Form>
          </TabsContent>
        </Tabs>
      </DialogContent>

      {/* 创建模型对话框 */}
      <CreateModelDialog
        open={showCreateModelDialog}
        onOpenChange={setShowCreateModelDialog}
        onSuccess={handleModelCreated}
      />
    </Dialog>
  );
}
