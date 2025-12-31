export type UserLevel = 1 | 2 | 3 | 4 | 5;
export type UserStatus = 0 | 1;
export type UserRole = 'user' | 'admin';
export interface User {
    id: number;
    email: string;
    password_hash: string;
    balance: number;
    level: UserLevel;
    role: UserRole;
    status: UserStatus;
    register_ip: string;
    last_login_at: string;
    created_at: string;
}
export interface UserListParams {
    page?: number;
    limit?: number;
    email?: string;
    level?: UserLevel;
    status?: UserStatus;
}
export interface UserListResponse {
    items: User[];
    total: number;
    page: number;
    limit: number;
}
export interface UpdateBalanceRequest {
    amount: number;
    reason: string;
}
export interface UpdateProfileRequest {
    level?: UserLevel;
    status?: UserStatus;
}
export declare const USER_STATUS_LABELS: {
    readonly 0: "封禁";
    readonly 1: "正常";
};
export declare const USER_ROLE_LABELS: {
    readonly user: "普通用户";
    readonly admin: "管理员";
};
export declare const USER_LEVEL_LABELS: {
    readonly 1: "T1";
    readonly 2: "T2";
    readonly 3: "T3";
    readonly 4: "T4";
    readonly 5: "T5";
};
export declare const LEVEL_COLORS: {
    readonly 1: "bg-gray-100 text-gray-800";
    readonly 2: "bg-blue-100 text-blue-800";
    readonly 3: "bg-green-100 text-green-800";
    readonly 4: "bg-orange-100 text-orange-800";
    readonly 5: "bg-purple-100 text-purple-800";
};
export interface UserDetails {
    user: User;
    recent_transactions: Transaction[];
    recent_tasks: Task[];
}
export interface Transaction {
    id: number;
    type: 'recharge' | 'consume' | 'refund';
    amount: number;
    reason: string;
    created_at: string;
}
export interface Task {
    id: number;
    model: string;
    prompt: string;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    token_used: number;
    created_at: string;
}
