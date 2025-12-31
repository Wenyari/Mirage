import type { CDK, CDKStatus, CDKType } from '@/types/cdk';
interface CDKTableProps {
    data: CDK[];
    total: number;
    page: number;
    pageSize: number;
    onPageChange: (page: number) => void;
    onPageSizeChange: (pageSize: number) => void;
    onTypeChange: (type: CDKType | 'all') => void;
    onStatusChange: (status: CDKStatus | 'all') => void;
    onSearch: (search: string) => void;
}
export declare function CDKTable({ data, total, page, pageSize, onPageChange, onPageSizeChange, onTypeChange, onStatusChange, onSearch, }: CDKTableProps): import("react/jsx-runtime").JSX.Element;
export {};
