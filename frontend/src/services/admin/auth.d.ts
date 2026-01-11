import { User } from '@/types/user';
export interface LoginParams {
    email: string;
    password?: string;
    code?: string;
}
export interface LoginResponse {
    token: string;
    user: Omit<User, 'password_hash' | 'register_ip'>;
}
export declare function login(params: LoginParams): Promise<LoginResponse>;
export declare function logout(): Promise<void>;
