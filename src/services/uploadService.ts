/**
 * Document Upload Service
 * 
 * Manages file upload communication with backend API including
 * progress tracking, error handling, and retry logic.
 */
import apiClient from '@/api/apiClient';

export interface UploadProgress {
  fileName: string;
  progress: number; // 0-100
  status: 'pending' | 'uploading' | 'success' | 'error' | 'scanning';
  error?: string;
  uploadedBytes: number;
  totalBytes: number;
  speed?: number; // bytes/second
  estimatedTimeRemaining?: number; // seconds
}

export interface UploadResult {
  success: boolean;
  fileName: string;
  fileId?: string;
  message?: string;
  error?: string;
}

/**
 * Upload single file with progress tracking
 */
export async function uploadFile(
  file: File,
  onProgress?: (progress: UploadProgress) => void
): Promise<UploadResult> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('metadata', JSON.stringify({
    originalName: file.name,
    size: file.size,
    type: file.type,
    uploadedAt: new Date().toISOString(),
  }));
  
  let startTime = Date.now();
  let lastLoaded = 0;
  let lastTime = startTime;
  
  try {
    const response = await apiClient.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (!progressEvent.total || !onProgress) return;
        
        const now = Date.now();
        const loaded = progressEvent.loaded;
        const total = progressEvent.total;
        const progress = Math.round((loaded / total) * 100);
        
        // Calculate speed and ETA
        const timeDelta = (now - lastTime) / 1000; // seconds
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
    
    // Upload complete - now scanning
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
    
    return {
      success: false,
      fileName: file.name,
      error: errorMessage,
    };
  }
}

/**
 * Upload multiple files (batch)
 */
export async function uploadBatch(
  files: File[],
  onProgress?: (fileProgress: Map<string, UploadProgress>) => void
): Promise<UploadResult[]> {
  const progressMap = new Map<string, UploadProgress>();
  
  // Initialize progress for all files
  files.forEach((file) => {
    progressMap.set(file.name, {
      fileName: file.name,
      progress: 0,
      status: 'pending',
      uploadedBytes: 0,
      totalBytes: file.size,
    });
  });
  
  // Upload files in parallel (max 3 concurrent)
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

/**
 * Retry failed upload
 */
export async function retryUpload(
  file: File,
  onProgress?: (progress: UploadProgress) => void
): Promise<UploadResult> {
  return uploadFile(file, onProgress);
}

/**
 * Cancel ongoing upload (placeholder)
 */
export function cancelUpload(fileName: string): void {
  // In production, would use AbortController
  console.log(`Cancelling upload for ${fileName}`);
}

