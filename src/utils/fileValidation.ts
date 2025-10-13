/**
 * File Validation Utilities
 * 
 * Provides client-side validation for file uploads including
 * type checking, size limits, and security validation.
 */

// Allowed file types
export const ALLOWED_FILE_TYPES = {
  'application/pdf': ['.pdf'],
  'application/msword': ['.doc'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'text/plain': ['.txt'],
  'text/csv': ['.csv'],
  'application/vnd.ms-excel': ['.xls'],
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
};

export const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB
export const MAX_BATCH_SIZE = 50; // Maximum files in batch
export const MAX_TOTAL_SIZE = 100 * 1024 * 1024; // 100 MB total

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

/**
 * Validate file type
 */
export function validateFileType(file: File): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];
  
  const allowedMimeTypes = Object.keys(ALLOWED_FILE_TYPES);
  
  if (!allowedMimeTypes.includes(file.type)) {
    // Check by extension as fallback
    const extension = file.name.toLowerCase().match(/\.[^.]+$/)?.[0];
    const isAllowedByExtension = Object.values(ALLOWED_FILE_TYPES)
      .flat()
      .includes(extension || '');
    
    if (!isAllowedByExtension) {
      errors.push(
        `File type "${file.type || 'unknown'}" is not supported. Allowed types: PDF, DOC, DOCX, TXT, CSV, XLS, XLSX`
      );
    }
  }
  
  return {
    isValid: errors.length === 0,
    errors,
    warnings,
  };
}

/**
 * Validate file size
 */
export function validateFileSize(file: File): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];
  
  if (file.size === 0) {
    errors.push('File is empty');
  } else if (file.size > MAX_FILE_SIZE) {
    errors.push(
      `File size (${formatFileSize(file.size)}) exceeds maximum allowed size (${formatFileSize(MAX_FILE_SIZE)})`
    );
  } else if (file.size > MAX_FILE_SIZE * 0.8) {
    warnings.push('File is close to size limit');
  }
  
  return {
    isValid: errors.length === 0,
    errors,
    warnings,
  };
}

/**
 * Validate file name
 */
export function validateFileName(file: File): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];
  
  // Check for potentially dangerous characters
  const dangerousChars = /[<>:"|?*\x00-\x1f]/;
  if (dangerousChars.test(file.name)) {
    errors.push('File name contains invalid characters');
  }
  
  // Check length
  if (file.name.length > 255) {
    errors.push('File name is too long (max 255 characters)');
  }
  
  // Check for hidden files
  if (file.name.startsWith('.')) {
    warnings.push('Hidden file detected');
  }
  
  return {
    isValid: errors.length === 0,
    errors,
    warnings,
  };
}

/**
 * Validate single file (comprehensive)
 */
export function validateFile(file: File): ValidationResult {
  const typeValidation = validateFileType(file);
  const sizeValidation = validateFileSize(file);
  const nameValidation = validateFileName(file);
  
  return {
    isValid:
      typeValidation.isValid && sizeValidation.isValid && nameValidation.isValid,
    errors: [
      ...typeValidation.errors,
      ...sizeValidation.errors,
      ...nameValidation.errors,
    ],
    warnings: [
      ...typeValidation.warnings,
      ...sizeValidation.warnings,
      ...nameValidation.warnings,
    ],
  };
}

/**
 * Validate batch of files
 */
export function validateBatch(files: File[]): {
  isValid: boolean;
  errors: string[];
  warnings: string[];
  fileResults: Map<string, ValidationResult>;
} {
  const errors: string[] = [];
  const warnings: string[] = [];
  const fileResults = new Map<string, ValidationResult>();
  
  // Check batch size
  if (files.length === 0) {
    errors.push('No files selected');
  } else if (files.length > MAX_BATCH_SIZE) {
    errors.push(`Too many files. Maximum ${MAX_BATCH_SIZE} files per batch`);
  }
  
  // Check total size
  const totalSize = files.reduce((sum, file) => sum + file.size, 0);
  if (totalSize > MAX_TOTAL_SIZE) {
    errors.push(
      `Total size (${formatFileSize(totalSize)}) exceeds maximum (${formatFileSize(MAX_TOTAL_SIZE)})`
    );
  }
  
  // Validate each file
  let validFiles = 0;
  files.forEach((file) => {
    const result = validateFile(file);
    fileResults.set(file.name, result);
    
    if (result.isValid) {
      validFiles++;
    }
  });
  
  if (validFiles === 0 && files.length > 0) {
    errors.push('No valid files to upload');
  }
  
  return {
    isValid: errors.length === 0 && validFiles > 0,
    errors,
    warnings,
    fileResults,
  };
}

/**
 * Format file size for display
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Get file extension
 */
export function getFileExtension(fileName: string): string {
  const match = fileName.toLowerCase().match(/\.[^.]+$/);
  return match ? match[0] : '';
}

/**
 * Check if file type is allowed
 */
export function isFileTypeAllowed(file: File): boolean {
  const allowedMimeTypes = Object.keys(ALLOWED_FILE_TYPES);
  if (allowedMimeTypes.includes(file.type)) {
    return true;
  }
  
  // Check by extension
  const extension = getFileExtension(file.name);
  return Object.values(ALLOWED_FILE_TYPES).flat().includes(extension);
}

