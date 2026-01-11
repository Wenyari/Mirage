import type { ModelConfig } from '@/types/modelConfig';
interface ModelConfigDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    mode: 'create' | 'edit';
    config?: ModelConfig;
}
export declare function ModelConfigDialog({ open, onOpenChange, mode, config }: ModelConfigDialogProps): import("react/jsx-runtime").JSX.Element;
export {};
