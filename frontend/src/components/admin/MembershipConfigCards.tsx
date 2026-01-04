import { zodResolver } from '@hookform/resolvers/zod';
import { Save } from 'lucide-react';
import { AlertCircle } from 'lucide-react';
import { useEffect,useState } from 'react';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';
import * as z from 'zod';

import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
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
import { Skeleton } from '@/components/ui/skeleton';
import { Slider } from '@/components/ui/slider';
import { useMembershipConfigs, useUpdateMembershipConfigs } from '@/hooks/useModelConfigs';
import type { MembershipConfigs, MembershipTier } from '@/types/modelConfig';
import { ALL_MEMBERSHIP_TIERS, MEMBERSHIP_TIER_LABELS } from '@/types/modelConfig';

// 表单 Schema
const formSchema = z.object({
  T1: z.object({
    concurrent_limit: z.coerce.number().min(1).max(100),
    queue_weight: z.coerce.number().min(1).max(10),
    price: z.coerce.number().min(0),
  }),
  T2: z.object({
    concurrent_limit: z.coerce.number().min(1).max(100),
    queue_weight: z.coerce.number().min(1).max(10),
    price: z.coerce.number().min(0),
  }),
  T3: z.object({
    concurrent_limit: z.coerce.number().min(1).max(100),
    queue_weight: z.coerce.number().min(1).max(10),
    price: z.coerce.number().min(0),
  }),
  T4: z.object({
    concurrent_limit: z.coerce.number().min(1).max(100),
    queue_weight: z.coerce.number().min(1).max(10),
    price: z.coerce.number().min(0),
  }),
  T5: z.object({
    concurrent_limit: z.coerce.number().min(1).max(100),
    queue_weight: z.coerce.number().min(1).max(10),
    price: z.coerce.number().min(0),
  }),
});

type FormValues = z.infer<typeof formSchema>;

export function MembershipConfigCards() {
  const [editingTier, setEditingTier] = useState<MembershipTier | null>(null);

  const { data, isLoading, isError, error } = useMembershipConfigs();
  const updateMutation = useUpdateMembershipConfigs();

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      T1: { concurrent_limit: 1, queue_weight: 1, price: 0 },
      T2: { concurrent_limit: 3, queue_weight: 2, price: 29 },
      T3: { concurrent_limit: 5, queue_weight: 3, price: 99 },
      T4: { concurrent_limit: 10, queue_weight: 4, price: 299 },
      T5: { concurrent_limit: 20, queue_weight: 5, price: 999 },
    },
  });

  // 数据加载后更新表单
  useEffect(() => {
    if (data?.data) {
      form.reset({
        T1: {
          concurrent_limit: data.data.T1.concurrent_limit,
          queue_weight: data.data.T1.queue_weight,
          price: data.data.T1.price,
        },
        T2: {
          concurrent_limit: data.data.T2.concurrent_limit,
          queue_weight: data.data.T2.queue_weight,
          price: data.data.T2.price,
        },
        T3: {
          concurrent_limit: data.data.T3.concurrent_limit,
          queue_weight: data.data.T3.queue_weight,
          price: data.data.T3.price,
        },
        T4: {
          concurrent_limit: data.data.T4.concurrent_limit,
          queue_weight: data.data.T4.queue_weight,
          price: data.data.T4.price,
        },
        T5: {
          concurrent_limit: data.data.T5.concurrent_limit,
          queue_weight: data.data.T5.queue_weight,
          price: data.data.T5.price,
        },
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  const onSubmit = async (values: FormValues) => {
    try {
      const updatedConfigs: MembershipConfigs = {
        T1: {
          level: 1,
          name: 'T1',
          ...values.T1,
          description: data?.data.T1.description || '免费用户',
        },
        T2: {
          level: 2,
          name: 'T2',
          ...values.T2,
          description: data?.data.T2.description || '基础会员',
        },
        T3: {
          level: 3,
          name: 'T3',
          ...values.T3,
          description: data?.data.T3.description || '高级会员',
        },
        T4: {
          level: 4,
          name: 'T4',
          ...values.T4,
          description: data?.data.T4.description || '专业会员',
        },
        T5: {
          level: 5,
          name: 'T5',
          ...values.T5,
          description: data?.data.T5.description || '旗舰会员',
        },
      };

      await updateMutation.mutateAsync(updatedConfigs);
      toast.success('会员等级配置已更新');
      setEditingTier(null);
    } catch (err: any) {
      toast.error(err.message || '更新失败');
    }
  };

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {ALL_MEMBERSHIP_TIERS.map((tier) => (
          <Skeleton key={tier} className="h-80" />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="size-4" />
        <AlertDescription>{(error as any)?.message || '加载失败'}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* 标题和保存按钮 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold">会员等级配置</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            配置各等级的并发限制、队列权重和价格
          </p>
        </div>
        <Button
          onClick={form.handleSubmit(onSubmit)}
          disabled={!form.formState.isDirty || updateMutation.isPending}
        >
          <Save className="mr-2 size-4" />
          {updateMutation.isPending ? '保存中...' : '保存所有修改'}
        </Button>
      </div>

      {/* 等级配置卡片 */}
      <Form {...form}>
        <form className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
          {ALL_MEMBERSHIP_TIERS.map((tier) => {
            const tierConfig = data?.data[tier];
            if (!tierConfig) return null;

            return (
              <Card key={tier} className="relative">
                <CardHeader>
                  <CardTitle className="text-lg">{MEMBERSHIP_TIER_LABELS[tier]}</CardTitle>
                  <CardDescription>{tierConfig.description}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* 并发限制 */}
                  <FormField
                    control={form.control}
                    name={`${tier}.concurrent_limit`}
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="text-sm">并发限制</FormLabel>
                        <FormControl>
                          <div className="space-y-2">
                            <Slider
                              min={1}
                              max={20}
                              step={1}
                              value={[field.value]}
                              onValueChange={(v) => {
                                field.onChange(v[0]);
                                setEditingTier(tier);
                              }}
                            />
                            <div className="flex justify-between text-xs text-muted-foreground">
                              <span>1</span>
                              <span className="font-semibold text-foreground">{field.value}</span>
                              <span>20</span>
                            </div>
                          </div>
                        </FormControl>
                        <FormDescription className="text-xs">
                          同时运行任务数
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {/* 队列权重 */}
                  <FormField
                    control={form.control}
                    name={`${tier}.queue_weight`}
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="text-sm">队列权重</FormLabel>
                        <FormControl>
                          <div className="space-y-2">
                            <Slider
                              min={1}
                              max={10}
                              step={1}
                              value={[field.value]}
                              onValueChange={(v) => {
                                field.onChange(v[0]);
                                setEditingTier(tier);
                              }}
                            />
                            <div className="flex justify-between text-xs text-muted-foreground">
                              <span>1</span>
                              <span className="font-semibold text-foreground">{field.value}</span>
                              <span>10</span>
                            </div>
                          </div>
                        </FormControl>
                        <FormDescription className="text-xs">
                          优先级权重
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {/* 价格 */}
                  <FormField
                    control={form.control}
                    name={`${tier}.price`}
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="text-sm">价格（元/月）</FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            min={0}
                            step={1}
                            {...field}
                            onChange={(e) => {
                              field.onChange(e);
                              setEditingTier(tier);
                            }}
                          />
                        </FormControl>
                        <FormDescription className="text-xs">
                          {field.value === 0 ? '免费' : `¥${field.value}/月`}
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </CardContent>
              </Card>
            );
          })}
        </form>
      </Form>
    </div>
  );
}
