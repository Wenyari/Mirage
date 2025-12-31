import type { User, UserLevel, UserStatus } from '@/types/user';
interface UserEditDialogProps {
    user: User | null;
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSubmit: (userId: number, data: {
        level?: UserLevel;
        status?: UserStatus;
    }) => Promise<void>;
    isLoading?: boolean;
}
/**
 * 用户编辑对话框
 * 用于修改用户等级和状态
 */
export declare function UserEditDialog({ user, open, onOpenChange, onSubmit, isLoading, }: UserEditDialogProps): import("react/jsx-runtime").JSX.Element | null;
export {};
