import type { ApiResponse } from '@/types/api';
export interface UploadResponse {
    url: string;
    key: string;
}
export declare const uploadService: {
    uploadFile: (file: File, type?: string) => Promise<ApiResponse<UploadResponse>>;
    deleteFile: (key: string) => Promise<import("axios").AxiosResponse<ApiResponse<void>, any, {}>>;
};
