import { zodResolver } from '@hookform/resolvers/zod';
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';
import * as z from 'zod';

import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
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
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import {
  useAvailableModels,
  useCreateModelConfig,
  useUpdateModelConfig,
} from '@/hooks/useModelConfigs';
import type { MembershipTier, ModelConfig } from '@/types/modelConfig';
import { ALL_MEMBERSHIP_TIERS, MEMBERSHIP_TIER_LABELS } from '@/types/modelConfig';

interface ModelConfigDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  mode: 'create' | 'edit';
  config?: ModelConfig;
}

// 表单 Schema
const formSchema = z.object({
  model: z.string().min(1, '请选择模型'),
  allowed_tiers: z.array(z.string()).min(1, '请至少选择一个等级'),
  cost_per_call: z.coerce.number().min(0, '固定计费不能为负数'),
  token_cost_enabled: z.boolean(),
  token_input_cost: z.coerce.number().min(0).optional(),
  token_output_cost: z.coerce.number().min(0).optional(),
  params: z.string().optional().refine((val) => {
    if (!val) return true;
    try {
      JSON.parse(val);
      return true;
    } catch {
      return false;
    }
  }, '必须是有效的 JSON 格式'),
  is_active: z.boolean(),
  description: z.string().optional(),
});

type FormValues = z.infer<typeof formSchema>;

export function ModelConfigDialog({ open, onOpenChange, mode, config }: ModelConfigDialogProps) {
  const createMutation = useCreateModelConfig();
  const updateMutation = useUpdateModelConfig();
  const { data: availableModelsData } = useAvailableModels();

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      model: '',
      allowed_tiers: ['T1', 'T2', 'T3', 'T4', 'T5'],
      cost_per_call: 10,
      token_cost_enabled: false,
      token_input_cost: 0.03,
      token_output_cost: 0.06,
      params: '',
      is_active: true,
      description: '',
    },
  });

  const tokenCostEnabled = form.watch('token_cost_enabled');

  // 编辑模式时，填充表单数据
  useEffect(() => {
    if (mode === 'edit' && config) {
      form.reset({
        model: config.model,
        allowed_tiers: config.allowed_tiers,
        cost_per_call: config.cost_per_call,
        token_cost_enabled: config.token_cost_config.enabled,
        token_input_cost: config.token_cost_config.input_cost || 0,
        token_output_cost: config.token_cost_config.output_cost || 0,
        params: config.params ? JSON.stringify(config.params, null, 2) : '',
        is_active: Boolean(config.is_active),
        description: config.description || '',
      });
    } else {
      form.reset({
        model: '',
        allowed_tiers: ['T1', 'T2', 'T3', 'T4', 'T5'],
        cost_per_call: 10,
        token_cost_enabled: false,
        token_input_cost: 0.03,
        token_output_cost: 0.06,
        params: '',
        is_active: true,
        description: '',
      });
    }
  }, [mode, config, form]);

  const onSubmit = async (values: FormValues) => {
    try {
      const requestData = {
        model: values.model,
        allowed_tiers: values.allowed_tiers as MembershipTier[],
        cost_per_call: values.cost_per_call,
        token_cost_config: {
          enabled: values.token_cost_enabled,
          ...(values.token_cost_enabled && {
            input_cost: values.token_input_cost || 0,
            output_cost: values.token_output_cost || 0,
          }),
        },
        params: values.params ? JSON.parse(values.params) : null,
        is_active: values.is_active,
        description: values.description || '',
      };

      if (mode === 'create') {
        await createMutation.mutateAsync(requestData);
        toast.success('模型配置已创建');
      } else if (config) {
        await updateMutation.mutateAsync({
          id: config.id,
          data: requestData,
        });
        toast.success('模型配置已更新');
      }

      onOpenChange(false);
      form.reset();
    } catch (err: any) {
      toast.error(err.message || '操作失败');
    }
  };

  // 可选择的模型列表（创建模式）
  const availableModels = (availableModelsData as any)?.data?.filter((m: any) => !m.has_config) || [];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] max-w-2xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{mode === 'create' ? '添加模型配置' : '编辑模型配置'}</DialogTitle>
          <DialogDescription>
            {mode === 'create'
              ? '为新模型配置等级权限和计费规则'
              : '修改模型的等级权限和计费规则'}
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            {/* 模型选择 */}
            <FormField
              control={form.control}
              name="model"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>模型 *</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    defaultValue={field.value}
                    disabled={mode === 'edit'}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="选择模型" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {mode === 'edit' && config ? (
                        <SelectItem value={config.model}>{config.model_name}</SelectItem>
                      ) : (
                        availableModels.map((model: any) => (
                          <SelectItem key={model.model} value={model.model}>
                            {model.model_name} ({model.key_count} 个密钥)
                          </SelectItem>
                        ))
                      )}
                    </SelectContent>
                  </Select>
                  <FormDescription>
                    {mode === 'edit' ? '模型标识不可修改' : '选择要配置的模型'}
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* 允许等级 */}
            <FormField
              control={form.control}
              name="allowed_tiers"
              render={() => (
                <FormItem>
                  <FormLabel>允许使用的等级 *</FormLabel>
                  <div className="mt-2 grid grid-cols-5 gap-4">
                    {ALL_MEMBERSHIP_TIERS.map((tier) => (
                      <FormField
                        key={tier}
                        control={form.control}
                        name="allowed_tiers"
                        render={({ field }) => (
                          <FormItem className="flex items-center space-x-2 space-y-0">
                            <FormControl>
                              <Checkbox
                                checked={field.value?.includes(tier)}
                                onCheckedChange={(checked) => {
                                  const value = field.value || [];
                                  if (checked) {
                                    field.onChange([...value, tier]);
                                  } else {
                                    field.onChange(value.filter((t) => t !== tier));
                                  }
                                }}
                              />
                            </FormControl>
                            <FormLabel className="cursor-pointer text-sm font-normal">
                              {MEMBERSHIP_TIER_LABELS[tier]}
                            </FormLabel>
                          </FormItem>
                        )}
                      />
                    ))}
                  </div>
                  <FormDescription>勾选可以使用该模型的会员等级</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* 固定计费 */}
            <FormField
              control={form.control}
              name="cost_per_call"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>固定计费（积分/次）*</FormLabel>
                  <FormControl>
                    <Input type="number" min={0} step={0.01} {...field} />
                  </FormControl>
                  <FormDescription>每次调用扣除的基础积分</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Token 计费开关 */}
            <FormField
              control={form.control}
              name="token_cost_enabled"
              render={({ field }) => (
                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                  <div className="space-y-0.5">
                    <FormLabel className="text-base">启用 Token 计费</FormLabel>
                    <FormDescription>
                      开启后将根据输入/输出 Token 数量额外计费
                    </FormDescription>
                  </div>
                  <FormControl>
                    <Switch checked={field.value} onCheckedChange={field.onChange} />
                  </FormControl>
                </FormItem>
              )}
            />

            {/* Token 费率配置 */}
            {tokenCostEnabled && (
              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="token_input_cost"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>输入 Token 费率</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          min={0}
                          step={0.001}
                          placeholder="0.03"
                          {...field}
                        />
                      </FormControl>
                      <FormDescription>积分/千token</FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="token_output_cost"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>输出 Token 费率</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          min={0}
                          step={0.001}
                          placeholder="0.06"
                          {...field}
                        />
                      </FormControl>
                      <FormDescription>积分/千token</FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            )}

            {/* 自定义参数 */}
            <FormField
              control={form.control}
              name="params"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>自定义参数 (JSON)</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder='例如: {"durations":[10,15], "hd_supported": true}'
                      className="font-mono text-xs"
                      rows={4}
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>
                    用于前端渲染的可选参数，必须是有效的 JSON 格式
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* 启用状态 */}
            <FormField
              control={form.control}
              name="is_active"
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

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                取消
              </Button>
              <Button
                type="submit"
                disabled={createMutation.isPending || updateMutation.isPending}
              >
                {createMutation.isPending || updateMutation.isPending
                  ? '保存中...'
                  : mode === 'create'
                    ? '创建配置'
                    : '保存修改'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
