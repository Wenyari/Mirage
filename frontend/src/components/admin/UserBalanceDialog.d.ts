import type { User } from '@/types/user';
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
export declare function UserBalanceDialog({ user, open, onOpenChange, onSubmit, isLoading, }: UserBalanceDialogProps): import("react/jsx-runtime").JSX.Element | null;
export {};
