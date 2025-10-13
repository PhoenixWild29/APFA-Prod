/**
 * Document Upload Page
 * 
 * Provides interface for users to upload documents to the knowledge base
 */
import React from 'react';
import DocumentUpload from '@/components/DocumentUpload';

export default function UploadPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Upload Documents</h1>
        <p className="mt-2 text-muted-foreground">
          Upload documents to enhance the AI knowledge base
        </p>
      </div>

      <DocumentUpload />

      <div className="rounded-lg border bg-card p-6">
        <h2 className="mb-4 text-lg font-semibold">Supported File Types</h2>
        <ul className="space-y-2 text-sm text-muted-foreground">
          <li>✓ PDF Documents (.pdf)</li>
          <li>✓ Microsoft Word (.doc, .docx)</li>
          <li>✓ Text Files (.txt)</li>
          <li>✓ CSV Spreadsheets (.csv)</li>
          <li>✓ Excel Files (.xls, .xlsx)</li>
        </ul>
        
        <h2 className="mb-4 mt-6 text-lg font-semibold">Upload Guidelines</h2>
        <ul className="space-y-2 text-sm text-muted-foreground">
          <li>• Maximum file size: 10 MB per file</li>
          <li>• Maximum batch size: 50 files</li>
          <li>• Total batch size: 100 MB</li>
          <li>• Files are automatically scanned for security</li>
          <li>• Processing begins immediately after upload</li>
        </ul>
      </div>
    </div>
  );
}

