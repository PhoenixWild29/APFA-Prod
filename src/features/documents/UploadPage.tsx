import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import DocumentUpload from '@/components/DocumentUpload';

export default function UploadPage() {
  const navigate = useNavigate();

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-6">
      {/* Back button */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => navigate('/app/documents')}
        className="gap-1.5 text-muted-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Documents
      </Button>

      {/* Header */}
      <div>
        <h1 className="font-serif text-2xl font-semibold">Upload Documents</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Upload financial documents to ground your advisor in your personal data.
        </p>
      </div>

      {/* Upload component — reuse existing */}
      <DocumentUpload />

      {/* Guidelines */}
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-xl border bg-card p-4">
          <h3 className="text-sm font-semibold">Supported Formats</h3>
          <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
            <li className="flex items-center gap-2">
              <span className="text-pos">&#10003;</span> PDF Documents (.pdf)
            </li>
            <li className="flex items-center gap-2">
              <span className="text-pos">&#10003;</span> Word (.doc, .docx)
            </li>
            <li className="flex items-center gap-2">
              <span className="text-pos">&#10003;</span> Text Files (.txt)
            </li>
            <li className="flex items-center gap-2">
              <span className="text-pos">&#10003;</span> CSV / Excel (.csv, .xls, .xlsx)
            </li>
          </ul>
        </div>
        <div className="rounded-xl border bg-card p-4">
          <h3 className="text-sm font-semibold">Limits</h3>
          <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
            <li>Max file size: <span className="font-medium text-foreground">10 MB</span></li>
            <li>Max batch: <span className="font-medium text-foreground">50 files</span></li>
            <li>Total batch: <span className="font-medium text-foreground">100 MB</span></li>
            <li>Auto virus scan on upload</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
