import apiClient from '@/api/apiClient';

export interface UploadProgress {
  fileName: string;
  progress: number;
  status: 'pending' | 'uploading' | 'success' | 'error' | 'scanning';
  error?: string;
  uploadedBytes: number;
  totalBytes: number;
  speed?: number;
  estimatedTimeRemaining?: number;
}

export interface UploadResult {
  success: boolean;
  fileName: string;
  fileId?: string;
  message?: string;
  error?: string;
}

const activeUploads = new Map<string, AbortController>();

export async function uploadFile(
  file: File,
  onProgress?: (progress: UploadProgress) => void
): Promise<UploadResult> {
  const controller = new AbortController();
  activeUploads.set(file.name, controller);

  const formData = new FormData();
  formData.append('file', file);
  formData.append('metadata', JSON.stringify({
    originalName: file.name,
    size: file.size,
    type: file.type,
    uploadedAt: new Date().toISOString(),
  }));

  let lastLoaded = 0;
  let lastTime = Date.now();

  try {
    const response = await apiClient.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      signal: controller.signal,
      onUploadProgress: (progressEvent) => {
        if (!progressEvent.total || !onProgress) return;

        const now = Date.now();
        const loaded = progressEvent.loaded;
        const total = progressEvent.total;
        const progress = Math.round((loaded / total) * 100);

        const timeDelta = (now - lastTime) / 1000;
        const bytesDelta = loaded - lastLoaded;
        const speed = timeDelta > 0 ? bytesDelta / timeDelta : 0;

        const remainingBytes = total - loaded;
        const estimatedTimeRemaining = speed > 0 ? remainingBytes / speed : 0;

        lastLoaded = loaded;
        lastTime = now;

        onProgress({
          fileName: file.name,
          progress,
          status: 'uploading',
          uploadedBytes: loaded,
          totalBytes: total,
          speed,
          estimatedTimeRemaining,
        });
      },
    });

    if (onProgress) {
      onProgress({
        fileName: file.name,
        progress: 100,
        status: 'scanning',
        uploadedBytes: file.size,
        totalBytes: file.size,
      });
    }

    return {
      success: true,
      fileName: file.name,
      fileId: response.data.file_id,
      message: response.data.message,
    };
  } catch (error: any) {
    if (error.code === 'ERR_CANCELED') {
      if (onProgress) {
        onProgress({
          fileName: file.name,
          progress: 0,
          status: 'error',
          error: 'Upload cancelled',
          uploadedBytes: 0,
          totalBytes: file.size,
        });
      }
      return { success: false, fileName: file.name, error: 'Upload cancelled' };
    }

    const errorMessage = error.response?.data?.detail || 'Upload failed';

    if (onProgress) {
      onProgress({
        fileName: file.name,
        progress: 0,
        status: 'error',
        error: errorMessage,
        uploadedBytes: 0,
        totalBytes: file.size,
      });
    }

    return { success: false, fileName: file.name, error: errorMessage };
  } finally {
    activeUploads.delete(file.name);
  }
}

export async function uploadBatch(
  files: File[],
  onProgress?: (fileProgress: Map<string, UploadProgress>) => void
): Promise<UploadResult[]> {
  const progressMap = new Map<string, UploadProgress>();

  files.forEach((file) => {
    progressMap.set(file.name, {
      fileName: file.name,
      progress: 0,
      status: 'pending',
      uploadedBytes: 0,
      totalBytes: file.size,
    });
  });

  const results: UploadResult[] = [];
  const concurrentLimit = 3;

  for (let i = 0; i < files.length; i += concurrentLimit) {
    const batch = files.slice(i, i + concurrentLimit);

    const batchResults = await Promise.all(
      batch.map((file) =>
        uploadFile(file, (progress) => {
          progressMap.set(file.name, progress);
          onProgress?.(new Map(progressMap));
        })
      )
    );

    results.push(...batchResults);
  }

  return results;
}

export async function retryUpload(
  file: File,
  onProgress?: (progress: UploadProgress) => void
): Promise<UploadResult> {
  return uploadFile(file, onProgress);
}

export function cancelUpload(fileName: string): void {
  const controller = activeUploads.get(fileName);
  if (controller) {
    controller.abort();
    activeUploads.delete(fileName);
  }
}
