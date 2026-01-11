type Option = {
    value: string;
    label: string;
};
interface FancyMultiSelectProps {
    selected: string[];
    onChange: (value: string[]) => void;
    options: Option[];
    placeholder?: string;
}
export declare function FancyMultiSelect({ selected, onChange, options, placeholder }: FancyMultiSelectProps): import("react/jsx-runtime").JSX.Element;
export {};
