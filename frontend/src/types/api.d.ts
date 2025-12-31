export interface ApiResponse<T = unknown> {
    code: number;
    message: string;
    data: T;
}
export interface PaginationParams {
    page?: number;
    limit?: number;
}
export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    limit: number;
}
