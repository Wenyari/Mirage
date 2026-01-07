import { zodResolver } from '@hookform/resolvers/zod';
import { useEffect, useState } from 'react';
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
import { Switch } from '@/components/ui/switch';
import { useModels, useUpdateKey } from '@/hooks/useKeys';
import type { Key, ModelConfig } from '@/types/key';

interface KeyEditDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  keyData: Key | null;
}

// 详细配置 Schema
const modelConfigSchema = z.object({
  model: z.string(),
  api_base: z.string().url('请输入有效的 URL').optional().or(z.literal('')),
});

// 编辑表单 Schema
const editSchema = z.object({
  models: z.array(z.string()).min(1, '请至少选择一个模型'),
  use_advanced_config: z.boolean().default(false),
  model_configs: z.array(modelConfigSchema).optional(),
  max_concurrency: z.coerce.number().min(1).max(100),
  weight: z.coerce.number().min(1).max(100),
  status: z.union([z.literal(0), z.literal(1)]),
});

type EditFormValues = z.infer<typeof editSchema>;

export function KeyEditDialog({ open, onOpenChange, keyData }: KeyEditDialogProps) {
  const updateMutation = useUpdateKey();
  const { data: modelsData, isLoading: modelsLoading } = useModels();
  const [showCreateModelDialog, setShowCreateModelDialog] = useState(false);

  // 获取启用的模型列表
  const enabledModels = modelsData?.data?.filter((p) => p.enabled) || [];

  const form = useForm<EditFormValues>({
    resolver: zodResolver(editSchema),
    defaultValues: {
      models: [],
      use_advanced_config: false,
      model_configs: [],
      max_concurrency: 3,
      weight: 10,
      status: 1,
    },
  });

  const watchAdvanced = form.watch('use_advanced_config');

  // 当 keyData 变化时，更新表单默认值
  useEffect(() => {
    if (keyData) {
      const hasConfigs = keyData.model_configs && keyData.model_configs.length > 0;
      
      form.reset({
        models: keyData.models || [],
        use_advanced_config: hasConfigs,
        model_configs: keyData.model_configs || [],
        max_concurrency: keyData.max_concurrency,
        weight: keyData.weight,
        status: keyData.status,
      });
    }
  }, [keyData, form]);

  const onSubmit = async (values: EditFormValues) => {
    if (!keyData) return;

    try {
      let finalModels: string[] | ModelConfig[] = values.models;

      // 如果启用了高级配置，构造 ModelConfig 数组
      if (values.use_advanced_config && values.model_configs) {
        finalModels = values.models.map(modelKey => {
          const config = values.model_configs?.find(c => c.model === modelKey);
          // 如果没有特定配置，且原 keyData 有 api_base，是否应该回退？
          // 编辑模式下，我们主要关注 model_configs。
          // 如果用户开启了高级模式，我们假设他们想要完全控制。
          return {
            model: modelKey,
            api_base: config?.api_base || '' 
          };
        });
      }

      const result = await updateMutation.mutateAsync({
        id: keyData.id,
        data: {
          models: finalModels, // 这里的类型在 UpdateKeyRequest 中已经是 ModelType[] | ModelConfig[]
          max_concurrency: values.max_concurrency,
          weight: values.weight,
          status: values.status,
        },
      });

      if (result.code === 0) {
        toast.success('密钥配置已更新');
        onOpenChange(false);
      }
    } catch (error: any) {
      toast.error(error.message || '更新失败');
    }
  };

  // 创建模型成功后的回调
  const handleModelCreated = (modelKey: string) => {
    const currentModels = form.getValues('models');
    form.setValue('models', [...currentModels, modelKey]);
  };

  // 渲染模型多选器 (复用 KeyAddDialog 的逻辑)
  const renderModelSelect = (field: any) => {
    return (
      <div className="space-y-3">
        <div className="flex flex-wrap gap-2 mb-2">
          {field.value.map((modelKey: string) => {
            const model = enabledModels.find(m => m.key === modelKey);
            return (
              <Badge key={modelKey} variant="secondary" className="flex items-center gap-1">
                {model?.name || modelKey}
                <span 
                  className="cursor-pointer ml-1 text-muted-foreground hover:text-foreground"
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
                {enabledModels.map((model) => (
                  <div key={model.key} className="flex items-center space-x-2">
                    <Checkbox 
                      id={`edit-model-${model.key}`}
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
                        const validConfigs = currentConfigs.filter((c: any) => newModels.includes(c.model));
                        newModels.forEach((m: string) => {
                          if (!validConfigs.find((c: any) => c.model === m)) {
                            // 如果是新选中的，且原 keyData 有该模型的配置，尝试恢复？
                            // 简化起见，初始化为空
                            validConfigs.push({ model: m, api_base: '' });
                          }
                        });
                        form.setValue('model_configs', validConfigs);
                      }}
                    />
                    <label
                      htmlFor={`edit-model-${model.key}`}
                      className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
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
          className="text-primary hover:text-primary/80 h-auto p-0"
          onClick={() => setShowCreateModelDialog(true)}
        >
          + 添加新模型
        </Button>
      </div>
    );
  };

  // 渲染高级配置
  const renderAdvancedConfig = () => {
    const models = form.watch('models');
    const modelConfigs = form.watch('model_configs') || [];

    if (!models || models.length === 0) return null;

    return (
      <div className="space-y-4 rounded-md border p-4 bg-muted/30">
        <div className="text-sm font-medium mb-2">分模型 API Base 配置</div>
        <div className="space-y-3">
          {models.map((modelKey: string) => {
            const modelName = enabledModels.find(m => m.key === modelKey)?.name || modelKey;
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

  if (!keyData) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>编辑密钥配置</DialogTitle>
          <DialogDescription>
            修改密钥的模型关联、并发数、权重和状态设置
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            {/* 密钥信息展示 */}
            <div className="rounded-lg border bg-muted/50 p-4">
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">ID:</span>
                  <span className="font-mono">{keyData.id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">密钥:</span>
                  <code className="rounded bg-background px-2 py-1 text-xs">
                    {keyData.key_secret.slice(0, 10)}...
                  </code>
                </div>
              </div>
            </div>

            {/* 模型选择 */}
            <FormField
              control={form.control}
              name="models"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>适用模型 *</FormLabel>
                  <FormControl>
                    {renderModelSelect(field)}
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* 高级配置开关 */}
            <FormField
              control={form.control}
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

            {watchAdvanced && renderAdvancedConfig()}

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

      {/* 创建模型对话框 */}
      <CreateModelDialog
        open={showCreateModelDialog}
        onOpenChange={setShowCreateModelDialog}
        onSuccess={handleModelCreated}
      />
    </Dialog>
  );
}
