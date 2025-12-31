import type { UserStatus } from '@/types/user';
interface StatusBadgeProps {
    status: UserStatus;
    onChange?: (status: UserStatus) => void;
    disabled?: boolean;
    className?: string;
}
/**
 * 用户状态徽章组件
 * 显示用户状态（正常/封禁），支持切换
 */
export declare function StatusBadge({ status, onChange, disabled, className }: StatusBadgeProps): import("react/jsx-runtime").JSX.Element;
export {};
