import type { LucideIcon } from 'lucide-react';
interface ActivityCardProps {
    title: string;
    description: string;
    icon: LucideIcon;
    points?: number;
    actionText?: string;
    className?: string;
    onClick?: () => void;
    disabled?: boolean;
    variant?: 'default' | 'checkin';
    footer?: React.ReactNode;
    status?: React.ReactNode;
}
export declare function ActivityCard({ title, description, icon: Icon, points, actionText, className, onClick, disabled, variant, footer, status, }: ActivityCardProps): import("react/jsx-runtime").JSX.Element;
export {};
