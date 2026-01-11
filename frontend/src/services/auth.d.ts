import { AuthUser } from '@/store/authStore';
import { ApiResponse } from '@/types/api';
export interface SendCodeRequest {
    email: string;
    cf_token: string;
}
export interface RegisterRequest {
    email: string;
    code: string;
    password: string;
}
export interface LoginRequest {
    email: string;
    password: string;
    cf_token: string;
}
export interface RegisterResponse {
    user_id: number;
}
export interface LoginResponse {
    token: string;
    user: AuthUser;
}
export interface MeResponse extends AuthUser {
    vip_desc?: string;
}
export declare const authService: {
    sendCode: (data: SendCodeRequest) => Promise<import("axios").AxiosResponse<ApiResponse<void>, any, {}>>;
    register: (data: RegisterRequest) => Promise<ApiResponse<RegisterResponse>>;
    login: (data: LoginRequest) => Promise<ApiResponse<LoginResponse>>;
    me: () => Promise<any>;
    logout: () => Promise<import("axios").AxiosResponse<ApiResponse<void>, any, {}>>;
};
