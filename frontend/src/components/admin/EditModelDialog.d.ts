import type { Model } from '@/types/key';
interface EditModelDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    model?: Model;
}
export declare function EditModelDialog({ open, onOpenChange, model }: EditModelDialogProps): import("react/jsx-runtime").JSX.Element;
export {};
