import type { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

interface ActivityCardProps {
    title: string;
    description: string;
    icon: LucideIcon;
    points?: number;
    actionText?: string;
    className?: string;
    onClick?: () => void;
    disabled?: boolean;
    variant?: 'default' | 'checkin'; // Specialized variants
    footer?: React.ReactNode; // For extra info like date
    status?: React.ReactNode; // For badges like "Active"
}

export function ActivityCard({
    title,
    description,
    icon: Icon,
    points,
    actionText = "去完成",
    className,
    onClick,
    disabled,
    variant = 'default',
    footer,
    status,
}: ActivityCardProps) {

    // Color configuration based on variant
    const colors = variant === 'checkin' ? {
        bg: "bg-gradient-to-br from-orange-50 to-amber-50 dark:from-orange-950/20 dark:to-amber-950/20",
        curtain: "bg-orange-500",
        curtainLight: "bg-orange-200/50 dark:bg-orange-800/30",
        icon: "text-orange-500",
        text: "text-orange-600 dark:text-orange-400"
    } : {
        bg: "bg-gradient-to-br from-slate-50 to-gray-50 dark:from-slate-950/20 dark:to-gray-950/20",
        curtain: "bg-primary", // mediumturquoise-ish from theme
        curtainLight: "bg-primary/20",
        icon: "text-primary",
        text: "text-primary"
    };

    return (
        <div
            className={cn(
                "group relative h-[320px] w-full overflow-hidden rounded-xl border shadow-sm transition-all hover:shadow-md",
                colors.bg,
                disabled && "opacity-80 cursor-not-allowed",
                className
            )}
            onClick={!disabled ? onClick : undefined}
        >
            {/* --- Initial Content (Visible by default) --- */}
            <div className="relative z-0 flex h-full flex-col p-6 transition-opacity duration-300 group-hover:opacity-20">
                <div className="flex items-start justify-between">
                    <div className={cn("rounded-lg p-3 bg-background/80 backdrop-blur-sm shadow-sm", colors.text)}>
                        <Icon className="size-6" />
                    </div>
                    {status}
                </div>

                <div className="mt-8 flex-1 space-y-2">
                    <h3 className="text-xl font-bold tracking-tight">{title}</h3>
                    <p className="text-sm text-muted-foreground line-clamp-3 leading-relaxed">
                        {description}
                    </p>
                </div>

                {/* Footer positioned at bottom-right */}
                <div className="absolute bottom-6 right-6 text-right">
                    {points !== undefined && (
                        <div className="mb-1 flex items-center justify-end gap-1.5 font-medium">
                            <span className={cn("text-lg font-bold", colors.text)}>{points}</span>
                            <span className="text-xs text-muted-foreground">积分</span>
                        </div>
                    )}
                    <div className="text-xs text-muted-foreground">
                        {footer}
                    </div>
                </div>
            </div>

            {/* --- Curtain Effects (Expand on hover) --- */}

            {/* Top Right Curtain */}
            <div
                className={cn(
                    "absolute top-0 right-0 h-24 w-24 rounded-bl-[100px] transition-all duration-500 ease-in-out z-10",
                    colors.curtainLight,
                    !disabled && "group-hover:h-full group-hover:w-full group-hover:rounded-none group-hover:bg-opacity-100",
                    !disabled && colors.curtain
                )}
            />

            {/* Bottom Left Curtain */}
            <div
                className={cn(
                    "absolute bottom-0 left-0 h-24 w-24 rounded-tr-[100px] transition-all duration-500 ease-in-out z-10",
                    colors.curtainLight,
                    !disabled && "group-hover:h-full group-hover:w-full group-hover:rounded-none group-hover:bg-opacity-100",
                    !disabled && colors.curtain
                )}
            />

            {/* --- Hover Content (Revealed on hover) --- */}
            <div className="absolute inset-0 z-20 flex flex-col items-center justify-center p-6 text-center opacity-0 transition-all duration-500 delay-100 group-hover:opacity-100 pointer-events-none group-hover:pointer-events-auto">
                {!disabled ? (
                    <>
                        <h4 className="mb-2 text-2xl font-bold text-white translate-y-4 transition-transform duration-500 group-hover:translate-y-0">
                            {actionText}
                        </h4>
                        <p className="mb-6 text-white/90 translate-y-4 transition-transform duration-500 delay-75 group-hover:translate-y-0 max-w-[200px] line-clamp-2">
                            {title}
                        </p>
                        <Button
                            size="lg"
                            variant="secondary"
                            className="w-full max-w-[140px] shadow-lg translate-y-4 transition-transform duration-500 delay-100 group-hover:translate-y-0 font-semibold"
                        >
                            立即参与
                        </Button>
                    </>
                ) : (
                    <h4 className="text-xl font-bold text-white/50">
                        {status || "不可用"}
                    </h4>
                )}
            </div>
        </div>
    );
}
