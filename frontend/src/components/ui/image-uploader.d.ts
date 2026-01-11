interface ImageUploaderProps {
    value?: string[];
    onChange: (urls: string[]) => void;
    maxFiles?: number;
    maxSizeMB?: number;
    className?: string;
}
export declare function ImageUploader({ value, onChange, maxFiles, maxSizeMB, className, }: ImageUploaderProps): import("react/jsx-runtime").JSX.Element;
export {};
