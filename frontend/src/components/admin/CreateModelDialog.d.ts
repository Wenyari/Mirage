interface CreateModelDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSuccess?: (modelKey: string) => void;
}
export declare function CreateModelDialog({ open, onOpenChange, onSuccess }: CreateModelDialogProps): import("react/jsx-runtime").JSX.Element;
export {};
