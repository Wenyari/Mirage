import { Badge } from '@/components/ui/badge';
import type { UserLevel } from '@/types/user';
import { LEVEL_COLORS,USER_LEVEL_LABELS } from '@/types/user';

interface LevelBadgeProps {
  level: UserLevel;
  className?: string;
}

/**
 * 用户等级徽章组件
 * 显示T1-T5等级，使用不同颜色区分
 */
export function LevelBadge({ level, className }: LevelBadgeProps) {
  const label = USER_LEVEL_LABELS[level];
  const colorClass = LEVEL_COLORS[level];
  
  return (
    <Badge 
      variant="secondary" 
      className={`${colorClass} border-0 font-medium ${className || ''}`}
    >
      {label}
    </Badge>
  );
}