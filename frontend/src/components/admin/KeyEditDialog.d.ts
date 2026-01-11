import type { Key } from '@/types/key';
interface KeyEditDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    keyData: Key | null;
}
export declare function KeyEditDialog({ open, onOpenChange, keyData }: KeyEditDialogProps): import("react/jsx-runtime").JSX.Element | null;
export {};
