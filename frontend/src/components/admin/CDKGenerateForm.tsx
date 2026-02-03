import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { toast } from 'sonner';

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
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
import { Button } from '@/components/ui/button';
import { useGenerateCDK } from '@/hooks/useCDK';
import { exportCDKCodesToExcel } from '@/utils/export';

// 表单验证 Schema
const formSchema = z.object({
  points: z.coerce.number().min(1, '积分面额必须大于0').max(1000000, '积分面额不能超过1000000'),
  type: z.enum(['once', 'universal'], {
    required_error: '请选择CDK类型',
  }),
  grant_level: z.coerce.number().optional(),
  count: z.coerce.number().min(1, '生成数量必须大于0').max(1000, '单次最多生成1000个'),
  batch_no: z.string().optional(),
  expire_at: z.string().optional(),
  valid_days: z.coerce.number().min(0, '积分有效期不能小于0').optional(),
});

type FormValues = z.infer<typeof formSchema>;

export function CDKGenerateForm() {
  const [isGenerating, setIsGenerating] = useState(false);
  const generateMutation = useGenerateCDK();

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      points: 100,
      type: 'once',
      grant_level: undefined,
      count: 10,
      batch_no: '',
      expire_at: '',
      valid_days: undefined,
    },
  });

  const onSubmit = async (values: FormValues) => {
    setIsGenerating(true);
    try {
      const result = await generateMutation.mutateAsync(values);

      if (result.code === 0) {
        toast.success(`成功生成 ${values.count} 个CDK兑换码`);

        // 自动下载 Excel
        exportCDKCodesToExcel(
          result.data.cdks.map(c => c.code), // 适配新的数据结构
          result.data.batch_no,
          values.points,
          `cdk-${result.data.batch_no}`
        );

        // 重置表单
        form.reset({
          points: values.points,
          type: values.type,
          count: 10,
          batch_no: '',
          expire_at: '',
          valid_days: undefined,
        });
      }
    } catch (error: any) {
      toast.error(error.message || '生成CDK失败');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <Card>
      <CardHeader className="flex items-center justify-between">
        <div>
          <CardTitle>生成 CDK 兑换码</CardTitle>
          <CardDescription>
            批量生成兑换码，生成后自动下载 Excel 文件
          </CardDescription>
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" size="sm" onClick={() => { form.setValue('points', 1000); form.setValue('grant_level', 2); }}>9.9 体验包（一个月）</Button>
          <Button variant="ghost" size="sm" onClick={() => { form.setValue('points', 3150); form.setValue('grant_level', 2); }}>29.9 Pro体验包（一个月）</Button>
          <Button variant="ghost" size="sm" onClick={() => { form.setValue('points', 5500); form.setValue('grant_level', 3); }}>49.9 标准包（三个月）</Button>
          <Button variant="ghost" size="sm" onClick={() => { form.setValue('points', 24000); form.setValue('grant_level', 4); }}>199 专业包（半年）</Button>
        </div>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* 积分面额 */}
              <FormField
                control={form.control}
                name="points"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>积分面额 *</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        placeholder="请输入积分面额"
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>单个CDK的积分价值</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* CDK 类型 */}
              <FormField
                control={form.control}
                name="type"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>CDK 类型 *</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      defaultValue={field.value}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="选择CDK类型" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="once">一次性</SelectItem>
                        <SelectItem value="universal">通用码</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormDescription>
                      一次性：单个用户只能使用一次；通用码：多个用户可使用
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* 授予等级（可选） */}
              <FormField
                control={form.control}
                name="grant_level"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>授予等级 (可选)</FormLabel>
                    <FormControl>
                      <Select
                        onValueChange={(v) => field.onChange(Number(v))}
                        value={field.value ? String(field.value) : undefined}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="不授予等级" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="1">T1</SelectItem>
                          <SelectItem value="2">T2</SelectItem>
                          <SelectItem value="3">T3</SelectItem>
                          <SelectItem value="4">T4</SelectItem>
                          <SelectItem value="5">T5</SelectItem>
                        </SelectContent>
                      </Select>
                    </FormControl>
                    <FormDescription>兑换该 CDK 后将把用户等级提升到此等级（如果当前等级低于此值）</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* 生成数量 */}
              <FormField
                control={form.control}
                name="count"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>生成数量 *</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        placeholder="请输入生成数量"
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>单次最多生成 1000 个</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* 批次号（可选） */}
              <FormField
                control={form.control}
                name="batch_no"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>批次号（可选）</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="留空自动生成"
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>用于批量管理，留空自动生成</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* 积分有效期 */}
              <FormField
                control={form.control}
                name="valid_days"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>积分时效 (天)</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        placeholder="留空表示永久有效"
                        {...field}
                        value={field.value || ''}
                      />
                    </FormControl>
                    <FormDescription>充值后积分的有效天数，留空则积分永久有效</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <Button
              type="submit"
              disabled={isGenerating}
              className="w-full md:w-auto"
            >
              {isGenerating ? '生成中...' : '生成 CDK'}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
