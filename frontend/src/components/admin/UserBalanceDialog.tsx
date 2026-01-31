import { zodResolver } from '@hookform/resolvers/zod';
import { useEffect, useState } from 'react';
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
  balance_type: z.enum(['recharge', 'activity']),
  amount: z.number().min(1, '金额必须大于0').max(100000, '金额不能超过100000'),
  reason: z.string().min(2, '请输入操作原因').max(200, '原因不能超过200字'),
});

type FormValues = z.infer<typeof formSchema>;

interface UserBalanceDialogProps {
  user: User | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (userId: number, amount: number, reason: string, balance_type: 'recharge' | 'activity') => Promise<void>;
  isLoading?: boolean;
}

/**
 * 用户积分管理对话框
 * 用于人工充值和扣费（支持活动积分和充值积分）
 */
export function UserBalanceDialog({
  user,
  open,
  onOpenChange,
  onSubmit,
  isLoading = false,
}: UserBalanceDialogProps) {
  const [submitType, setSubmitType] = useState<'recharge' | 'deduct'>('recharge');
  const [balanceType, setBalanceType] = useState<'recharge' | 'activity'>('recharge');

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      type: 'recharge',
      balance_type: 'recharge',
      amount: 100,
      reason: '',
    },
  });

  // 当用户或对话框打开状态变化时，重置表单
  useEffect(() => {
    if (open) {
      form.reset({
        type: 'recharge',
        balance_type: 'recharge',
        amount: 100,
        reason: '',
      });
      setSubmitType('recharge');
      setBalanceType('recharge');
    }
  }, [open, form]);

  const handleSubmit = async (values: FormValues) => {
    if (!user) return;

    try {
      const finalAmount = values.type === 'deduct' ? -Math.abs(values.amount) : Math.abs(values.amount);
      await onSubmit(user.id, finalAmount, values.reason, values.balance_type);
      onOpenChange(false);
      form.reset();
    } catch (error) {
      // 错误处理在父组件中完成
    }
  };

  if (!user) return null;

  // 获取当前选定类型的余额
  const currentBalance = balanceType === 'recharge' ? user.recharge_balance : user.activity_balance;

  // 计算操作后的余额
  const amount = form.watch('amount') || 0;
  const newBalance = submitType === 'recharge'
    ? currentBalance + amount
    : currentBalance - amount;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>积分管理</DialogTitle>
          <DialogDescription>
            为用户 {user.email} 进行积分管理
          </DialogDescription>
        </DialogHeader>

        {/* 当前余额显示 */}
        <div className="mb-4 grid grid-cols-2 gap-4">
          <div className={`rounded-lg border p-3 ${balanceType === 'recharge' ? 'bg-blue-50 border-blue-200' : 'bg-gray-50'}`}>
            <div className="text-sm font-medium text-gray-600">充值积分余额</div>
            <div className="text-xl font-bold text-blue-600">
              {user.recharge_balance.toLocaleString()}
            </div>
          </div>
          <div className={`rounded-lg border p-3 ${balanceType === 'activity' ? 'bg-purple-50 border-purple-200' : 'bg-gray-50'}`}>
            <div className="text-sm font-medium text-gray-600">活动积分余额</div>
            <div className="text-xl font-bold text-purple-600">
              {user.activity_balance.toLocaleString()}
            </div>
          </div>
        </div>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              {/* 积分类型选择 */}
              <FormField
                control={form.control}
                name="balance_type"
                render={({ field }) => (
                  <FormItem className="space-y-3">
                    <FormLabel>积分类型</FormLabel>
                    <FormControl>
                      <RadioGroup
                        onValueChange={(value) => {
                          field.onChange(value);
                          setBalanceType(value as 'recharge' | 'activity');
                        }}
                        value={field.value}
                        className="flex flex-col gap-2"
                      >
                        <div className="flex items-center space-x-2">
                          <RadioGroupItem value="recharge" id="type_recharge" />
                          <Label htmlFor="type_recharge">充值积分</Label>
                        </div>
                        <div className="flex items-center space-x-2">
                          <RadioGroupItem value="activity" id="type_activity" />
                          <Label htmlFor="type_activity">活动积分</Label>
                        </div>
                      </RadioGroup>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

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
                        className="flex flex-col gap-2"
                      >
                        <div className="flex items-center space-x-2">
                          <RadioGroupItem value="recharge" id="op_recharge" />
                          <Label htmlFor="op_recharge" className="text-green-600">
                            充值
                          </Label>
                        </div>
                        <div className="flex items-center space-x-2">
                          <RadioGroupItem value="deduct" id="op_deduct" />
                          <Label htmlFor="op_deduct" className="text-red-600">
                            扣费
                          </Label>
                        </div>
                      </RadioGroup>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

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
                      rows={2}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* 预览信息 */}
            <div className="rounded-lg border bg-yellow-50 p-3 text-sm text-yellow-800">
              <div className="flex justify-between">
                <span>预计变更后{balanceType === 'recharge' ? '充值' : '活动'}余额:</span>
                <span className="font-bold">{newBalance.toLocaleString()}</span>
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