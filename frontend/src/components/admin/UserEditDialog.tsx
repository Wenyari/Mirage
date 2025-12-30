import { zodResolver } from '@hookform/resolvers/zod';
import { useEffect,useState } from 'react';
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import type { User, UserLevel, UserStatus } from '@/types/user';
import { USER_LEVEL_LABELS, USER_STATUS_LABELS } from '@/types/user';

const formSchema = z.object({
  level: z.number().min(1).max(5),
  status: z.number().min(0).max(1),
});

type FormValues = z.infer<typeof formSchema>;

interface UserEditDialogProps {
  user: User | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (userId: number, data: { level?: UserLevel; status?: UserStatus }) => Promise<void>;
  isLoading?: boolean;
}

/**
 * 用户编辑对话框
 * 用于修改用户等级和状态
 */
export function UserEditDialog({
  user,
  open,
  onOpenChange,
  onSubmit,
  isLoading = false,
}: UserEditDialogProps) {
  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      level: 1,
      status: 1,
    },
  });

  // 当用户数据变化时更新表单
  useEffect(() => {
    if (user) {
      form.reset({
        level: user.level,
        status: user.status,
      });
    }
  }, [user, form]);

  const handleSubmit = async (values: FormValues) => {
    if (!user) return;

    try {
      await onSubmit(user.id, {
        level: values.level as UserLevel,
        status: values.status as UserStatus,
      });
      onOpenChange(false);
    } catch (error) {
      // 错误处理在父组件中完成
    }
  };

  if (!user) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>编辑用户资料</DialogTitle>
          <DialogDescription>
            修改用户 {user.email} 的等级和状态信息
          </DialogDescription>
        </DialogHeader>
        
        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="level"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>会员等级</FormLabel>
                  <Select
                    onValueChange={(value) => field.onChange(parseInt(value))}
                    value={field.value.toString()}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="选择用户等级" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {Object.entries(USER_LEVEL_LABELS).map(([level, label]) => (
                        <SelectItem key={level} value={level}>
                          {label} - {getLevelDescription(parseInt(level) as UserLevel)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormDescription>
                    用户等级决定了可用的功能和权限
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="status"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>账号状态</FormLabel>
                  <Select
                    onValueChange={(value) => field.onChange(parseInt(value))}
                    value={field.value.toString()}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="选择账号状态" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="1">
                        正常 - 用户可以正常使用
                      </SelectItem>
                      <SelectItem value="0">
                        封禁 - 用户无法登录和使用
                      </SelectItem>
                    </SelectContent>
                  </Select>
                  <FormDescription>
                    封禁状态的用户将无法登录系统
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={isLoading}
              >
                取消
              </Button>
              <Button type="submit" disabled={isLoading}>
                {isLoading ? '保存中...' : '保存修改'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}

/**
 * 获取等级描述
 */
function getLevelDescription(level: UserLevel): string {
  const descriptions = {
    1: '基础用户',
    2: '初级用户', 
    3: '中级用户',
    4: '高级用户',
    5: '顶级用户'
  };
  return descriptions[level];
}