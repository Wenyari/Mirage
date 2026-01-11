import type { Key } from '@/types/key';
interface KeysTableProps {
    data: Key[];
    onEdit: (key: Key) => void;
}
export declare function KeysTable({ data, onEdit }: KeysTableProps): import("react/jsx-runtime").JSX.Element;
export {};
