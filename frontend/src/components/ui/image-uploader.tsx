import { Loader2, Trash2, Upload } from 'lucide-react';
import { useState } from 'react';
import { toast } from 'sonner';

import { cn } from '@/lib/utils';
import { uploadService } from '@/services/upload';

interface ImageUploaderProps {
  value?: string[];
  onChange: (urls: string[]) => void;
  maxFiles?: number;
  maxSizeMB?: number;
  className?: string;
}

export function ImageUploader({
  value = [],
  onChange,
  maxFiles = 1,
  maxSizeMB = 1,
  className,
}: ImageUploaderProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const processFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;

    // Check file count limit
    if (value.length + files.length > maxFiles) {
      toast.error(`最多只能上传 ${maxFiles} 张图片`);
      return;
    }

    setIsUploading(true);
    const newUrls: string[] = [];

    try {
      for (let i = 0; i < files.length; i++) {
        const file = files[i];

        // Check file type
        if (!file.type.startsWith('image/')) {
          toast.error(`文件 ${file.name} 不是图片格式`);
          continue;
        }

        // Check file size
        if (file.size > maxSizeMB * 1024 * 1024) {
          toast.error(`文件 ${file.name} 超过 ${maxSizeMB}MB 限制`);
          continue;
        }

        // Upload
        const res: any = await uploadService.uploadFile(file);
        // Handle different response structures (unwrapped vs wrapped)
        const url = res?.data?.url || res?.url;

        if (url) {
          newUrls.push(url);
        } else {
          toast.error(`文件 ${file.name} 上传失败`);
        }
      }

      if (newUrls.length > 0) {
        onChange([...value, ...newUrls]);
        toast.success(`成功上传 ${newUrls.length} 张图片`);
      }
    } catch (error: any) {
      console.error('Upload failed:', error);
      toast.error((error.data ? error.data.msg : error.message) || '上传失败');
    } finally {
      setIsUploading(false);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    await processFiles(e.target.files);
    // Reset input value to allow selecting same file again
    e.target.value = '';
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    // 只有当离开整个上传区域时才设置为false
    if (e.currentTarget === e.target) {
      setIsDragging(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (isUploading) return;

    const files = e.dataTransfer.files;
    await processFiles(files);
  };

  const handleRemove = async (index: number) => {
    const url = value[index];

    try {
      // 从URL中解析出object_key
      const parsed = new URL(url);
      const objectKey = parsed.pathname.substring(1); // 去掉开头的 '/'

      // 调用后端删除接口
      await uploadService.deleteFile(objectKey);

      // 从本地状态中删除
      const newUrls = [...value];
      newUrls.splice(index, 1);
      onChange(newUrls);

      toast.success('图片已删除');
    } catch (error: any) {
      console.error('Delete failed:', error);
      toast.error(error.message || '删除失败');
    }
  };

  return (
    <div className={cn("space-y-3", className)}>
      {/* File List */}
      {value.length > 0 && (
        <div className={cn("grid gap-3", maxFiles > 1 ? "grid-cols-2" : "grid-cols-1")}>
          {value.map((url, index) => (
            <div key={index} className="relative group aspect-video overflow-hidden rounded-lg border bg-muted">
              <img src={url} alt={`Uploaded ${index + 1}`} className="h-full w-full object-cover" />
              <button
                onClick={() => handleRemove(index)}
                className="absolute right-1 top-1 rounded-full bg-black/50 p-1 text-white opacity-0 transition-opacity hover:bg-red-500 group-hover:opacity-100"
              >
                <Trash2 className="size-3" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Upload Area */}
      {value.length < maxFiles && (
        <label
          className={cn(
            "flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-muted-foreground/25 bg-muted/5 p-4 text-center transition-colors hover:bg-muted/20",
            isUploading && "cursor-not-allowed opacity-50",
            isDragging && "border-primary bg-primary/10"
          )}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          <input
            type="file"
            className="hidden"
            accept="image/*"
            multiple={maxFiles > 1}
            onChange={handleFileChange}
            disabled={isUploading}
          />
          {isUploading ? (
            <Loader2 className="mb-2 size-6 animate-spin text-muted-foreground" />
          ) : (
            <Upload className="mb-2 size-6 text-muted-foreground" />
          )}
          <span className="text-xs text-muted-foreground">
            {isUploading ? "上传中..." : "点击或拖拽上传"}
          </span>
        </label>
      )}
    </div>
  );
}
