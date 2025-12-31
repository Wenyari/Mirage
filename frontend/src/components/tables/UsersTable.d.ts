import type { User, UserLevel, UserListResponse, UserStatus } from '@/types/user';
interface UsersTableProps {
    data: UserListResponse | undefined;
    isLoading: boolean;
    searchValue: string;
    onEdit: (user: User) => void;
    onBalanceEdit: (user: User) => void;
    onStatusChange: (userId: number, status: UserStatus) => void;
    onPageChange: (page: number) => void;
    onLimitChange: (limit: number) => void;
    onSearch: (email: string) => void;
    onClearSearch: () => void;
    onLevelFilter: (level: UserLevel | undefined) => void;
    onStatusFilter: (status: UserStatus | undefined) => void;
}
export declare function UsersTable({ data, isLoading, searchValue, onEdit, onBalanceEdit, onStatusChange, onPageChange, onLimitChange, onSearch, onClearSearch, onLevelFilter, onStatusFilter, }: UsersTableProps): import("react/jsx-runtime").JSX.Element;
export {};
