import type { UserLevel } from '@/types/user';
interface LevelBadgeProps {
    level: UserLevel;
    className?: string;
}
/**
 * 用户等级徽章组件
 * 显示T1-T5等级，使用不同颜色区分
 */
export declare function LevelBadge({ level, className }: LevelBadgeProps): import("react/jsx-runtime").JSX.Element;
export {};
