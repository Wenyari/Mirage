import api from '@/lib/api';
import type { ApiResponse } from '@/types/api';

export interface UploadResponse {
  url: string;
  key: string;
}

export const uploadService = {
  uploadFile: async (file: File, type: string = 'image') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('type', type);

    const response = await api.post<ApiResponse<UploadResponse>>('/upload/file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  deleteFile: async (key: string) => {
    return api.delete<ApiResponse<void>>(`/upload/delete/${encodeURIComponent(key)}`);
  }
};
