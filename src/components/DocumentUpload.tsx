/**
 * Document Upload Component
 * 
 * Provides drag-and-drop file upload interface with:
 * - Real-time validation
 * - Progress tracking
 * - Batch upload support
 * - Security scanning status
 * - WCAG 2.1 AA accessibility
 */
import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Button } from '@/components/ui/button';
import { validateBatch, formatFileSize, ValidationResult } from '@/utils/fileValidation';
import { uploadBatch, UploadProgress, UploadResult, retryUpload } from '@/services/uploadService';
import {
  Upload,
  File,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Shield,
  Loader2,
  X,
} from 'lucide-react';

interface FileUploadState {
  file: File;
  validation: ValidationResult;
  progress: UploadProgress | null;
  result: UploadResult | null;
}

export default function DocumentUpload() {
  const [files, setFiles] = useState<FileUploadState[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    // Validate batch
    const validation = validateBatch(acceptedFiles);
    
    // Create file upload states
    const newFiles: FileUploadState[] = acceptedFiles.map((file) => ({
      file,
      validation: validation.fileResults.get(file.name) || {
        isValid: false,
        errors: ['Validation failed'],
        warnings: [],
      },
      progress: null,
      result: null,
    }));
    
    setFiles((prev) => [...prev, ...newFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: true,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
      'text/csv': ['.csv'],
    },
  });

  const handleUpload = async () => {
    // Filter valid files
    const validFiles = files.filter((f) => f.validation.isValid && !f.result?.success);
    
    if (validFiles.length === 0) {
      return;
    }
    
    setIsUploading(true);
    
    // Upload files
    const results = await uploadBatch(
      validFiles.map((f) => f.file),
      (progressMap) => {
        // Update progress for each file
        setFiles((prev) =>
          prev.map((fileState) => {
            const progress = progressMap.get(fileState.file.name);
            return progress ? { ...fileState, progress } : fileState;
          })
        );
      }
    );
    
    // Update results
    setFiles((prev) =>
      prev.map((fileState) => {
        const result = results.find((r) => r.fileName === fileState.file.name);
        return result ? { ...fileState, result } : fileState;
      })
    );
    
    setIsUploading(false);
  };

  const removeFile = (fileName: string) => {
    setFiles((prev) => prev.filter((f) => f.file.name !== fileName));
  };

  const retryFile = async (fileName: string) => {
    const fileState = files.find((f) => f.file.name === fileName);
    if (!fileState) return;
    
    const result = await retryUpload(fileState.file, (progress) => {
      setFiles((prev) =>
        prev.map((f) =>
          f.file.name === fileName ? { ...f, progress } : f
        )
      );
    });
    
    setFiles((prev) =>
      prev.map((f) =>
        f.file.name === fileName ? { ...f, result } : f
      )
    );
  };

  const clearAll = () => {
    setFiles([]);
  };

  const validFilesCount = files.filter((f) => f.validation.isValid).length;
  const totalSize = files.reduce((sum, f) => sum + f.file.size, 0);

  return (
    <div className="space-y-6" role="region" aria-label="Document upload interface">
      {/* Drop Zone */}
      <div
        {...getRootProps()}
        className={`cursor-pointer rounded-lg border-2 border-dashed p-12 text-center transition-colors ${
          isDragActive
            ? 'border-primary bg-primary/10'
            : 'border-muted-foreground/25 hover:border-primary/50'
        }`}
        role="button"
        tabIndex={0}
        aria-label="Drag and drop files here or click to select files"
      >
        <input {...getInputProps()} aria-label="File upload input" />
        <Upload className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
        <p className="mb-2 text-lg font-medium">
          {isDragActive ? 'Drop files here...' : 'Drag & drop files here'}
        </p>
        <p className="text-sm text-muted-foreground">
          or click to browse (PDF, DOC, DOCX, TXT, CSV - max 10MB per file)
        </p>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-medium">
                Files Selected ({files.length})
              </h3>
              <p className="text-sm text-muted-foreground">
                {validFilesCount} valid · Total size: {formatFileSize(totalSize)}
              </p>
            </div>
            <div className="flex gap-2">
              <Button
                onClick={handleUpload}
                disabled={isUploading || validFilesCount === 0}
                aria-busy={isUploading}
              >
                {isUploading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="mr-2 h-4 w-4" />
                    Upload {validFilesCount} {validFilesCount === 1 ? 'File' : 'Files'}
                  </>
                )}
              </Button>
              <Button onClick={clearAll} variant="outline" disabled={isUploading}>
                Clear All
              </Button>
            </div>
          </div>

          {/* Individual File Items */}
          <div className="space-y-2" role="list" aria-label="File upload list">
            {files.map((fileState) => (
              <FileUploadItem
                key={fileState.file.name}
                fileState={fileState}
                onRemove={() => removeFile(fileState.file.name)}
                onRetry={() => retryFile(fileState.file.name)}
                disabled={isUploading}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

interface FileUploadItemProps {
  fileState: FileUploadState;
  onRemove: () => void;
  onRetry: () => void;
  disabled: boolean;
}

function FileUploadItem({ fileState, onRemove, onRetry, disabled }: FileUploadItemProps) {
  const { file, validation, progress, result } = fileState;
  const hasErrors = validation.errors.length > 0;
  const isSuccess = result?.success === true;
  const isError = result?.success === false;
  const isScanning = progress?.status === 'scanning';
  const isUploading = progress?.status === 'uploading';

  return (
    <div
      className="rounded-lg border bg-card p-4"
      role="listitem"
      aria-label={`File: ${file.name}`}
    >
      <div className="flex items-start justify-between">
        <div className="flex flex-1 items-start gap-3">
          {/* Status Icon */}
          {hasErrors && <XCircle className="mt-0.5 h-5 w-5 text-destructive" />}
          {isSuccess && <CheckCircle2 className="mt-0.5 h-5 w-5 text-green-600" />}
          {isScanning && <Shield className="mt-0.5 h-5 w-5 animate-pulse text-yellow-600" />}
          {isUploading && <Loader2 className="mt-0.5 h-5 w-5 animate-spin text-primary" />}
          {!hasErrors && !isSuccess && !isScanning && !isUploading && (
            <File className="mt-0.5 h-5 w-5 text-muted-foreground" />
          )}

          {/* File Info */}
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <p className="font-medium">{file.name}</p>
              <span className="text-xs text-muted-foreground">{formatFileSize(file.size)}</span>
            </div>
            
            {/* Validation Errors */}
            {validation.errors.map((error, idx) => (
              <p key={idx} className="text-sm text-destructive" role="alert">
                {error}
              </p>
            ))}
            
            {/* Validation Warnings */}
            {validation.warnings.map((warning, idx) => (
              <p key={idx} className="text-sm text-yellow-600">
                ⚠ {warning}
              </p>
            ))}
            
            {/* Upload Progress */}
            {progress && isUploading && (
              <div className="mt-2 space-y-1">
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>{progress.progress}%</span>
                  {progress.estimatedTimeRemaining && progress.estimatedTimeRemaining > 0 && (
                    <span>~{Math.ceil(progress.estimatedTimeRemaining)}s remaining</span>
                  )}
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
                  <div
                    className="h-full bg-primary transition-all duration-300"
                    style={{ width: `${progress.progress}%` }}
                    role="progressbar"
                    aria-valuenow={progress.progress}
                    aria-valuemin={0}
                    aria-valuemax={100}
                  />
                </div>
              </div>
            )}
            
            {/* Security Scanning Status */}
            {isScanning && (
              <p className="mt-1 text-sm text-yellow-600">
                <Shield className="mr-1 inline h-4 w-4" />
                Security scanning in progress...
              </p>
            )}
            
            {/* Success Message */}
            {isSuccess && result?.message && (
              <p className="mt-1 text-sm text-green-600">{result.message}</p>
            )}
            
            {/* Error Message */}
            {isError && result?.error && (
              <p className="mt-1 text-sm text-destructive" role="alert">
                {result.error}
              </p>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          {isError && (
            <Button
              size="sm"
              variant="outline"
              onClick={onRetry}
              disabled={disabled}
              aria-label={`Retry upload for ${file.name}`}
            >
              Retry
            </Button>
          )}
          <Button
            size="sm"
            variant="ghost"
            onClick={onRemove}
            disabled={disabled || isUploading}
            aria-label={`Remove ${file.name}`}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}

