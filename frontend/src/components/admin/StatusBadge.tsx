import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import type { UserStatus } from '@/types/user';
import { USER_STATUS_LABELS } from '@/types/user';

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
export function StatusBadge({ status, onChange, disabled, className }: StatusBadgeProps) {
  const label = USER_STATUS_LABELS[status];
  const isActive = status === 1;
  
  if (onChange) {
    return (
      <div className={`flex items-center gap-2 ${className || ''}`}>
        <Switch
          checked={isActive}
          onCheckedChange={(checked) => onChange(checked ? 1 : 0)}
          disabled={disabled}
        />
        <span className={`text-sm ${isActive ? 'text-green-600' : 'text-red-600'}`}>
          {label}
        </span>
      </div>
    );
  }
  
  return (
    <Badge 
      variant={isActive ? "default" : "destructive"}
      className={className}
    >
      {label}
    </Badge>
  );
}