import { zodResolver } from '@hookform/resolvers/zod';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';
import * as z from 'zod';

import { CreateModelDialog } from '@/components/admin/CreateModelDialog';
import { Badge } from "@/components/ui/badge";
import { Button } from '@/components/ui/button';
import { Checkbox } from "@/components/ui/checkbox";
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
import { ScrollArea } from "@/components/ui/scroll-area";
import { Slider } from '@/components/ui/slider';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from "@/components/ui/switch";
import { useAddKey, useBatchAddKeys, useModels } from '@/hooks/useKeys';
import type { ModelConfig } from '@/types/key';

interface KeyAddDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

// 详细配置 Schema
const modelConfigSchema = z.object({
  model: z.string(),
  api_base: z.string().url('请输入有效的 URL').optional().or(z.literal('')),
});

// 单个添加表单 Schema（动态验证模型）
const singleSchema = z.object({
  models: z.array(z.string()).min(1, '请至少选择一个模型'),
  use_advanced_config: z.boolean().default(false), // 是否启用高级配置（分模型配置 api_base）
  model_configs: z.array(modelConfigSchema).optional(), // 高级配置
  api_base: z.string().url('请输入有效的 URL').optional().or(z.literal('')),
  key_secret: z.string().min(10, '密钥长度至少10个字符'),
  max_concurrency: z.coerce.number().min(1).max(100),
  weight: z.coerce.number().min(1).max(100),
});

// 批量添加表单 Schema（动态验证模型）
const batchSchema = z.object({
  models: z.array(z.string()).min(1, '请至少选择一个模型'),
  use_advanced_config: z.boolean().default(false),
  model_configs: z.array(modelConfigSchema).optional(),
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
  const enabledModels = (modelsData as any)?.data?.filter((p: any) => p.enabled) || [];

  // 单个添加表单
  const singleForm = useForm<SingleFormValues>({
    resolver: zodResolver(singleSchema),
    defaultValues: {
      models: [],
      use_advanced_config: false,
      model_configs: [],
      api_base: '',
      max_concurrency: 3,
      weight: 10,
    },
  });

  // 批量添加表单
  const batchForm = useForm<BatchFormValues>({
    resolver: zodResolver(batchSchema),
    defaultValues: {
      models: [],
      use_advanced_config: false,
      model_configs: [],
      api_base: '',
      max_concurrency: 3,
      weight: 10,
    },
  });

  // 监听 models 变化，自动更新 model_configs
  const watchSingleModels = singleForm.watch('models');
  const watchBatchModels = batchForm.watch('models');
  const watchSingleAdvanced = singleForm.watch('use_advanced_config');
  const watchBatchAdvanced = batchForm.watch('use_advanced_config');

  // 单个添加提交
  const onSingleSubmit = async (values: SingleFormValues) => {
    try {
      let finalModels: string[] | ModelConfig[] = values.models;

      // 如果启用了高级配置，构造 ModelConfig 数组
      if (values.use_advanced_config && values.model_configs) {
        // 确保 model_configs 里的 api_base 有值才使用
        finalModels = values.models.map(modelKey => {
          const config = values.model_configs?.find(c => c.model === modelKey);
          return {
            model: modelKey,
            api_base: config?.api_base || values.api_base || '' // 优先使用具体配置，否则使用全局，最后为空
          };
        });
      }

      const result = await addMutation.mutateAsync({
        ...values,
        models: finalModels,
      });

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

      let finalModels: string[] | ModelConfig[] = values.models;

      // 如果启用了高级配置，构造 ModelConfig 数组
      if (values.use_advanced_config && values.model_configs) {
        finalModels = values.models.map(modelKey => {
          const config = values.model_configs?.find(c => c.model === modelKey);
          return {
            model: modelKey,
            api_base: config?.api_base || values.api_base || ''
          };
        });
      }

      const result = await batchAddMutation.mutateAsync({
        models: finalModels,
        keys,
        max_concurrency: values.max_concurrency,
        weight: values.weight,
        api_base: values.api_base, // 仍然传递全局 api_base 作为回退
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
    // 自动追加新创建的模型
    const currentSingle = singleForm.getValues('models');
    singleForm.setValue('models', [...currentSingle, modelKey]);

    const currentBatch = batchForm.getValues('models');
    batchForm.setValue('models', [...currentBatch, modelKey]);
  };

  // 渲染模型多选器
  const renderModelSelect = (field: any, form: any) => {
    return (
      <div className="space-y-3">
        <div className="mb-2 flex flex-wrap gap-2">
          {field.value.map((modelKey: string) => {
            const model = enabledModels.find((m: { key: string; }) => m.key === modelKey);
            return (
              <Badge key={modelKey} variant="secondary" className="flex items-center gap-1">
                {model?.name || modelKey}
                <span
                  className="ml-1 cursor-pointer text-muted-foreground hover:text-foreground"
                  onClick={() => {
                    field.onChange(field.value.filter((k: string) => k !== modelKey));
                  }}
                >
                  ×
                </span>
              </Badge>
            );
          })}
        </div>

        <ScrollArea className="h-[120px] w-full rounded-md border p-4">
          <div className="grid grid-cols-2 gap-4">
            {modelsLoading ? (
              <div className="text-sm text-muted-foreground">加载中...</div>
            ) : (
              <>
                {enabledModels.map((model: any) => (
                  <div key={model.key} className="flex items-center space-x-2">
                    <Checkbox
                      id={`model-${model.key}-${mode}`}
                      checked={field.value.includes(model.key)}
                      onCheckedChange={(checked) => {
                        let newModels;
                        if (checked) {
                          newModels = [...field.value, model.key];
                        } else {
                          newModels = field.value.filter((k: string) => k !== model.key);
                        }
                        field.onChange(newModels);

                        // 同步更新 model_configs
                        const currentConfigs = form.getValues('model_configs') || [];
                        // 移除不在 newModels 里的配置
                        const validConfigs = currentConfigs.filter((c: any) => newModels.includes(c.model));
                        // 为新添加的模型添加默认空配置（如果不存在）
                        newModels.forEach((m: string) => {
                          if (!validConfigs.find((c: any) => c.model === m)) {
                            validConfigs.push({ model: m, api_base: '' });
                          }
                        });
                        form.setValue('model_configs', validConfigs);
                      }}
                    />
                    <label
                      htmlFor={`model-${model.key}-${mode}`}
                      className="cursor-pointer text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                    >
                      {model.name}
                    </label>
                  </div>
                ))}
              </>
            )}
          </div>
        </ScrollArea>

        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="h-auto p-0 text-primary hover:text-primary/80"
          onClick={() => setShowCreateModelDialog(true)}
        >
          + 添加新模型
        </Button>
      </div>
    );
  };

  // 渲染高级配置（每个模型的 API Base）
  const renderAdvancedConfig = (form: any) => {
    const models = form.watch('models');
    const modelConfigs = form.watch('model_configs') || [];

    if (!models || models.length === 0) return null;

    return (
      <div className="space-y-4 rounded-md border p-4 bg-muted/30">
        <div className="text-sm font-medium mb-2">分模型 API Base 配置</div>
        <div className="space-y-3">
          {models.map((modelKey: string, index: number) => {
            const modelName = enabledModels.find((m: { key: string; }) => m.key === modelKey)?.name || modelKey;
            // 找到对应的 config index
            const configIndex = modelConfigs.findIndex((c: any) => c.model === modelKey);

            return (
              <div key={modelKey} className="grid grid-cols-[120px_1fr] items-center gap-4">
                <span className="text-sm text-muted-foreground truncate" title={modelName}>{modelName}</span>
                <Input
                  placeholder="特定 API Base URL (可选)"
                  className="h-8 text-xs font-mono"
                  value={modelConfigs[configIndex]?.api_base || ''}
                  onChange={(e) => {
                    const newConfigs = [...modelConfigs];
                    if (configIndex >= 0) {
                      newConfigs[configIndex] = { ...newConfigs[configIndex], api_base: e.target.value };
                    } else {
                      newConfigs.push({ model: modelKey, api_base: e.target.value });
                    }
                    form.setValue('model_configs', newConfigs);
                  }}
                />
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>添加 API 密钥</DialogTitle>
          <DialogDescription>
            支持单个添加或批量导入密钥，可同时关联多个模型
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
                  name="models"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>适用模型 *</FormLabel>
                      <FormControl>
                        {renderModelSelect(field, singleForm)}
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={singleForm.control}
                  name="api_base"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>默认 API Base URL (可选)</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="例如: https://api.openai.com/v1"
                          {...field}
                          className="font-mono text-sm"
                        />
                      </FormControl>
                      <FormDescription>
                        如果不填，则默认使用该模型的官方地址。
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={singleForm.control}
                  name="use_advanced_config"
                  render={({ field }) => (
                    <FormItem className="flex flex-row items-center justify-between rounded-lg border p-3 shadow-sm">
                      <div className="space-y-0.5">
                        <FormLabel>高级配置</FormLabel>
                        <FormDescription>
                          为每个模型单独配置 API Base URL
                        </FormDescription>
                      </div>
                      <FormControl>
                        <Switch
                          checked={field.value}
                          onCheckedChange={field.onChange}
                        />
                      </FormControl>
                    </FormItem>
                  )}
                />

                {watchSingleAdvanced && renderAdvancedConfig(singleForm)}

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
                  name="models"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>适用模型 *</FormLabel>
                      <FormControl>
                        {renderModelSelect(field, batchForm)}
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={batchForm.control}
                  name="api_base"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>默认 API Base URL (可选)</FormLabel>
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
                  name="use_advanced_config"
                  render={({ field }) => (
                    <FormItem className="flex flex-row items-center justify-between rounded-lg border p-3 shadow-sm">
                      <div className="space-y-0.5">
                        <FormLabel>高级配置</FormLabel>
                        <FormDescription>
                          为每个模型单独配置 API Base URL
                        </FormDescription>
                      </div>
                      <FormControl>
                        <Switch
                          checked={field.value}
                          onCheckedChange={field.onChange}
                        />
                      </FormControl>
                    </FormItem>
                  )}
                />

                {watchBatchAdvanced && renderAdvancedConfig(batchForm)}

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
