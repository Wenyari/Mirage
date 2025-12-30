import { zodResolver } from '@hookform/resolvers/zod';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
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
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Textarea } from '@/components/ui/textarea';
import type { User } from '@/types/user';

const formSchema = z.object({
  type: z.enum(['recharge', 'deduct']),
  amount: z.number().min(1, '金额必须大于0').max(100000, '金额不能超过100000'),
  reason: z.string().min(2, '请输入操作原因').max(200, '原因不能超过200字'),
});

type FormValues = z.infer<typeof formSchema>;

interface UserBalanceDialogProps {
  user: User | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (userId: number, amount: number, reason: string) => Promise<void>;
  isLoading?: boolean;
}

/**
 * 用户积分管理对话框
 * 用于人工充值和扣费
 */
export function UserBalanceDialog({
  user,
  open,
  onOpenChange,
  onSubmit,
  isLoading = false,
}: UserBalanceDialogProps) {
  const [submitType, setSubmitType] = useState<'recharge' | 'deduct'>('recharge');

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      type: 'recharge',
      amount: 100,
      reason: '',
    },
  });

  const handleSubmit = async (values: FormValues) => {
    if (!user) return;

    try {
      const finalAmount = values.type === 'deduct' ? -Math.abs(values.amount) : Math.abs(values.amount);
      await onSubmit(user.id, finalAmount, values.reason);
      onOpenChange(false);
      form.reset();
    } catch (error) {
      // 错误处理在父组件中完成
    }
  };

  if (!user) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>积分管理</DialogTitle>
          <DialogDescription>
            为用户 {user.email} 进行积分充值或扣费操作
          </DialogDescription>
        </DialogHeader>
        
        {/* 当前余额显示 */}
        <div className="mb-4 rounded-lg border bg-gray-50 p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-600">当前余额</span>
            <span className="text-2xl font-bold text-blue-600">
              {user.balance.toLocaleString()}
            </span>
          </div>
        </div>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
            {/* 操作类型选择 */}
            <FormField
              control={form.control}
              name="type"
              render={({ field }) => (
                <FormItem className="space-y-3">
                  <FormLabel>操作类型</FormLabel>
                  <FormControl>
                    <RadioGroup
                      onValueChange={(value) => {
                        field.onChange(value);
                        setSubmitType(value as 'recharge' | 'deduct');
                      }}
                      value={field.value}
                      className="flex gap-4"
                    >
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="recharge" id="recharge" />
                        <Label htmlFor="recharge" className="text-green-600">
                          充值
                        </Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="deduct" id="deduct" />
                        <Label htmlFor="deduct" className="text-red-600">
                          扣费
                        </Label>
                      </div>
                    </RadioGroup>
                  </FormControl>
                  <FormDescription>
                    选择充值将增加用户积分，选择扣费将减少用户积分
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* 金额输入 */}
            <FormField
              control={form.control}
              name="amount"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>
                    {submitType === 'recharge' ? '充值金额' : '扣费金额'}
                  </FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      placeholder={`请输入${submitType === 'recharge' ? '充值' : '扣费'}金额`}
                      {...field}
                      onChange={(e) => field.onChange(parseInt(e.target.value) || 0)}
                    />
                  </FormControl>
                  <FormDescription>
                    {submitType === 'recharge' 
                      ? '输入要充值的积分数额' 
                      : '输入要扣除的积分数额，不能超过用户当前余额'
                    }
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* 操作原因 */}
            <FormField
              control={form.control}
              name="reason"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>操作原因</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="请输入操作原因，例如：活动奖励、违规扣费等"
                      className="resize-none"
                      rows={3}
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>
                    请详细说明此次操作的原因，便于后续审计和查询
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* 预览信息 */}
            <div className="rounded-lg border bg-yellow-50 p-4">
              <h4 className="mb-2 text-sm font-medium text-yellow-800">操作预览</h4>
              <div className="space-y-1 text-sm text-yellow-700">
                <div>用户：{user.email}</div>
                <div>类型：{submitType === 'recharge' ? '充值' : '扣费'}</div>
                <div>金额：{form.watch('amount')?.toLocaleString()}</div>
                <div>
                  操作后余额：{
                    submitType === 'recharge' 
                      ? (user.balance + (form.watch('amount') || 0)).toLocaleString()
                      : (user.balance - (form.watch('amount') || 0)).toLocaleString()
                  }
                </div>
              </div>
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={isLoading}
              >
                取消
              </Button>
              <Button 
                type="submit" 
                disabled={isLoading}
                className={submitType === 'recharge' ? 'bg-green-600' : 'bg-red-600'}
              >
                {isLoading 
                  ? '处理中...' 
                  : (submitType === 'recharge' ? '确认充值' : '确认扣费')
                }
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}